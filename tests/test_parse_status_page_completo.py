#!/usr/bin/env python3
"""Teste completo para validar a função parse_status_page com todos os cenários."""

import os
import sys
from datetime import datetime, timedelta

# Adiciona o diretório pai ao path para importar check_sincronismo
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from check_sincronismo import parse_status_page, STATUS_OK
from bs4 import BeautifulSoup

def carregar_html_real():
    """Carrega o HTML real do arquivo debug."""
    with open('debug/status_page_debug.html', 'r', encoding='utf-8') as f:
        return f.read()

def modificar_dados(html_base, filiais):
    """Modifica os dados das filiais no HTML."""
    soup = BeautifulSoup(html_base, 'lxml')
    
    # Encontra o tbody
    tbody = soup.find('tbody')
    if tbody:
        # Limpa o conteúdo existente
        tbody.clear()
        
        # Adiciona novas linhas
        for i, filial in enumerate(filiais):
            tr = soup.new_tag('tr')
            
            # Cód. Local
            td = soup.new_tag('td', coluna='Cód. Local')
            div = soup.new_tag('div')
            div.string = str(i + 1)
            td.append(div)
            tr.append(td)
            
            # Filial
            td = soup.new_tag('td', coluna='Filial')
            div = soup.new_tag('div')
            div.string = filial['nome']
            td.append(div)
            tr.append(td)
            
            # Ultimo Reg. Receb.
            td = soup.new_tag('td', coluna='Ultimo Reg. Receb.')
            div = soup.new_tag('div')
            div.string = ''
            td.append(div)
            tr.append(td)
            
            # Data Ult. Reg. Receb.
            td = soup.new_tag('td', coluna='Data Ult. Reg. Receb.')
            div = soup.new_tag('div')
            div.string = filial['data_receb']
            td.append(div)
            tr.append(td)
            
            # Hora Ult. Reg. Receb.
            td = soup.new_tag('td', coluna='Hora Ult. Reg. Receb.')
            div = soup.new_tag('div')
            div.string = filial['hora_receb']
            td.append(div)
            tr.append(td)
            
            # Ultimo Reg. Env.
            td = soup.new_tag('td', coluna='Ultimo Reg. Env.')
            div = soup.new_tag('div')
            div.string = '1000'
            td.append(div)
            tr.append(td)
            
            # Qtde Falta Receber
            td = soup.new_tag('td', coluna='Qtde Falta Receber')
            div = soup.new_tag('div')
            div.string = '0'
            td.append(div)
            tr.append(td)
            
            # Data Ult. Reg. Env.
            td = soup.new_tag('td', coluna='Data Ult. Reg. Env.')
            div = soup.new_tag('div')
            div.string = filial['data_envio']
            td.append(div)
            tr.append(td)
            
            # Hora Ultimo Reg. Env.
            td = soup.new_tag('td', coluna='Hora Ultimo Reg. Env.')
            div = soup.new_tag('div')
            div.string = filial['hora_envio']
            td.append(div)
            tr.append(td)
            
            # Qtde Falta Enviar
            td = soup.new_tag('td', coluna='Qtde Falta Enviar')
            div = soup.new_tag('div')
            div.string = '0'
            td.append(div)
            tr.append(td)
            
            # Qtde Receber
            td = soup.new_tag('td', coluna='Qtde Receber')
            div = soup.new_tag('div')
            div.string = '500'
            td.append(div)
            tr.append(td)
            
            # Qtde Enviar
            td = soup.new_tag('td', coluna='Qtde Enviar')
            div = soup.new_tag('div')
            div.string = '500'
            td.append(div)
            tr.append(td)
            
            # Log Filial p/ Sinc.
            td = soup.new_tag('td', coluna='Log Filial p/ Sinc.')
            div = soup.new_tag('div')
            div.string = filial['log_problema']
            td.append(div)
            tr.append(td)
            
            # Data Atual (oculta)
            td = soup.new_tag('td', coluna='Data Atual', style='display:none;')
            div = soup.new_tag('div')
            div.string = datetime.now().strftime('%d/%m/%Y')
            td.append(div)
            tr.append(td)
            
            # Log Sinc. p/ Filial
            td = soup.new_tag('td', coluna='Log Sinc. p/ Filial')
            div = soup.new_tag('div')
            div.string = ''
            td.append(div)
            tr.append(td)
            
            # Hr Atual (oculta)
            td = soup.new_tag('td', coluna='Hr Atual', style='display:none;')
            div = soup.new_tag('div')
            div.string = datetime.now().strftime('%H:%M:%S')
            td.append(div)
            tr.append(td)
            
            tbody.append(tr)
    
    return str(soup)

