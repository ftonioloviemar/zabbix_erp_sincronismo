#!/usr/bin/env python3
"""Script de debug para testar apenas a função parse_status_page."""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Adiciona o diretório atual ao path para importar o script principal
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from check_sincronismo import parse_status_page, setup_logging
from bs4 import BeautifulSoup

def main():
    """Função de debug para testar parsing."""
    load_dotenv()
    logger = setup_logging()
    
    print("=== DEBUG DA FUNÇÃO PARSE_STATUS_PAGE ===")
    
    # Lê o HTML salvo anteriormente
    try:
        with open('debug/status_page_debug.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        print(f"HTML carregado - tamanho: {len(html_content)} caracteres")
        
        # Testa a função de parsing
        print("\nExecutando parse_status_page...")
        result = parse_status_page(html_content)
        
        print(f"\n=== RESULTADOS ===")
        print(f"Data último envio: {result['data_ultimo_envio']}")
        print(f"Hora último envio: {result['hora_ultimo_envio']}")
        print(f"Problema envio: {result['problema_envio']}")
        print(f"Problema receb: {result['problema_receb']}")
        
        # Análise manual para comparar
        print(f"\n=== ANÁLISE MANUAL ===")
        soup = BeautifulSoup(html_content, 'lxml')
        
        # Encontra a tabela correta (Tabela 1 baseada no debug anterior)
        tabelas = soup.find_all('table')
        if len(tabelas) > 1:
            tabela = tabelas[1]  # Segunda tabela
            headers = tabela.find_all('tr')[0].find_all(['th', 'td'])
            header_texts = [h.get_text(strip=True) for h in headers]
            print(f"Headers: {header_texts}")
            
            # Encontra os índices manualmente
            for idx, header in enumerate(header_texts):
                header_upper = header.upper()
                if 'LOG FILIAL' in header_upper and 'SINC' in header_upper:
                    print(f"✅ Log Filial p/ Sinc. encontrado no índice: {idx}")
                elif 'DATA' in header_upper and 'ENV' in header_upper and 'ULT' in header_upper:
                    print(f"✅ Data Ult. Reg. Env. encontrado no índice: {idx}")
                elif 'HORA' in header_upper and ('ENV' in header_upper or 'ULT' in header_upper):
                    print(f"✅ Hora Ultimo Reg. Env. encontrado no índice: {idx}")
            
            # Mostra a primeira linha de dados
            if len(tabela.find_all('tr')) > 1:
                primeira_dados = tabela.find_all('tr')[1].find_all('td')
                dados_texts = [d.get_text(strip=True) for d in primeira_dados]
                print(f"Primeira linha de dados: {dados_texts}")
                
                # Mostra valores específicos
                log_idx = None
                data_idx = None
                hora_idx = None
                
                for idx, header in enumerate(header_texts):
                    header_upper = header.upper()
                    if 'LOG FILIAL' in header_upper and 'SINC' in header_upper:
                        log_idx = idx
                    elif 'DATA' in header_upper and 'ENV' in header_upper and 'ULT' in header_upper:
                        data_idx = idx
                    elif 'HORA' in header_upper and ('ENV' in header_upper or 'ULT' in header_upper):
                        hora_idx = idx
                
                if log_idx is not None and log_idx < len(dados_texts):
                    print(f"Valor Log Filial p/ Sinc.: '{dados_texts[log_idx]}'")
                if data_idx is not None and data_idx < len(dados_texts):
                    print(f"Valor Data Ult. Reg. Env.: '{dados_texts[data_idx]}'")
                if hora_idx is not None and hora_idx < len(dados_texts):
                    print(f"Valor Hora Ultimo Reg. Env.: '{dados_texts[hora_idx]}'")
        
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Cria diretório debug se não existir
    os.makedirs('debug', exist_ok=True)
    main()