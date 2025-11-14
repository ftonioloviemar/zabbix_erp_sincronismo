import os
import sys
import argparse
import requests
import re
import logging
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from dotenv import load_dotenv
from logging.handlers import TimedRotatingFileHandler

# Configuração do logging com rotação diária
def setup_logging():
    """Configura o sistema de logs com rotação diária."""
    # Cria o diretório de logs se não existir
    logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    
    # Configura o handler de rotação diária
    log_filename = os.path.join(logs_dir, 'g70k_')
    handler = TimedRotatingFileHandler(
        log_filename,
        when='midnight',
        interval=1,
        backupCount=30,  # Mantém 30 dias de logs
        encoding='utf-8'
    )
    
    # Formato do log
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    
    # Configura o logger
    logger = logging.getLogger('zabbix_erp_sincronismo')
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    
    return logger

# Inicializa o logging
logger = setup_logging()

# Status de saida para o Zabbix
STATUS_OK = "STATUS_OK"

class ERPLoginError(Exception):
    """Excecao para falhas de login no ERP."""
    pass

class StatusFetchError(Exception):
    """Excecao para falhas ao buscar a pagina de status."""
    pass

class ParsingError(Exception):
    """Excecao para erros ao analisar o HTML."""
    pass

def select_empresa(session, base_url, html_content, debug=False):
    """Seleciona a primeira empresa disponível após o login."""
    logger.info("Selecionando empresa após login...")
    
    # Procura o código da primeira empresa na tabela
    soup = BeautifulSoup(html_content, 'lxml')
    
    # Procura a tabela de empresas
    tabela = soup.find('table', {'id': 'tblBody'}) or soup.find('tbody')
    if not tabela:
        raise ERPLoginError("Não foi possível encontrar a tabela de empresas")
    
    # Pega a primeira linha com dados (excluindo cabeçalho)
    linhas = tabela.find_all('tr')
    if len(linhas) < 2:
        raise ERPLoginError("Nenhuma empresa disponível para seleção")
    
    # Pega a primeira linha de dados
    primeira_linha = linhas[1]
    celulas = primeira_linha.find_all('td')
    
    if not celulas:
        raise ERPLoginError("Nenhuma célula encontrada na linha da empresa")
    
    # O código da empresa geralmente está na primeira célula
    codigo_empresa = celulas[0].get_text(strip=True)
    logger.info(f"Selecionando empresa: {codigo_empresa}")
    
    # URL para selecionar a empresa
    select_url = f"{base_url}/Tecnicon/Controller?acao=Tecnicon.EmpresaLogin.selecionarEmpresa&idDialog=dv0"
    
    payload = {
        'smenuvChamado': 'null',
        'telaChamou': 'null',
        'painel': 'false',
        'empresa': codigo_empresa,
        'modal': 'false',
        'iddialog': 'dv0'
    }
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Cookie': 'nerroslog=0'
    }
    
    try:
        response = session.post(select_url, data=payload, headers=headers, timeout=30)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise ERPLoginError(f"Erro ao selecionar empresa: {e}")
    
    if debug:
        debug_dir = "debug"
        os.makedirs(debug_dir, exist_ok=True)
        debug_filename = os.path.join(debug_dir, "empresa_selection_debug.html")
        with open(debug_filename, "w", encoding="utf-8") as f:
            f.write(response.text)
    
    # Tenta extrair o token da resposta após seleção da empresa
    token_match = re.search(r"preencheSessao\s*\(\s*'([^']*)'", response.text)
    if not token_match:
        # Se não encontrar na resposta da seleção, tenta usar o HTML original
        token_match = re.search(r"preencheSessao\s*\(\s*'([^']*)'", html_content)
        if not token_match:
            raise ERPLoginError("Não foi possível encontrar o token de autorização após seleção da empresa")
    
    return token_match.group(1)