def testar_todos_cenarios():
    """Testa todos os cenários possíveis."""
    
    html_base = carregar_html_real()
    agora = datetime.now()
    
    print("=== TESTES DA FUNÇÃO PARSE_STATUS_PAGE ===\n")
    
    # Teste 1: Cenário OK (sem problemas)
    print("1. Testando cenário OK (sem problemas):")
    filiais = [
        {
            'nome': 'FILIAL TESTE OK',
            'data_receb': agora.strftime('%d/%m/%Y'),
            'hora_receb': agora.strftime('%H:%M:%S'),
            'data_envio': agora.strftime('%d/%m/%Y'),
            'hora_envio': agora.strftime('%H:%M:%S'),
            'log_problema': ''
        }
    ]
    
    html_modificado = modificar_dados(html_base, filiais)
    try:
        result = parse_status_page(html_modificado)
        print(f"   Resultado: {result}")
        if result['problema_envio'] == '':
            print("   ✅ STATUS_OK - Nenhum problema detectado")
        else:
            print(f"   ❌ Problema inesperado: {result['problema_envio']}")
    except Exception as e:
        print(f"   ❌ Erro: {e}")
    
    # Teste 2: Cenário com problema no log
    print("\n2. Testando cenário com problema no log:")
    filiais = [
        {
            'nome': 'FILIAL COM LOG PROBLEMA',
            'data_receb': agora.strftime('%d/%m/%Y'),
            'hora_receb': agora.strftime('%H:%M:%S'),
            'data_envio': agora.strftime('%d/%m/%Y'),
            'hora_envio': agora.strftime('%H:%M:%S'),
            'log_problema': 'Erro de conexão com servidor'
        }
    ]
    
    html_modificado = modificar_dados(html_base, filiais)
    try:
        result = parse_status_page(html_modificado)
        print(f"   Resultado: {result}")
        if 'Erro de conexão com servidor' in result['problema_envio']:
            print("   ✅ Problema no log detectado corretamente")
        else:
            print(f"   ❌ Problema no log não detectado: {result['problema_envio']}")
    except Exception as e:
        print(f"   ❌ Erro: {e}")
    
    # Teste 3: Cenário com tempo excedido
    print("\n3. Testando cenário com tempo excedido:")
    tempo_excedido = agora - timedelta(minutes=6)  # 6 minutos atrás
    filiais = [
        {
            'nome': 'FILIAL TEMPO EXCEDIDO',
            'data_receb': agora.strftime('%d/%m/%Y'),
            'hora_receb': agora.strftime('%H:%M:%S'),
            'data_envio': tempo_excedido.strftime('%d/%m/%Y'),
            'hora_envio': tempo_excedido.strftime('%H:%M:%S'),
            'log_problema': ''
        }
    ]
    
    html_modificado = modificar_dados(html_base, filiais)
    try:
        result = parse_status_page(html_modificado)
        print(f"   Resultado: {result}")
        if 'Tempo limite excedido' in result['problema_envio']:
            print("   ✅ Tempo excedido detectado corretamente")
        else:
            print(f"   ❌ Tempo excedido não detectado: {result['problema_envio']}")
    except Exception as e:
        print(f"   ❌ Erro: {e}")
    
    # Teste 4: Cenário com ambos os problemas
    print("\n4. Testando cenário com ambos os problemas (log e tempo):")
    tempo_excedido = agora - timedelta(minutes=7)  # 7 minutos atrás
    filiais = [
        {
            'nome': 'FILIAL AMBOS PROBLEMAS',
            'data_receb': agora.strftime('%d/%m/%Y'),
            'hora_receb': agora.strftime('%H:%M:%S'),
            'data_envio': tempo_excedido.strftime('%d/%m/%Y'),
            'hora_envio': tempo_excedido.strftime('%H:%M:%S'),
            'log_problema': 'Erro de timeout na conexão'
        }
    ]
    
    html_modificado = modificar_dados(html_base, filiais)
    try:
        result = parse_status_page(html_modificado)
        print(f"   Resultado: {result}")
        if 'Erro de timeout na conexão' in result['problema_envio'] and 'Tempo limite excedido' in result['problema_envio']:
            print("   ✅ Ambos os problemas detectados corretamente")
        else:
            print(f"   ❌ Problemas não detectados corretamente: {result['problema_envio']}")
    except Exception as e:
        print(f"   ❌ Erro: {e}")
    
    # Teste 5: Cenário com múltiplas filiais (mistos)
    print("\n5. Testando cenário com múltiplas filiais (mistos):")
    tempo_ok = agora - timedelta(minutes=2)  # 2 minutos atrás (OK)
    tempo_excedido = agora - timedelta(minutes=6)  # 6 minutos atrás (excedido)
    
    filiais = [
        {
            'nome': 'FILIAL A (OK)',
            'data_receb': agora.strftime('%d/%m/%Y'),
            'hora_receb': agora.strftime('%H:%M:%S'),
            'data_envio': tempo_ok.strftime('%d/%m/%Y'),
            'hora_envio': tempo_ok.strftime('%H:%M:%S'),
            'log_problema': ''
        },
        {
            'nome': 'FILIAL B (TEMPO EXCEDIDO)',
            'data_receb': agora.strftime('%d/%m/%Y'),
            'hora_receb': agora.strftime('%H:%M:%S'),
            'data_envio': tempo_excedido.strftime('%d/%m/%Y'),
            'hora_envio': tempo_excedido.strftime('%H:%M:%S'),
            'log_problema': ''
        },
        {
            'nome': 'FILIAL C (LOG PROBLEMA)',
            'data_receb': agora.strftime('%d/%m/%Y'),
            'hora_receb': agora.strftime('%H:%M:%S'),
            'data_envio': tempo_ok.strftime('%d/%m/%Y'),
            'hora_envio': tempo_ok.strftime('%H:%M:%S'),
            'log_problema': 'Erro na filial C'
        }
    ]
    
    html_modificado = modificar_dados(html_base, filiais)
    try:
        result = parse_status_page(html_modificado)
        print(f"   Resultado: {result}")
        
        # Deve reportar os problemas das filiais B e C
        tempos_excedidos = 'Tempo limite excedido' in result['problema_envio']
        log_problemas = 'Erro na filial C' in result['problema_envio']
        
        if tempos_excedidos and log_problemas:
            print("   ✅ Problemas das filiais B e C detectados corretamente")
        else:
            print(f"   ❌ Problemas não detectados corretamente: {result['problema_envio']}")
            
        # Não deve mencionar a filial A que está OK
        if 'FILIAL A' not in result['problema_envio']:
            print("   ✅ Filial A (OK) não mencionada nos problemas")
        else:
            print(f"   ❌ Filial A (OK) mencionada indevidamente: {result['problema_envio']}")
            
    except Exception as e:
        print(f"   ❌ Erro: {e}")
    
    # Teste 6: Cenário com log contendo apenas espaços
    print("\n6. Testando cenário com log contendo apenas espaços:")
    filiais = [
        {
            'nome': 'FILIAL ESPACOS',
            'data_receb': agora.strftime('%d/%m/%Y'),
            'hora_receb': agora.strftime('%H:%M:%S'),
            'data_envio': agora.strftime('%d/%m/%Y'),
            'hora_envio': agora.strftime('%H:%M:%S'),
            'log_problema': '   '  # Apenas espaços
        }
    ]
    
    html_modificado = modificar_dados(html_base, filiais)
    try:
        result = parse_status_page(html_modificado)
        print(f"   Resultado: {result}")
        if result['problema_envio'] == '':
            print("   ✅ Espaços considerados vazio corretamente")
        else:
            print(f"   ❌ Espaços não considerados vazio: {result['problema_envio']}")
    except Exception as e:
        print(f"   ❌ Erro: {e}")

if __name__ == '__main__':
    testar_todos_cenarios()