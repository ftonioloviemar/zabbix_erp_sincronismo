#!/usr/bin/env python3
"""Script de debug para analisar a estrutura HTML do ERP."""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Adiciona o diretório atual ao path para importar o script principal
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from check_sincronismo import get_auth_token, get_sync_status_page, setup_logging
import requests
from bs4 import BeautifulSoup

def main():
    """Função de debug para analisar HTML."""
    load_dotenv()
    logger = setup_logging()
    
    print("=== DEBUG DE ESTRUTURA HTML ===")
    
    try:
        # Carrega configurações
        base_url = os.getenv('ERP_BASE_URL')
        username = os.getenv('ERP_USERNAME')
        password = os.getenv('ERP_PASSWORD')
        
        # Realiza login e obtém página de status
        with requests.Session() as session:
            print("Realizando login...")
            token = get_auth_token(session, base_url, username, password, debug=True)
            print("Login realizado com sucesso!")
            
            print("Obtendo página de status...")
            status_html = get_sync_status_page(session, base_url, token)
            print(f"Página obtida - tamanho: {len(status_html)} caracteres")
            
            # Salva HTML para análise
            with open('debug/status_page_debug.html', 'w', encoding='utf-8') as f:
                f.write(status_html)
            print("HTML salvo em: debug/status_page_debug.html")
            
            # Analisa estrutura
            print("\n=== ANÁLISE DA ESTRUTURA ===")
            soup = BeautifulSoup(status_html, 'lxml')
            
            # Encontra todas as tabelas
            tabelas = soup.find_all('table')
            print(f"Total de tabelas encontradas: {len(tabelas)}")
            
            for idx, tabela in enumerate(tabelas):
                print(f"\n--- Tabela {idx} ---")
                
                # Pega todas as linhas
                linhas = tabela.find_all('tr')
                print(f"Total de linhas: {len(linhas)}")
                
                if linhas:
                    # Analisa headers da primeira linha
                    headers = linhas[0].find_all(['th', 'td'])
                    header_texts = [h.get_text(strip=True) for h in headers]
                    print(f"Headers: {header_texts}")
                    
                    # Se tiver mais de uma linha, mostra a primeira linha de dados
                    if len(linhas) > 1:
                        primeira_dados = linhas[1].find_all('td')
                        dados_texts = [d.get_text(strip=True) for d in primeira_dados]
                        print(f"Primeira linha de dados: {dados_texts}")
                        
                        # Procura por colunas específicas
                        for i, header in enumerate(header_texts):
                            header_upper = header.upper()
                            if 'LOG' in header_upper and 'FILIAL' in header_upper:
                                print(f"  -> Coluna 'Log Filial' encontrada no índice {i}: '{dados_texts[i] if i < len(dados_texts) else 'N/A'}'")
                            elif 'DATA' in header_upper and 'ENV' in header_upper:
                                print(f"  -> Coluna 'Data Envio' encontrada no índice {i}: '{dados_texts[i] if i < len(dados_texts) else 'N/A'}'")
                            elif 'HORA' in header_upper and ('ENV' in header_upper or 'ULT' in header_upper):
                                print(f"  -> Coluna 'Hora Envio' encontrada no índice {i}: '{dados_texts[i] if i < len(dados_texts) else 'N/A'}'")
                    
                    # Mostra mais algumas linhas se houver
                    if len(linhas) > 2:
                        print(f"... e mais {len(linhas)-2} linhas")
            
            print("\n=== ANÁLISE DE TEXTOS ===")
            # Procura por padrões de data e hora no HTML
            import re
            datas = re.findall(r'\d{2}/\d{2}/\d{4}', status_html)
            horas = re.findall(r'\d{2}:\d{2}:\d{2}', status_html)
            
            print(f"Datas encontradas: {datas[:10]}...")  # Primeiras 10
            print(f"Horas encontradas: {horas[:10]}...")  # Primeiras 10
            
            # Procura especificamente por 07:53:22
            if '07:53:22' in status_html:
                print("✅ Hora 07:53:22 encontrada no HTML!")
                # Mostra o contexto
                idx = status_html.find('07:53:22')
                contexto = status_html[max(0, idx-50):idx+50]
                print(f"Contexto: {contexto}")
            else:
                print("❌ Hora 07:53:22 NÃO encontrada no HTML")
                
    except Exception as e:
        print(f"\n❌ Erro geral: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Cria diretório debug se não existir
    os.makedirs('debug', exist_ok=True)
    main()