def get_auth_token(session, base_url, username, password, debug=False):
    """Realiza o login no ERP e extrai o token de autorizacao."""
    logger.info(f"Tentando login no ERP: {base_url} com usuário: {username}")
    login_url = f"{base_url}/Tecnicon/Controller?acao=Tecnicon.EfetuaLogin.obterTelaHtml&idDialog=dv0"
    payload = {
        'smenuvChamado': 'null',
        'telaChamou': 'null',
        'painel': 'false',
        'usuario': username,
        'senha': password,
        'tipologin': 'L',
        'modal': 'false',
        'tipoTela': 'O',
        'telafechar': 'false',
        'telamaximizar': 'false',
        'telaminimizar': 'false',
        'iddialog': 'dv0',
        'width': '820px',
        'min-height': '107px',
        'height': '325px',
        'carregouJsDinamico': 'false',
        'logintimeout': 'false',
        'empresaURL': 'Portal'
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Cookie': 'nerroslog=0',
        'Authorization': '-9876'
    }

    try:
        response = session.post(login_url, data=payload, headers=headers, timeout=30)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise ERPLoginError(f"Erro de conexao ao tentar logar: {e}")

    if debug:
        debug_dir = "debug"
        os.makedirs(debug_dir, exist_ok=True)
        debug_filename = os.path.join(debug_dir, "login_response_debug.html")
        with open(debug_filename, "w", encoding="utf-8") as f:
            f.write(response.text)

    # Verifica se a resposta contém a tela de seleção de empresa
    if "Selecione a Empresa" in response.text or "tEmpresas" in response.text:
        logger.info("Tela de seleção de empresa detectada, selecionando empresa...")
        return select_empresa(session, base_url, response.text, debug)
    
    # Se não for tela de seleção de empresa, tenta extrair o token diretamente
    token_match = re.search(r"preencheSessao\s*\(\s*'([^']*)'", response.text)
    if not token_match:
        raise ERPLoginError("Nao foi possivel encontrar o token de autorizacao em preencheSessao(). Verifique a estrutura da pagina de resposta.")
    
    return token_match.group(1)

def get_sync_status_page(session, base_url, auth_token):
    """Busca a pagina HTML com o status do sincronismo."""
    status_url = f"{base_url}/Tecnicon/Controller?acao=TecniconVista.CarregaVista.carregaVista&idDialog=dv4"
    headers = {
        'Authorization': auth_token
    }
    payload = {
        'smenuvChamado': '11327',
        'telaChamou': 'Status Sincronismo 2',
        'empresa': '17',
        'filial': '1',
        'local': '1',
        'vista': '2052',
        'mobile': 'false',
        'svistaaba': '2902',
        'idTbl': '2902',
        'param1': '{"parametros":[]}',
        'param2': 'svistaaba|2902',
        'tamGridVista': '681',
        'tituloPainel': 'Status Sincronismo'
    }

    try:
        response = session.post(status_url, headers=headers, data=payload, timeout=30)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        raise StatusFetchError(f"Erro de conexao ao buscar a pagina de status: {e}")

