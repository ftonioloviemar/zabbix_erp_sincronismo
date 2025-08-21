import os
import sys
import argparse
import requests
import re
from vieutil import Viecry
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from dotenv import load_dotenv

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

def get_auth_token(session, base_url, username, password, debug=False):
    """Realiza o login no ERP e extrai o token de autorizacao."""
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

    # Corrigido para buscar o token em 'preencheSessao', conforme encontrado pelo usuario
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
        
        data = {
            'data_ultimo_envio': soup.find('td', id='DTULTIMOENV').get_text(strip=True),
            'hora_ultimo_envio': soup.find('td', id='HRULTIMOENV').get_text(strip=True),
            'problema_envio': soup.find('td', id='PROBLEMA').get_text(strip=True),
            'problema_receb': soup.find('td', id='PROBLEMAREC').get_text(strip=True),
        }
        return data
    except AttributeError as e:
        raise ParsingError(f"Erro ao analisar a pagina de status. Um campo esperado (ID) nao foi encontrado. Detalhes: {e}")

def main():
    """Funcao principal do script."""
    load_dotenv()

    parser = argparse.ArgumentParser(description="Verifica o status de sincronismo do ERP Tecnicon.")
    parser.add_argument('--url', default=os.getenv('ERP_BASE_URL'), help="URL base do ERP.")
    parser.add_argument('--username', default=os.getenv('ERP_USERNAME'), help="Usuario para login.")
    parser.add_argument('--password', default=os.getenv('ERP_PASSWORD'), help="Senha para login.")
    parser.add_argument('--max-delay', type=int, default=os.getenv('MAX_SECONDS_DELAY'), help="Atraso maximo em segundos permitido.")
    parser.add_argument('--debug', action='store_true', help="Ativa o modo de depuracao, salvando a resposta HTML do login.")

    args = parser.parse_args()

    if not all([args.url, args.username, args.password, args.max_delay]):
        print("Erro: Faltando parametros. Forneca URL, username, password e max-delay via argumentos ou arquivo .env")
        sys.exit(1)

    try:
        # Descriptografar a senha recebida como argumento
        cry = Viecry()
        decrypted_password = cry.descriptografar(args.password)
    except Exception as e:
        print(f"STATUS_PROBLEMA: Falha ao descriptografar a senha. Verifique a chave. Erro: {e}")
        sys.exit(1)

    try:
        with requests.Session() as session:
            token = get_auth_token(session, args.url, args.username, decrypted_password, debug=args.debug)
            status_html = get_sync_status_page(session, args.url, token)
            status_data = parse_status_page(status_html)

        if 'PROBL' in status_data['problema_envio'].upper() or 'PROBL' in status_data['problema_receb'].upper():
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
            print(f"STATUS_PROBLEMA: Sincronismo atrasado em {int(delay)} segundos (limite: {args.max_delay}s).")
            sys.exit(1)

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