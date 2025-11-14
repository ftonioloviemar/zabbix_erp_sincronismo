#!/usr/bin/env python3
"""Teste simples para validar a função parse_status_page com HTML real."""

import os
import sys
from datetime import datetime, timedelta

# Adiciona o diretório pai ao path para importar check_sincronismo
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from check_sincronismo import parse_status_page, STATUS_OK

def teste_simples():
    """Teste simples com HTML real."""
    
    # Carrega o HTML real
    with open('debug/status_page_debug.html', 'r', encoding='utf-8') as f:
        html_real = f.read()
    
    print("=== Testando HTML real ===")
    try:
        result = parse_status_page(html_real)
        print(f"✅ Sucesso! Resultado: {result}")
        
        # Verifica se está OK (sem problemas)
        if result['problema_envio'] == '':
            print("✅ STATUS_OK - Nenhum problema detectado")
        else:
            print(f"⚠️  Problemas detectados: {result['problema_envio']}")
            
    except Exception as e:
        print(f"❌ Erro: {e}")

def teste_com_alteracoes():
    """Testa com alterações no HTML para simular problemas."""
    from bs4 import BeautifulSoup
    
    # Carrega o HTML real
    with open('debug/status_page_debug.html', 'r', encoding='utf-8') as f:
        html_real = f.read()
    
    # Teste 1: Adicionar problema no log
    print("\n=== Teste 1: Adicionando problema no log ===")
    soup = BeautifulSoup(html_real, 'lxml')
    
    # Encontra a célula do log e adiciona um problema
    celula_log = soup.find('td', {'coluna': 'Log Filial p/ Sinc.'})
    if celula_log:
        div = celula_log.find('div')
        if div:
            div.string = 'Erro de conexão com o servidor'
    
    html_modificado = str(soup)
    try:
        result = parse_status_page(html_modificado)
        print(f"✅ Resultado: {result}")
        
        if 'Erro de conexão com o servidor' in result['problema_envio']:
            print("✅ Problema no log detectado corretamente")
        else:
            print("❌ Problema no log não detectado")
            
    except Exception as e:
        print(f"❌ Erro: {e}")
    
    # Teste 2: Alterar tempo para excedido
    print("\n=== Teste 2: Alterando tempo para excedido ===")
    soup = BeautifulSoup(html_real, 'lxml')
    
    # Encontra a célula da hora e altera para 6 minutos atrás
    agora = datetime.now()
    tempo_excedido = agora - timedelta(minutes=6)
    hora_excedido = tempo_excedido.strftime('%H:%M:%S')
    
    celula_hora = soup.find('td', {'coluna': 'Hora Ultimo Reg. Env.'})
    if celula_hora:
        div = celula_hora.find('div')
        if div:
            div.string = hora_excedido
    
    html_modificado = str(soup)
    try:
        result = parse_status_page(html_modificado)
        print(f"✅ Resultado: {result}")
        
        if 'Tempo limite excedido' in result['problema_envio']:
            print("✅ Tempo excedido detectado corretamente")
        else:
            print("❌ Tempo excedido não detectado")
            
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == '__main__':
    teste_simples()
    teste_com_alteracoes()