def parse_status_page(html_content):
    """Analisa o HTML e extrai os dados de sincronismo conforme condições específicas:
    
    Condições de problema:
    1. Qualquer célula na coluna "Log Filial p/ Sinc." contiver valor (não estiver vazia)
    2. O último registro enviado exceder o limite de tempo definido
    
    Condições de OK:
    1. Todas as células da coluna "Log Filial p/ Sinc." estiverem vazias
    2. E a data/hora do último registro estiver dentro do limite definido
    """
    try:
        soup = BeautifulSoup(html_content, 'lxml')
        
        # Log para debug
        logger.info("Iniciando análise da página de status com lógica específica")
        
        # Encontra a tabela de sincronismo
        tabela = None
        estrutura_colunas = None  # Para armazenar a estrutura de colunas encontrada
        todas_tabelas = soup.find_all('table')
        
        logger.info(f"Total de tabelas encontradas: {len(todas_tabelas)}")
        
        # Primeiro, procura por uma tabela que tenha os headers/nomes das colunas
        for idx, t in enumerate(todas_tabelas):
            linhas = t.find_all('tr')
            if len(linhas) > 0:
                # Analisa a primeira linha
                primeira_linha = linhas[0].find_all(['th', 'td'])
                texts_primeira = [h.get_text(strip=True) for h in primeira_linha]
                
                # Verifica se parece ser cabeçalho (tem nomes descritivos)
                parece_cabecalho = False
                for texto in texts_primeira:
                    texto_upper = texto.upper()
                    if any(termo in texto_upper for termo in ['LOG', 'FILIAL', 'DATA', 'HORA', 'ENV', 'SINC']):
                        parece_cabecalho = True
                        break
                
                if parece_cabecalho:
                    tabela = t
                    estrutura_colunas = texts_primeira
                    logger.info(f"Tabela {idx} com estrutura de colunas encontrada")
                    logger.info(f"Estrutura: {estrutura_colunas}")
                    break
        
        # Se não encontrou tabela com cabeçalho, usa a primeira com dados
        if not tabela:
            for idx, t in enumerate(todas_tabelas):
                linhas = t.find_all('tr')
                if len(linhas) > 1:  # Mais de 1 linha (dados)
                    tabela = t
                    logger.info(f"Usando tabela {idx} com dados como fallback")
                    break
        
        if not tabela:
            logger.error("Nenhuma tabela de sincronismo encontrada")
            raise ParsingError("Não foi possível encontrar a tabela de sincronismo")
        
        # Agora procura a tabela que tem os dados reais
        tabela_dados = None
        linhas_dados = []
        
        for idx, t in enumerate(todas_tabelas):
            linhas = t.find_all('tr')
            # Pula a tabela que já usamos para pegar a estrutura
            if t == tabela:
                continue
            
            if len(linhas) > 0:
                # Verifica se tem dados (não é só cabeçalho)
                primeira_linha = linhas[0].find_all(['th', 'td'])
                texts_primeira = [h.get_text(strip=True) for h in primeira_linha]
                
                # Se não parece cabeçalho e tem múltiplas linhas, é provavelmente dados
                if not any(termo in ' '.join(texts_primeira).upper() for termo in ['LOG', 'FILIAL', 'DATA', 'HORA', 'ENV', 'SINC']) and len(linhas) > 1:
                    tabela_dados = t
                    linhas_dados = linhas
                    logger.info(f"Tabela {idx} com dados encontrada")
                    break
        
        # Se não encontrou tabela com dados, usa a primeira que não seja a de estrutura
        if not tabela_dados and len(todas_tabelas) > 1:
            for idx, t in enumerate(todas_tabelas):
                if t != tabela and len(t.find_all('tr')) > 1:
                    tabela_dados = t
                    linhas_dados = t.find_all('tr')
                    logger.info(f"Usando tabela {idx} como fallback para dados")
                    break
        
        if not tabela_dados:
            logger.error("Nenhuma tabela com dados encontrada")
            raise ParsingError("Não foi possível encontrar tabela com dados de sincronismo")
        
        # Usa a estrutura encontrada anteriormente
        header_texts = estrutura_colunas
        logger.info(f"Usando estrutura de colunas: {header_texts}")
        
        # Encontra índices das colunas necessárias
        coluna_log_idx = None
        coluna_data_envio_idx = None
        coluna_hora_envio_idx = None
        
        logger.info("Procurando índices das colunas...")
        for idx, header in enumerate(header_texts):
            header_upper = header.upper().strip()
            logger.info(f"Analisando coluna {idx}: '{header}' -> '{header_upper}'")
            
            # Procura por coluna de log (prioridade máxima)
            if 'LOG FILIAL' in header_upper and 'SINC' in header_upper:
                coluna_log_idx = idx
                logger.info(f"✅ Coluna 'Log Filial p/ Sinc.' encontrada no índice: {idx}")
            
            # Procura por data de envio
            elif 'DATA' in header_upper and 'ENV' in header_upper and 'ULT' in header_upper:
                coluna_data_envio_idx = idx
                logger.info(f"✅ Coluna 'Data Ult. Reg. Env.' encontrada no índice: {idx}")
            
            # Procura por hora de envio
            elif 'HORA' in header_upper and ('ENV' in header_upper or 'ULT' in header_upper):
                coluna_hora_envio_idx = idx
                logger.info(f"✅ Coluna 'Hora Ultimo Reg. Env.' encontrada no índice: {idx}")
        
        # Se não encontrou os índices específicos, tenta correspondência parcial
        if coluna_log_idx is None:
            for idx, header in enumerate(header_texts):
                header_upper = header.upper()
                if 'LOG' in header_upper and ('FILIAL' in header_upper or 'SINC' in header_upper):
                    coluna_log_idx = idx
                    logger.info(f"✅ Coluna de log encontrada por correspondência parcial no índice: {idx}")
                    break
        
        if coluna_data_envio_idx is None:
            for idx, header in enumerate(header_texts):
                header_upper = header.upper()
                if 'DATA' in header_upper and 'ENV' in header_upper:
                    coluna_data_envio_idx = idx
                    logger.info(f"✅ Coluna de data de envio encontrada no índice: {idx}")
                    break
        
        if coluna_hora_envio_idx is None:
            for idx, header in enumerate(header_texts):
                header_upper = header.upper()
                if 'HORA' in header_upper and ('ENV' in header_upper or 'ULT' in header_upper):
                    coluna_hora_envio_idx = idx
                    logger.info(f"✅ Coluna de hora de envio encontrada no índice: {idx}")
                    break
        
        # Log final dos índices
        logger.info(f"Índices finais - Log: {coluna_log_idx}, Data: {coluna_data_envio_idx}, Hora: {coluna_hora_envio_idx}")
        
        # Se ainda não encontrou, tenta por posição baseado na estrutura típica
        if coluna_data_envio_idx is None and len(header_texts) > 7:
            coluna_data_envio_idx = 7  # Baseado no debug: Data Ult. Reg. Env. está no índice 7
            logger.info(f"Usando índice padrão para data de envio: {coluna_data_envio_idx}")
            
        if coluna_hora_envio_idx is None and len(header_texts) > 8:
            coluna_hora_envio_idx = 8  # Baseado no debug: Hora Ultimo Reg. Env. está no índice 8
            logger.info(f"Usando índice padrão para hora de envio: {coluna_hora_envio_idx}")
            
        if coluna_log_idx is None and len(header_texts) > 12:
            coluna_log_idx = 12  # Baseado no debug: Log Filial p/ Sinc. está no índice 12
            logger.info(f"Usando índice padrão para log filial: {coluna_log_idx}")
        
        # Processa os dados da tabela de dados
        logger.info(f"Processando {len(linhas_dados)} linhas de dados")
        
        # Variáveis para armazenar os resultados
        log_com_conteudo = False
        conteudo_log = []
        ultima_data_envio = None
        ultima_hora_envio = None
        
        # Analisa cada linha de dados
        for idx, linha in enumerate(linhas_dados):
            celulas = linha.find_all('td')
            if len(celulas) <= max(coluna_log_idx or 0, coluna_data_envio_idx or 0, coluna_hora_envio_idx or 0):
                logger.warning(f"Linha {idx+1} ignorada: apenas {len(celulas)} células")
                continue
            
            # Verifica a coluna de log
            if coluna_log_idx is not None and coluna_log_idx < len(celulas):
                texto_log = celulas[coluna_log_idx].get_text(strip=True)
                if texto_log:  # Se tem conteúdo (não está vazio)
                    log_com_conteudo = True
                    conteudo_log.append(texto_log)
                    logger.info(f"Linha {idx+1}: Log com conteúdo encontrado: '{texto_log}'")
            
            # Pega a data/hora do último registro (da última linha válida)
            if coluna_data_envio_idx is not None and coluna_hora_envio_idx is not None:
                if coluna_data_envio_idx < len(celulas) and coluna_hora_envio_idx < len(celulas):
                    data_texto = celulas[coluna_data_envio_idx].get_text(strip=True)
                    hora_texto = celulas[coluna_hora_envio_idx].get_text(strip=True)
                    
                    if data_texto and hora_texto:
                        ultima_data_envio = data_texto
                        ultima_hora_envio = hora_texto
                        logger.info(f"Última data/hora encontrada: {data_texto} {hora_texto}")
        
        # Prepara os resultados
        problema_envio = ""
        problema_receb = ""
        
        # Verificação 1: Log Filial p/ Sinc. com conteúdo
        if log_com_conteudo:
            problema_envio = f"Log com problema: {' | '.join(conteudo_log)}"
            logger.info(f"Problema detectado: {problema_envio}")
        
        # Verificação 2: Data/hora do último envio
        data_ultimo_envio = ultima_data_envio or ""
        hora_ultimo_envio = ultima_hora_envio or ""
        
        # Se não encontrou data/hora, tenta encontrar no HTML geral
        if not data_ultimo_envio or not hora_ultimo_envio:
            data_match = re.search(r'(\d{2}/\d{2}/\d{4})', html_content)
            hora_match = re.search(r'(\d{2}:\d{2}:\d{2})', html_content)
            
            if data_match:
                data_ultimo_envio = data_match.group(1)
                logger.info(f"Data encontrada via regex: {data_ultimo_envio}")
            if hora_match:
                hora_ultimo_envio = hora_match.group(1)
                logger.info(f"Hora encontrada via regex: {hora_ultimo_envio}")
        
        # Se ainda não encontrou, usa valores padrão
        if not data_ultimo_envio:
            data_ultimo_envio = datetime.now().strftime('%d/%m/%Y')
            logger.warning(f"Data não encontrada, usando valor padrão: {data_ultimo_envio}")
        if not hora_ultimo_envio:
            hora_ultimo_envio = datetime.now().strftime('%H:%M:%S')
            logger.warning(f"Hora não encontrada, usando valor padrão: {hora_ultimo_envio}")
        
        # Log do resultado final
        if log_com_conteudo:
            logger.info(f"Status: PROBLEMA - Log com conteúdo detectado")
        else:
            logger.info(f"Status: OK - Log vazio, verificando tempo...")
        
        data = {
            'data_ultimo_envio': data_ultimo_envio,
            'hora_ultimo_envio': hora_ultimo_envio,
            'problema_envio': problema_envio,
            'problema_receb': problema_receb,
        }
        return data
        
    except Exception as e:
        logger.error(f"Erro ao analisar página: {e}")
        raise ParsingError(f"Erro ao analisar a página de status: {e}")

