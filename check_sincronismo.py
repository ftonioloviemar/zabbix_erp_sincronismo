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
    """Analisa o HTML e extrai os dados de sincronismo."""
    try:
        soup = BeautifulSoup(html_content, 'lxml')
        
        # Log para debug - salva o HTML completo para análise
        logger.info(f"HTML recebido para análise (tamanho: {len(html_content)} caracteres)")
        
        # Salva HTML para debug em arquivo temporário
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
            f.write(html_content)
            logger.info(f"HTML salvo em {f.name} para análise detalhada")
        
        # Procura por TODAS as tabelas na página
        todas_tabelas = soup.find_all('table')
        logger.info(f"Total de tabelas encontradas: {len(todas_tabelas)}")
        
        # Procura também por divs que possam conter grids/tabelas
        divs_grid = soup.find_all('div', class_=lambda x: x and any(termo in str(x).lower() for termo in ['grid', 'table', 'dados', 'vista']))
        logger.info(f"Total de divs que podem conter grid: {len(divs_grid)}")
        
        # Analisa cada tabela encontrada
        tabela_principal = None
        linhas_encontradas = []
        
        for idx, tabela in enumerate(todas_tabelas):
            linhas = tabela.find_all('tr')
            logger.info(f"Tabela {idx}: {len(linhas)} linhas")
            
            # Log da estrutura da tabela
            for i, linha in enumerate(linhas[:3]):  # Log apenas primeiras 3 linhas
                celulas = linha.find_all(['td', 'th'])
                conteudo = [c.get_text(strip=True)[:30] for c in celulas[:5]]
                logger.info(f"  Linha {i}: {len(celulas)} células - {conteudo}")
            
            # Se encontrar uma tabela com dados (mais de 1 linha), usa ela
            if len(linhas) > 1:
                # Verifica se parece ser uma tabela de sincronismo procurando por palavras-chave
                texto_tabela = str(tabela).upper()
                if any(termo in texto_tabela for termo in ['FILIAL', 'SINCRONISMO', 'ENVIO', 'RECEB', 'STATUS']):
                    logger.info(f"  -> Tabela {idx} parece ser de sincronismo!")
                    tabela_principal = tabela
                    linhas_encontradas = linhas
                    break
        
        # Se não encontrou tabela com dados, tenta as divs
        if not tabela_principal and divs_grid:
            for idx, div in enumerate(divs_grid):
                # Procura por linhas dentro da div
                linhas = div.find_all(['tr', 'div'], class_=lambda x: x and 'row' in str(x).lower())
                if len(linhas) > 1:
                    logger.info(f"Div {idx} parece conter {len(linhas)} linhas de dados")
                    # Converte para estrutura simulada de tabela
                    tabela_principal = div
                    linhas_encontradas = linhas
                    break
        
        # Se ainda não encontrou, tenta qualquer estrutura com múltiplas linhas
        if not tabela_principal:
            # Procura por qualquer elemento que tenha múltiplas linhas com células
            possiveis = soup.find_all(['div', 'table', 'tbody'])
            for elem in possiveis:
                linhas = elem.find_all(['tr', 'div'], recursive=False)
                if len(linhas) > 2:  # Mais de 2 linhas pode indicar dados
                    logger.info(f"Encontrada estrutura alternativa com {len(linhas)} linhas")
                    tabela_principal = elem
                    linhas_encontradas = linhas
                    break
        
        if not tabela_principal:
            logger.error("Nenhuma tabela ou estrutura de dados encontrada")
            raise ParsingError("Não foi possível encontrar a tabela de sincronismo")
        
        logger.info(f"Usando estrutura com {len(linhas_encontradas)} linhas totais")
        
        # Se só tem 1 linha (cabeçalho), trata como caso especial
        if len(linhas_encontradas) <= 1:
            logger.warning("Apenas cabeçalho encontrado, verificando se há erro na página...")
            
            # Procura por mensagens de erro em qualquer lugar da página
            if any(termo in html_content.upper() for termo in ['ERRO', 'FALHA', 'PROBLEMA', 'INVALID']):
                logger.warning("Encontrada mensagem de erro no HTML")
                return {
                    'data_ultimo_envio': '',
                    'hora_ultimo_envio': '',
                    'problema_envio': 'ERRO_DETECTADO_HTML: Erro encontrado na página de sincronismo',
                    'problema_receb': '',
                }
            
            return {
                'data_ultimo_envio': '',
                'hora_ultimo_envio': '',
                'problema_envio': 'SEM_DADOS_SINCRONISMO: Nenhum dado de sincronismo encontrado na tabela',
                'problema_receb': '',
            }
        
        # Usa as linhas encontradas
        linhas = linhas_encontradas[1:]  # Pula cabeçalho
        
        # Variáveis para armazenar os problemas encontrados em qualquer linha
        problema_envio_global = ""
        problema_receb_global = ""
        data_ultimo_envio = ""
        hora_ultimo_envio = ""
        filiais_com_erro = []
        
        logger.info(f"Analisando {len(linhas)} linhas da tabela de sincronismo")
        
        # Analisa cada linha da tabela
        for idx, linha in enumerate(linhas):
            # Pega todas as células da linha
            celulas = linha.find_all('td')
            if len(celulas) < 2:  # Verifica se tem pelo menos 2 células (filial + dados)
                logger.warning(f"Linha {idx+1} ignorada: apenas {len(celulas)} células")
                continue
            
            # Pega o nome da filial (primeira coluna)
            filial = celulas[0].get_text(strip=True) if celulas else f"Linha {idx+1}"
            logger.info(f"Analisando linha {idx+1}: Filial '{filial}' ({len(celulas)} células)")
            
            # Flag para indicar se esta linha tem erro
            linha_com_erro = False
            mensagens_erro_linha = []  # Muda para lista para capturar múltiplos erros
            
            # Verifica cada célula da linha para detectar erros
            for celula_idx, celula in enumerate(celulas):
                # Pega o texto da célula
                texto_celula = celula.get_text(strip=True)
                
                # Verifica o estilo da célula (fundo amarelo indica erro)
                estilo_celula = celula.get('style', '').lower()
                classe_celula = celula.get('class', [])
                classe_celula_str = ' '.join(classe_celula) if isinstance(classe_celula, list) else str(classe_celula)
                
                # Detecta erro por fundo amarelo
                tem_fundo_amarelo = ('background-color: yellow' in estilo_celula or 
                                   'background: yellow' in estilo_celula or
                                   'bgcolor="yellow"' in str(celula))
                
                # Detecta erro por fundo vermelho/laranja (status 500)
                tem_fundo_vermelho = ('background-color: red' in estilo_celula or 
                                    'background: red' in estilo_celula or
                                    'background-color: orange' in estilo_celula or
                                    'background: orange' in estilo_celula or
                                    'bgcolor="red"' in str(celula) or
                                    'bgcolor="orange"' in str(celula))
                
                # Detecta erro por texto
                tem_erro_texto = any(palavra in texto_celula.upper() for palavra in ['ERRO', 'PROBL', 'INVÁLIDO', 'INVALID', 'FALHA', 'FAIL'])
                
                # Detecta status HTTP de erro (500, 404, etc)
                tem_status_erro = any(str(num) in texto_celula for num in ['500', '404', '403', '502', '503'])
                
                # Detecta erro por classe CSS
                tem_classe_erro = any(classe in classe_celula_str.lower() for classe in ['error', 'erro', 'probl', 'fail', 'danger'])
                
                if tem_fundo_amarelo or tem_fundo_vermelho or tem_erro_texto or tem_classe_erro or tem_status_erro:
                    linha_com_erro = True
                    # Adiciona a mensagem de erro à lista
                    if texto_celula and texto_celula not in mensagens_erro_linha:  # Evita duplicatas
                        mensagens_erro_linha.append(texto_celula)
                    logger.warning(f"  -> Erro detectado na célula {celula_idx}: '{texto_celula}' (fundo_amarelo={tem_fundo_amarelo}, fundo_vermelho={tem_fundo_vermelho}, erro_texto={tem_erro_texto}, status_erro={tem_status_erro}, classe_erro={tem_classe_erro})")
                    # NÃO dá break - continua verificando para capturar todos os erros da linha
            
            # Se encontrou erro na linha, adiciona à lista
            if linha_com_erro:
                filiais_com_erro.append(filial)
                # Junta todas as mensagens de erro da linha
                mensagem_completa = " | ".join(mensagens_erro_linha) if mensagens_erro_linha else "Erro detectado"
                if problema_envio_global:
                    problema_envio_global += f" | [{filial}]: {mensagem_completa}"
                else:
                    problema_envio_global = f"[{filial}]: {mensagem_completa}"
        
        # Se não encontrou data/hora específica, tenta pegar da primeira linha válida
        if not data_ultimo_envio:
            for linha in linhas:
                celulas = linha.find_all('td')
                if len(celulas) >= 3:  # Assume que data e hora estão nas colunas 1 e 2
                    data_ultimo_envio = celulas[1].get_text(strip=True) if len(celulas) > 1 else ""
                    hora_ultimo_envio = celulas[2].get_text(strip=True) if len(celulas) > 2 else ""
                    if data_ultimo_envio and hora_ultimo_envio:
                        logger.info(f"Data/hora encontradas: {data_ultimo_envio} {hora_ultimo_envio}")
                        break
        
        # Se ainda não encontrou data/hora, tenta encontrar em qualquer lugar da página
        if not data_ultimo_envio or not hora_ultimo_envio:
            # Procura por padrões de data e hora no HTML
            data_match = re.search(r'(\d{2}/\d{2}/\d{4})', html_content)
            hora_match = re.search(r'(\d{2}:\d{2}:\d{2})', html_content)
            
            if data_match:
                data_ultimo_envio = data_match.group(1)
                logger.info(f"Data encontrada via regex: {data_ultimo_envio}")
            if hora_match:
                hora_ultimo_envio = hora_match.group(1)
                logger.info(f"Hora encontrada via regex: {hora_ultimo_envio}")
        
        # Log resumo da análise
        if filiais_com_erro:
            logger.error(f"Erros encontrados nas filiais: {', '.join(filiais_com_erro)}")
        else:
            logger.info("Nenhum erro encontrado nas filiais analisadas")
        
        # Se não encontrou nenhuma data/hora, usa data/hora atual como fallback
        if not data_ultimo_envio or not hora_ultimo_envio:
            agora = datetime.now()
            data_ultimo_envio = agora.strftime('%d/%m/%Y')
            hora_ultimo_envio = agora.strftime('%H:%M:%S')
            logger.warning(f"Data/hora não encontradas, usando valores atuais: {data_ultimo_envio} {hora_ultimo_envio}")
        
        data = {
            'data_ultimo_envio': data_ultimo_envio,
            'hora_ultimo_envio': hora_ultimo_envio,
            'problema_envio': problema_envio_global,
            'problema_receb': problema_receb_global,
        }
        return data
        
    except AttributeError as e:
        raise ParsingError(f"Erro ao analisar a pagina de status. Um campo esperado (ID) nao foi encontrado. Detalhes: {e}")

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

        # Verifica se há problemas no sincronismo
        tem_problema = bool(status_data['problema_envio']) or bool(status_data['problema_receb'])
        
        if tem_problema:
            # Verifica se é o caso especial de sem dados
            if 'SEM_DADOS_SINCRONISMO' in status_data['problema_envio']:
                logger.warning("Nenhum dado de sincronismo encontrado - pode indicar que não há sincronismo configurado")
                print("STATUS_PROBLEMA: Nenhum dado de sincronismo encontrado na tabela - verificar se há sincronismo configurado")
                sys.exit(1)
            
            logger.error(f"Problemas detectados: {status_data['problema_envio']} | {status_data['problema_receb']}")
            print(f"STATUS_PROBLEMA: {status_data['problema_envio']} | {status_data['problema_receb']}")
            sys.exit(1)

        datetime_str = f"{status_data['data_ultimo_envio']} {status_data['hora_ultimo_envio']}"
        try:
            last_sync_time = datetime.strptime(datetime_str, '%d/%m/%Y %H:%M:%S')
        except ValueError:
             raise ParsingError(f"Formato de data/hora inesperado: '{datetime_str}'")

        current_time = datetime.now()
        delay = (current_time - last_sync_time).total_seconds()

        if delay > args.max_delay:
            logger.error(f"Sincronismo atrasado em {int(delay)} segundos (limite: {args.max_delay}s)")
            print(f"STATUS_PROBLEMA: Sincronismo atrasado em {int(delay)} segundos (limite: {args.max_delay}s).")
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
