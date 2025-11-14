#!/usr/bin/env python3
"""Testes usando HTML real do arquivo debug/status_page_debug.html."""

import os
import sys
import unittest
from datetime import datetime, timedelta

# Adiciona o diretório pai ao path para importar check_sincronismo
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from check_sincronismo import parse_status_page, STATUS_OK

def carregar_html_real():
    """Carrega o HTML real do arquivo debug."""
    with open('debug/status_page_debug.html', 'r', encoding='utf-8') as f:
        return f.read()

def modificar_html(html_base, dados_filiais):
    """Modifica o HTML base para incluir os dados das filiais fornecidos."""
    from bs4 import BeautifulSoup
    
    soup = BeautifulSoup(html_base, 'lxml')
    
    # Encontra o tbody
    tbody = soup.find('tbody')
    if tbody:
        # Limpa o conteúdo existente
        tbody.clear()
        
        # Adiciona novas linhas
        for i, filial in enumerate(dados_filiais):
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
            
            # Log Filial p/ Sinc.
            td = soup.new_tag('td', coluna='Log Filial p/ Sinc.')
            div = soup.new_tag('div')
            div.string = filial['log_problema']
            td.append(div)
            tr.append(td)
            
            tbody.append(tr)
    
    return str(soup)

class TestParseStatusPageReal(unittest.TestCase):
    """Testes usando HTML real modificado."""
    
    def setUp(self):
        """Configuração inicial para cada teste."""
        self.maxDiff = None
        self.html_base = carregar_html_real()
    
    def test_cenario_ok_simples(self):
        """Testa cenário OK: Log vazio e tempo dentro do limite."""
        agora = datetime.now()
        data_str = agora.strftime('%d/%m/%Y')
        hora_str = agora.strftime('%H:%M:%S')
        
        dados_filiais = [
            {
                'nome': 'FILIAL TESTE',
                'data_envio': data_str,
                'hora_envio': hora_str,
                'log_problema': ''
            }
        ]
        
        html_modificado = modificar_html(self.html_base, dados_filiais)
        result = parse_status_page(html_modificado)
        
        # Verifica que não há problema no log
        self.assertEqual(result['problema_envio'], '')
        self.assertEqual(result['data_ultimo_envio'], data_str)
        self.assertEqual(result['hora_ultimo_envio'], hora_str)
    
    def test_cenario_problema_log_simples(self):
        """Testa cenário PROBLEMA: Log com conteúdo."""
        agora = datetime.now()
        data_str = agora.strftime('%d/%m/%Y')
        hora_str = agora.strftime('%H:%M:%S')
        
        dados_filiais = [
            {
                'nome': 'FILIAL TESTE',
                'data_envio': data_str,
                'hora_envio': hora_str,
                'log_problema': 'Erro de sincronismo'
            }
        ]
        
        html_modificado = modificar_html(self.html_base, dados_filiais)
        result = parse_status_page(html_modificado)
        
        # Verifica que há problema no log
        self.assertIn('Erro de sincronismo', result['problema_envio'])
    
    def test_cenario_tempo_excedido_simples(self):
        """Testa cenário PROBLEMA: Tempo limite excedido."""
        # Tempo passado (mais de 5 minutos atrás)
        tempo_passado = datetime.now() - timedelta(minutes=6)
        data_str = tempo_passado.strftime('%d/%m/%Y')
        hora_str = tempo_passado.strftime('%H:%M:%S')
        
        dados_filiais = [
            {
                'nome': 'FILIAL TESTE',
                'data_envio': data_str,
                'hora_envio': hora_str,
                'log_problema': ''
            }
        ]
        
        html_modificado = modificar_html(self.html_base, dados_filiais)
        result = parse_status_page(html_modificado)
        
        # Verifica que há problema de tempo
        self.assertIn('Tempo limite excedido', result['problema_envio'])
    
    def test_cenario_multiplas_filiais_misto(self):
        """Testa cenário com múltiplas filiais e problemas mistos."""
        agora = datetime.now()
        
        # Filial 1: OK
        tempo_ok = agora - timedelta(minutes=2)
        data_ok = tempo_ok.strftime('%d/%m/%Y')
        hora_ok = tempo_ok.strftime('%H:%M:%S')
        
        # Filial 2: Tempo excedido
        tempo_excedido = agora - timedelta(minutes=6)
        data_excedido = tempo_excedido.strftime('%d/%m/%Y')
        hora_excedido = tempo_excedido.strftime('%H:%M:%S')
        
        # Filial 3: Log com problema
        tempo_ok2 = agora - timedelta(minutes=1)
        data_ok2 = tempo_ok2.strftime('%d/%m/%Y')
        hora_ok2 = tempo_ok2.strftime('%H:%M:%S')
        
        dados_filiais = [
            {
                'nome': 'FILIAL A',
                'data_envio': data_ok,
                'hora_envio': hora_ok,
                'log_problema': ''
            },
            {
                'nome': 'FILIAL B',
                'data_envio': data_excedido,
                'hora_envio': hora_excedido,
                'log_problema': ''
            },
            {
                'nome': 'FILIAL C',
                'data_envio': data_ok2,
                'hora_envio': hora_ok2,
                'log_problema': 'Erro na filial C'
            }
        ]
        
        html_modificado = modificar_html(self.html_base, dados_filiais)
        result = parse_status_page(html_modificado)
        
        # Deve reportar os problemas das filiais B e C
        self.assertIn('Tempo limite excedido', result['problema_envio'])
        self.assertIn('Erro na filial C', result['problema_envio'])
        # Não deve mencionar a filial A que está OK
        self.assertNotIn('FILIAL A', result['problema_envio'])
    
    def test_cenario_log_com_espacos(self):
        """Testa cenário com log contendo apenas espaços (deve ser considerado vazio)."""
        agora = datetime.now()
        data_str = agora.strftime('%d/%m/%Y')
        hora_str = agora.strftime('%H:%M:%S')
        
        dados_filiais = [
            {
                'nome': 'FILIAL TESTE',
                'data_envio': data_str,
                'hora_envio': hora_str,
                'log_problema': '   '  # Apenas espaços
            }
        ]
        
        html_modificado = modificar_html(self.html_base, dados_filiais)
        result = parse_status_page(html_modificado)
        
        # Espaços devem ser considerados vazio (OK)
        self.assertEqual(result['problema_envio'], '')
    
    def test_cenario_ambos_problemas(self):
        """Testa cenário PROBLEMA: Ambos log e tempo com problemas."""
        # Tempo passado (mais de 5 minutos)
        tempo_passado = datetime.now() - timedelta(minutes=7)
        data_str = tempo_passado.strftime('%d/%m/%Y')
        hora_str = tempo_passado.strftime('%H:%M:%S')
        
        dados_filiais = [
            {
                'nome': 'FILIAL TESTE',
                'data_envio': data_str,
                'hora_envio': hora_str,
                'log_problema': 'Erro de conexão'
            }
        ]
        
        html_modificado = modificar_html(self.html_base, dados_filiais)
        result = parse_status_page(html_modificado)
        
        # Deve reportar ambos os problemas
        self.assertIn('Erro de conexão', result['problema_envio'])
        self.assertIn('Tempo limite excedido', result['problema_envio'])

if __name__ == '__main__':
    # Executa os testes
    unittest.main(verbosity=2)