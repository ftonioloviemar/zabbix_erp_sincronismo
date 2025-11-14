#!/usr/bin/env python3
"""Teste de debug para entender como a função parse_status_page procura tabelas."""

import os
import sys
from datetime import datetime, timedelta

# Adiciona o diretório pai ao path para importar check_sincronismo
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from check_sincronismo import parse_status_page
from bs4 import BeautifulSoup

def debug_html_simples():
    """Testa com HTML simples para entender o problema."""
    
    # HTML mínimo com a estrutura que a função espera
    html_minimo = '''
    <html>
    <body>
        <table id="tblHead">
            <thead>
                <tr>
                    <th>Cód. Local</th>
                    <th>Filial</th>
                    <th>Data Ult. Reg. Env.</th>
                    <th>Hora Ultimo Reg. Env.</th>
                    <th>Log Filial p/ Sinc.</th>
                </tr>
            </thead>
        </table>
        <table id="tblBody">
            <tbody>
                <tr>
                    <td>1</td>
                    <td>FILIAL TESTE</td>
                    <td>14/11/2025</td>
                    <td>15:30:00</td>
                    <td></td>
                </tr>
            </tbody>
        </table>
    </body>
    </html>
    '''
    
    print("=== Testando HTML mínimo ===")
    try:
        result = parse_status_page(html_minimo)
        print(f"Sucesso! Resultado: {result}")
    except Exception as e:
        print(f"Erro: {e}")
        
        # Debug manual
        soup = BeautifulSoup(html_minimo, 'lxml')
        todas_tabelas = soup.find_all('table')
        print(f"Total de tabelas encontradas: {len(todas_tabelas)}")
        
        for idx, t in enumerate(todas_tabelas):
            print(f"\nTabela {idx}:")
            print(f"  ID: {t.get('id', 'sem id')}")
            linhas = t.find_all('tr')
            print(f"  Total de linhas: {len(linhas)}")
            
            if len(linhas) > 0:
                primeira_linha = linhas[0].find_all(['th', 'td'])
                texts_primeira = [h.get_text(strip=True) for h in primeira_linha]
                print(f"  Primeira linha: {texts_primeira}")
                
                # Verifica se parece cabeçalho
                parece_cabecalho = False
                for texto in texts_primeira:
                    texto_upper = texto.upper()
                    if any(termo in texto_upper for termo in ['LOG', 'FILIAL', 'DATA', 'HORA', 'ENV', 'SINC']):
                        parece_cabecalho = True
                        break
                print(f"  Parece cabeçalho: {parece_cabecalho}")

def debug_html_real():
    """Testa com HTML real extraído do arquivo."""
    
    # Lê o HTML real do arquivo
    with open('debug/status_page_debug.html', 'r', encoding='utf-8') as f:
        html_real = f.read()
    
    print("\n=== Testando HTML real ===")
    try:
        result = parse_status_page(html_real)
        print(f"Sucesso! Resultado: {result}")
    except Exception as e:
        print(f"Erro: {e}")
        
        # Debug manual
        soup = BeautifulSoup(html_real, 'lxml')
        todas_tabelas = soup.find_all('table')
        print(f"Total de tabelas encontradas: {len(todas_tabelas)}")
        
        for idx, t in enumerate(todas_tabelas):
            print(f"\nTabela {idx}:")
            print(f"  ID: {t.get('id', 'sem id')}")
            linhas = t.find_all('tr')
            print(f"  Total de linhas: {len(linhas)}")
            
            if len(linhas) > 0:
                primeira_linha = linhas[0].find_all(['th', 'td'])
                texts_primeira = [h.get_text(strip=True) for h in primeira_linha]
                print(f"  Primeira linha: {texts_primeira}")
                
                # Verifica se parece cabeçalho
                parece_cabecalho = False
                for texto in texts_primeira:
                    texto_upper = texto.upper()
                    if any(termo in texto_upper for termo in ['LOG', 'FILIAL', 'DATA', 'HORA', 'ENV', 'SINC']):
                        parece_cabecalho = True
                        break
                print(f"  Parece cabeçalho: {parece_cabecalho}")

if __name__ == '__main__':
    debug_html_simples()
    debug_html_real()