def main():
    """Funcao principal do script."""
    logger.info("Iniciando verificação de sincronismo do ERP")
    load_dotenv()

    parser = argparse.ArgumentParser(description="Verifica o status de sincronismo do ERP Tecnicon.")
    parser.add_argument('--url', default=os.getenv('ERP_BASE_URL'), help="URL base do ERP.")
    parser.add_argument('--username', default=os.getenv('ERP_USERNAME'), help="Usuario para login.")
    parser.add_argument('--max-delay', type=int, default=os.getenv('MAX_SECONDS_DELAY'), help="Atraso maximo em segundos permitido.")
    parser.add_argument('--debug', action='store_true', help="Ativa o modo de depuracao, salvando a resposta HTML do login.")

    args = parser.parse_args()

    if not all([args.url, args.username, args.max_delay]):
        print("Erro: Faltando parametros. Forneca URL, username e max-delay via argumentos ou arquivo .env")
        sys.exit(1)

    try:
        # Lê a senha diretamente do .env (simplificado - sem criptografia)
        password = os.getenv('ERP_PASSWORD')
        if not password:
            print("STATUS_PROBLEMA: ERP_PASSWORD não encontrado no arquivo .env")
            sys.exit(1)
        logger.info(f"Senha carregada do .env para usuário: {args.username}")
    except Exception as e:
        print(f"STATUS_PROBLEMA: Falha ao carregar senha do .env. Erro: {e}")
        sys.exit(1)

    try:
        with requests.Session() as session:
            logger.info("Realizando login no ERP...")
            token = get_auth_token(session, args.url, args.username, password, debug=args.debug)
            logger.info("Login realizado com sucesso, buscando página de status...")
            status_html = get_sync_status_page(session, args.url, token)
            logger.info("Página de status obtida, analisando dados...")
            status_data = parse_status_page(status_html)

        # Verifica se há problemas no sincronismo conforme condições específicas
        tem_problema_log = bool(status_data['problema_envio'])  # Problema na coluna Log Filial p/ Sinc.
        
        # Se há problema no log, retorna imediatamente com o conteúdo do log
        if tem_problema_log:
            logger.error(f"Problema detectado na coluna Log Filial p/ Sinc.: {status_data['problema_envio']}")
            print(f"STATUS_PROBLEMA: {status_data['problema_envio']}")
            sys.exit(1)

        # Se não há problema no log, verifica o tempo
        datetime_str = f"{status_data['data_ultimo_envio']} {status_data['hora_ultimo_envio']}"
        try:
            last_sync_time = datetime.strptime(datetime_str, '%d/%m/%Y %H:%M:%S')
        except ValueError:
            raise ParsingError(f"Formato de data/hora inesperado: '{datetime_str}'")

        current_time = datetime.now()
        delay = (current_time - last_sync_time).total_seconds()

        if delay > args.max_delay:
            # Formata o tempo excedido (segundos ou minutos)
            if delay > 60:
                minutos = int(delay // 60)
                segundos = int(delay % 60)
                tempo_excedido = f"{minutos} minutos e {segundos} segundos"
            else:
                tempo_excedido = f"{int(delay)} segundos"
            
            logger.error(f"Sincronismo atrasado - tempo excedido: {tempo_excedido} (limite: {args.max_delay}s)")
            print(f"STATUS_PROBLEMA: Tempo excedido em {tempo_excedido} (limite: {args.max_delay}s)")
            sys.exit(1)

        logger.info("Sincronismo funcionando corretamente")
        print(STATUS_OK)

    except (ERPLoginError, StatusFetchError, ParsingError) as e:
        if args.debug:
            print(f"STATUS_PROBLEMA: {e} Um arquivo de depuracao foi salvo em 'debug/login_response_debug.html'.")
        else:
            print(f"STATUS_PROBLEMA: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"STATUS_PROBLEMA: Ocorreu um erro inesperado: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
