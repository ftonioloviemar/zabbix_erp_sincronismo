#!/usr/bin/env python3
"""Script de debug para verificar a captura e cálculo de data/hora."""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Adiciona o diretório atual ao path para importar o script principal
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from check_sincronismo import get_auth_token, get_sync_status_page, parse_status_page, setup_logging
import requests

def main():
    """Função de debug para verificar data/hora."""
    load_dotenv()
    logger = setup_logging()
    
    print("=== DEBUG DE DATA/HORA ===")
    print(f"Hora atual do sistema: {datetime.now()}")
    print(f"Fuso horário: {datetime.now().astimezone().tzinfo}")
    
    try:
        # Carrega configurações
        base_url = os.getenv('ERP_BASE_URL')
        username = os.getenv('ERP_USERNAME')
        password = os.getenv('ERP_PASSWORD')
        max_delay = int(os.getenv('MAX_SECONDS_DELAY', 300))
        
        print(f"\nConfigurações:")
        print(f"URL: {base_url}")
        print(f"Usuário: {username}")
        print(f"Max delay: {max_delay} segundos")
        
        # Realiza login e obtém página de status
        with requests.Session() as session:
            print("\nRealizando login...")
            token = get_auth_token(session, base_url, username, password, debug=True)
            print("Login realizado com sucesso!")
            
            print("\nObtendo página de status...")
            status_html = get_sync_status_page(session, base_url, token)
            print(f"Página obtida - tamanho: {len(status_html)} caracteres")
            
            print("\nAnalisando página...")
            status_data = parse_status_page(status_html)
            
            print(f"\n=== RESULTADOS ===")
            print(f"Data último envio: {status_data['data_ultimo_envio']}")
            print(f"Hora último envio: {status_data['hora_ultimo_envio']}")
            print(f"Problema envio: {status_data['problema_envio']}")
            print(f"Problema receb: {status_data['problema_receb']}")
            
            # Calcula diferença de tempo
            if status_data['data_ultimo_envio'] and status_data['hora_ultimo_envio']:
                try:
                    erp_datetime_str = f"{status_data['data_ultimo_envio']} {status_data['hora_ultimo_envio']}"
                    erp_time = datetime.strptime(erp_datetime_str, '%d/%m/%Y %H:%M:%S')
                    current_time = datetime.now()
                    
                    print(f"\n=== CÁLCULO DE TEMPO ===")
                    print(f"ERP datetime: {erp_time}")
                    print(f"Current datetime: {current_time}")
                    print(f"Diferença: {current_time - erp_time}")
                    
                    delay_seconds = (current_time - erp_time).total_seconds()
                    delay_minutes = delay_seconds / 60
                    
                    print(f"Delay em segundos: {delay_seconds}")
                    print(f"Delay em minutos: {delay_minutes}")
                    print(f"Max delay: {max_delay} segundos ({max_delay/60} minutos)")
                    
                    if delay_seconds > max_delay:
                        print(f"\n❌ EXCEDEU LIMITE!")
                        print(f"Excedeu em: {delay_seconds - max_delay} segundos")
                    else:
                        print(f"\n✅ DENTRO DO LIMITE!")
                        print(f"Faltam: {max_delay - delay_seconds} segundos para o limite")
                        
                except ValueError as e:
                    print(f"\n❌ Erro ao converter data/hora: {e}")
                    print(f"String tentada: '{erp_datetime_str}'")
            
    except Exception as e:
        print(f"\n❌ Erro geral: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()