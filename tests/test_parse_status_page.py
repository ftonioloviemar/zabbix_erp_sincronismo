#!/usr/bin/env python3
"""Testes para validar todos os cenários da função parse_status_page."""

import os
import sys
import unittest
from datetime import datetime, timedelta

# Adiciona o diretório pai ao path para importar check_sincronismo
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from check_sincronismo import parse_status_page, STATUS_OK
from bs4 import BeautifulSoup

class TestParseStatusPage(unittest.TestCase):
    """Testes para a função parse_status_page."""
    
    def setUp(self):
        """Configuração inicial para cada teste."""
        self.maxDiff = None
    
    def criar_html_teste(self, headers, dados):
        """Cria HTML de teste com headers e dados fornecidos."""
        html = '''<html><body>
        <div class='vista-role'>
            <div id='tbltblConCon2902' role='grid' class='div-grid-vistas'>
                <div class="div-header-grid">
                    <table id="tblHead" class="TGrid" cellpadding="0" cellspacing="0">
                        <thead><tr>'''
        
        # Headers
        for header in headers:
            html += f'<th title="{header}" coluna="{header}"><div>{header}</div></th>'
        
        html += '''</tr></thead></table></div>
                <div class="div-grid-table-vistas">
                    <table id="tblBody" class="TGrid" cellpadding="0" cellspacing="0">
                        <tbody>'''
        
        # Dados (garante pelo menos 2 linhas para a função reconhecer como dados)
        if len(dados) < 2:
            # Duplica a primeira linha se tiver apenas uma
            dados = dados + dados
        
        for linha in dados:
            html += '<tr>'
            for i, valor in enumerate(linha):
                header_name = headers[i] if i < len(headers) else f'COL{i}'
                html += f'<td coluna="{header_name}"><div>{valor}</div></td>'
            html += '</tr>'
        
        html += '''</tbody></table></div></div></div>
        </body></html>'''
        return html
    
    def test_cenario_ok_completo(self):
        """Testa cenário OK: Log vazio e tempo dentro do limite."""
        # Dados com hora atual (dentro do limite)
        agora = datetime.now()
        data_str = agora.strftime('%d/%m/%Y')
        hora_str = agora.strftime('%H:%M:%S')
        
        headers = ['Cód. Local', 'Filial', 'Data Ult. Reg. Env.', 'Hora Ultimo Reg. Env.', 'Log Filial p/ Sinc.']
        dados = [
            ['1', 'FILIAL TESTE', data_str, hora_str, ''],  # Log vazio
        ]
        
        html = self.criar_html_teste(headers, dados)
        result = parse_status_page(html)
        
        # Verifica que não há problema no log
        self.assertEqual(result['problema_envio'], '')
        self.assertEqual(result['data_ultimo_envio'], data_str)
        self.assertEqual(result['hora_ultimo_envio'], hora_str)
    
    def test_cenario_problema_log(self):
        """Testa cenário PROBLEMA: Log com conteúdo."""
        agora = datetime.now()
        data_str = agora.strftime('%d/%m/%Y')
        hora_str = agora.strftime('%H:%M:%S')
        
        headers = ['Cód. Local', 'Filial', 'Data Ult. Reg. Env.', 'Hora Ultimo Reg. Env.', 'Log Filial p/ Sinc.']
        dados = [
            ['1', 'FILIAL TESTE', data_str, hora_str, 'Erro de sincronismo'],  # Log com problema
        ]
        
        html = self.criar_html_teste(headers, dados)
        result = parse_status_page(html)
        
        # Verifica que há problema no log
        self.assertIn('Log com problema', result['problema_envio'])
        self.assertIn('Erro de sincronismo', result['problema_envio'])
    
    def test_cenario_problema_multiplas_filiais(self):
        """Testa cenário PROBLEMA: Múltiplas filiais com logs."""
        agora = datetime.now()
        data_str = agora.strftime('%d/%m/%Y')
        hora_str = agora.strftime('%H:%M:%S')
        
        headers = ['Cód. Local', 'Filial', 'Data Ult. Reg. Env.', 'Hora Ultimo Reg. Env.', 'Log Filial p/ Sinc.']
        dados = [
            ['1', 'FILIAL A', data_str, hora_str, 'Erro na filial A'],
            ['2', 'FILIAL B', data_str, hora_str, ''],  # Esta está OK
            ['3', 'FILIAL C', data_str, hora_str, 'Erro na filial C'],
        ]
        
        html = self.criar_html_teste(headers, dados)
        result = parse_status_page(html)
        
        # Verifica que há problema no log com múltiplas filiais
        self.assertIn('Log com problema', result['problema_envio'])
        self.assertIn('Erro na filial A', result['problema_envio'])
        self.assertIn('Erro na filial C', result['problema_envio'])
        # A filial B não deve aparecer no problema pois está OK
        self.assertNotIn('FILIAL B', result['problema_envio'])
    
    def test_cenario_tabela_sem_cabecalho(self):
        """Testa cenário com tabela que não tem cabeçalho descritivo."""
        agora = datetime.now()
        data_str = agora.strftime('%d/%m/%Y')
        hora_str = agora.strftime('%H:%M:%S')
        
        # HTML com tabela sem cabeçalho descritivo (apenas dados)
        html = f'''
        <html>
        <body>
        <div class='vista-role'>
            <div id='tbltblConCon2902' role='grid' class='div-grid-vistas'>
                <div class="div-header-grid">
                    <table id="tblHead" class="TGrid" cellpadding="0" cellspacing="0">
                        <thead><tr>
                            <th title="COL1"><div>COL1</div></th>
                            <th title="COL2"><div>COL2</div></th>
                            <th title="COL3"><div>COL3</div></th>
                            <th title="COL4"><div>COL4</div></th>
                            <th title="COL5"><div>COL5</div></th>
                        </tr></thead></table></div>
                <div class="div-grid-table-vistas">
                    <table id="tblBody" class="TGrid" cellpadding="0" cellspacing="0">
                        <tbody>
                        <tr>
                            <td coluna="COL1"><div>1</div></td>
                            <td coluna="COL2"><div>FILIAL TESTE</div></td>
                            <td coluna="COL3"><div>{data_str}</div></td>
                            <td coluna="COL4"><div>{hora_str}</div></td>
                            <td coluna="COL5"><div></div></td>
                        </tr>
                        </tbody></table></div></div></div>
        </body>
        </html>
        '''
        
        # Neste caso, o script deve usar índices padrão ou tentar encontrar os valores
        result = parse_status_page(html)
        
        # Deve conseguir processar mesmo sem cabeçalho descritivo
        self.assertIsNotNone(result['data_ultimo_envio'])
        self.assertIsNotNone(result['hora_ultimo_envio'])
    
    def test_cenario_html_minimo(self):
        """Testa cenário com HTML mínimo contendo apenas valores."""
        agora = datetime.now()
        data_str = agora.strftime('%d/%m/%Y')
        hora_str = agora.strftime('%H:%M:%S')
        
        # HTML mínimo com estrutura básica
        html = f'''
        <html>
        <body>
        <div class='vista-role'>
            <div id='tbltblConCon2902' role='grid' class='div-grid-vistas'>
                <div class="div-header-grid">
                    <table id="tblHead" class="TGrid" cellpadding="0" cellspacing="0">
                        <thead><tr>
                            <th title="Cód. Local"><div>Cód. Local</div></th>
                            <th title="Filial"><div>Filial</div></th>
                            <th title="Data Ult. Reg. Env."><div>Data Ult. Reg. Env.</div></th>
                            <th title="Hora Ultimo Reg. Env."><div>Hora Ultimo Reg. Env.</div></th>
                            <th title="Log Filial p/ Sinc."><div>Log Filial p/ Sinc.</div></th>
                        </tr></thead></table></div>
                <div class="div-grid-table-vistas">
                    <table id="tblBody" class="TGrid" cellpadding="0" cellspacing="0">
                        <tbody>
                        <tr>
                            <td coluna="Cód. Local"><div>1</div></td>
                            <td coluna="Filial"><div>TESTE</div></td>
                            <td coluna="Data Ult. Reg. Env."><div>{data_str}</div></td>
                            <td coluna="Hora Ultimo Reg. Env."><div>{hora_str}</div></td>
                            <td coluna="Log Filial p/ Sinc."><div></div></td>
                        </tr>
                        </tbody></table></div></div></div>
        </body>
        </html>
        '''
        
        result = parse_status_page(html)
        
        # Deve conseguir extrair valores mesmo em HTML mínimo
        self.assertEqual(result['data_ultimo_envio'], data_str)
        self.assertEqual(result['hora_ultimo_envio'], hora_str)
    
    def test_cenario_log_com_espacos(self):
        """Testa cenário com log contendo apenas espaços (deve ser considerado vazio)."""
        agora = datetime.now()
        data_str = agora.strftime('%d/%m/%Y')
        hora_str = agora.strftime('%H:%M:%S')
        
        headers = ['Cód. Local', 'Filial', 'Data Ult. Reg. Env.', 'Hora Ultimo Reg. Env.', 'Log Filial p/ Sinc.']
        dados = [
            ['1', 'FILIAL TESTE', data_str, hora_str, '   '],  # Apenas espaços
        ]
        
        html = self.criar_html_teste(headers, dados)
        result = parse_status_page(html)
        
        # Espaços devem ser considerados vazio (OK)
        self.assertEqual(result['problema_envio'], '')
    
    def test_cenario_colunas_em_ordem_diferente(self):
        """Testa cenário com colunas em ordem diferente."""
        agora = datetime.now()
        data_str = agora.strftime('%d/%m/%Y')
        hora_str = agora.strftime('%H:%M:%S')
        
        # Headers em ordem diferente
        headers = ['Log Filial p/ Sinc.', 'Cód. Local', 'Hora Ultimo Reg. Env.', 'Filial', 'Data Ult. Reg. Env.']
        dados = [
            ['', '1', hora_str, 'FILIAL TESTE', data_str],  # Log vazio
        ]
        
        html = self.criar_html_teste(headers, dados)
        result = parse_status_page(html)
        
        # Deve encontrar as colunas corretas mesmo em ordem diferente
        self.assertEqual(result['problema_envio'], '')
        self.assertEqual(result['data_ultimo_envio'], data_str)
        self.assertEqual(result['hora_ultimo_envio'], hora_str)
    
    def test_cenario_tempo_limite_excedido(self):
        """Testa cenário PROBLEMA: Tempo limite excedido."""
        # Tempo passado (mais de 5 minutos atrás)
        tempo_passado = datetime.now() - timedelta(minutes=6)
        data_str = tempo_passado.strftime('%d/%m/%Y')
        hora_str = tempo_passado.strftime('%H:%M:%S')
        
        headers = ['Cód. Local', 'Filial', 'Data Ult. Reg. Env.', 'Hora Ultimo Reg. Env.', 'Log Filial p/ Sinc.']
        dados = [
            ['1', 'FILIAL TESTE', data_str, hora_str, ''],  # Log vazio mas tempo excedido
        ]
        
        html = self.criar_html_teste(headers, dados)
        result = parse_status_page(html)
        
        # Verifica que há problema de tempo
        self.assertIn('Tempo limite excedido', result['problema_envio'])
        self.assertIn('360 segundos', result['problema_envio'])  # 6 minutos = 360 segundos
    
    def test_cenario_tempo_dentro_limite(self):
        """Testa cenário OK: Tempo dentro do limite."""
        # Tempo recente (menos de 5 minutos)
        tempo_recente = datetime.now() - timedelta(minutes=3)
        data_str = tempo_recente.strftime('%d/%m/%Y')
        hora_str = tempo_recente.strftime('%H:%M:%S')
        
        headers = ['Cód. Local', 'Filial', 'Data Ult. Reg. Env.', 'Hora Ultimo Reg. Env.', 'Log Filial p/ Sinc.']
        dados = [
            ['1', 'FILIAL TESTE', data_str, hora_str, ''],  # Log vazio e tempo OK
        ]
        
        html = self.criar_html_teste(headers, dados)
        result = parse_status_page(html)
        
        # Não deve haver problema
        self.assertEqual(result['problema_envio'], '')
        self.assertEqual(result['data_ultimo_envio'], data_str)
        self.assertEqual(result['hora_ultimo_envio'], hora_str)
    
    def test_cenario_problema_log_e_tempo(self):
        """Testa cenário PROBLEMA: Ambos log e tempo com problemas."""
        # Tempo passado (mais de 5 minutos)
        tempo_passado = datetime.now() - timedelta(minutes=7)
        data_str = tempo_passado.strftime('%d/%m/%Y')
        hora_str = tempo_passado.strftime('%H:%M:%S')
        
        headers = ['Cód. Local', 'Filial', 'Data Ult. Reg. Env.', 'Hora Ultimo Reg. Env.', 'Log Filial p/ Sinc.']
        dados = [
            ['1', 'FILIAL TESTE', data_str, hora_str, 'Erro de conexão'],  # Log com problema e tempo excedido
        ]
        
        html = self.criar_html_teste(headers, dados)
        result = parse_status_page(html)
        
        # Deve reportar ambos os problemas
        self.assertIn('Log com problema', result['problema_envio'])
        self.assertIn('Erro de conexão', result['problema_envio'])
        self.assertIn('Tempo limite excedido', result['problema_envio'])
    
    def test_cenario_multiplas_filiais_tempo_misto(self):
        """Testa cenário com múltiplas filiais e tempos mistos."""
        agora = datetime.now()
        
        # Filial 1: tempo OK, log OK
        tempo_ok = agora - timedelta(minutes=2)
        data_ok = tempo_ok.strftime('%d/%m/%Y')
        hora_ok = tempo_ok.strftime('%H:%M:%S')
        
        # Filial 2: tempo excedido, log OK
        tempo_excedido = agora - timedelta(minutes=6)
        data_excedido = tempo_excedido.strftime('%d/%m/%Y')
        hora_excedido = tempo_excedido.strftime('%H:%M:%S')
        
        # Filial 3: tempo OK, log com problema
        tempo_ok2 = agora - timedelta(minutes=1)
        data_ok2 = tempo_ok2.strftime('%d/%m/%Y')
        hora_ok2 = tempo_ok2.strftime('%H:%M:%S')
        
        headers = ['Cód. Local', 'Filial', 'Data Ult. Reg. Env.', 'Hora Ultimo Reg. Env.', 'Log Filial p/ Sinc.']
        dados = [
            ['1', 'FILIAL A', data_ok, hora_ok, ''],  # OK
            ['2', 'FILIAL B', data_excedido, hora_excedido, ''],  # Tempo excedido
            ['3', 'FILIAL C', data_ok2, hora_ok2, 'Erro na filial C'],  # Log com problema
        ]
        
        html = self.criar_html_teste(headers, dados)
        result = parse_status_page(html)
        
        # Deve reportar os problemas das filiais B e C
        self.assertIn('Tempo limite excedido', result['problema_envio'])
        self.assertIn('Log com problema', result['problema_envio'])
        self.assertIn('Erro na filial C', result['problema_envio'])
        # Não deve mencionar a filial A que está OK
        self.assertNotIn('FILIAL A', result['problema_envio'])
    
    def test_cenario_formato_data_hora_diferente(self):
        """Testa cenário com formato diferente de data/hora."""
        # Testa diferentes formatos de data e hora
        formatos_teste = [
            ('14/11/2025', '15:30:00'),
            ('2025-11-14', '15:30:00'),
            ('14-11-2025', '15:30:00'),
            ('14/11/25', '15:30'),  # Sem segundos
        ]
        
        for data_str, hora_str in formatos_teste:
            with self.subTest(data=data_str, hora=hora_str):
                headers = ['Cód. Local', 'Filial', 'Data Ult. Reg. Env.', 'Hora Ultimo Reg. Env.', 'Log Filial p/ Sinc.']
                dados = [
                    ['1', 'FILIAL TESTE', data_str, hora_str, ''],  # Log vazio
                ]
                
                html = self.criar_html_teste(headers, dados)
                result = parse_status_page(html)
                
                # Deve conseguir processar diferentes formatos
                self.assertEqual(result['data_ultimo_envio'], data_str)
                self.assertEqual(result['hora_ultimo_envio'], hora_str)

if __name__ == '__main__':
    # Executa os testes
    unittest.main(verbosity=2)