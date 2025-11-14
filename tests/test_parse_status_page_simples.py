#!/usr/bin/env python3
"""Testes simples para validar a função parse_status_page com HTML real."""

import os
import sys
import unittest
from datetime import datetime, timedelta

# Adiciona o diretório pai ao path para importar check_sincronismo
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from check_sincronismo import parse_status_page, STATUS_OK

class TestParseStatusPageSimples(unittest.TestCase):
    """Testes simples para a função parse_status_page."""
    
    def setUp(self):
        """Configuração inicial para cada teste."""
        self.maxDiff = None
    
    def criar_html_base(self):
        """Cria HTML base com a estrutura real do sistema."""
        return '''<div class='vista-role' style='position: absolute; top:0px; left:0px; bottom:4px; right:0px; overflow: auto;' role='vista' perfil='' cvista='2052' svistaaba='2902'>
   <div id='tbltblConCon2902' role='grid' class='div-grid-vistas' tempoupdate='00:00:00' cabecalho='Cód. Local||Filial||Ultimo Reg. Receb.||Data Ult. Reg. Receb.||Hora Ult. Reg. Receb.||Ultimo Reg. Env.||Qtde Falta Receber||Data Ult. Reg. Env.||Hora Ultimo Reg. Env.||Qtde Falta Enviar||Qtde Receber||Qtde Enviar||Log Filial p/ Sinc.||Data Atual||Log Sinc. p/ Filial||Hr Atual' style='position: absolute;top: 59px;left: 0px;right: 0px;bottom: 10px;' realce='null'>
     <div class="div-header-grid">
         <table id="tblHead" class="TGrid" cellpadding="0" cellspacing="0">
             <thead>
                 <tr>
                     <th title="Cód. Local" coluna="Cód. Local"><div>Cód. Local</div></th>
                     <th title="Filial" coluna="Filial"><div>Filial</div></th>
                     <th title="Data Ult. Reg. Env." coluna="Data Ult. Reg. Env."><div>Data Ult. Reg. Env.</div></th>
                     <th title="Hora Ultimo Reg. Env." coluna="Hora Ultimo Reg. Env."><div>Hora Ultimo Reg. Env.</div></th>
                     <th title="Log Filial p/ Sinc." coluna="Log Filial p/ Sinc."><div>Log Filial p/ Sinc.</div></th>
                 </tr>
             </thead>
         </table>
     </div>
     <div class="div-grid-table-vistas">
         <table id="tblBody" class="TGrid" cellpadding="0" cellspacing="0">
             <tbody>
                 {conteudo_dados}
             </tbody>
         </table>
     </div>
   </div>
</div>'''
    
    def test_cenario_ok_simples(self):
        """Testa cenário OK: Log vazio e tempo dentro do limite."""
        # Dados com hora atual (dentro do limite)
        agora = datetime.now()
        data_str = agora.strftime('%d/%m/%Y')
        hora_str = agora.strftime('%H:%M:%S')
        
        dados_html = f'''
                 <tr>
                     <td coluna="Cód. Local"><div>1</div></td>
                     <td coluna="Filial"><div>FILIAL TESTE</div></td>
                     <td coluna="Data Ult. Reg. Env."><div>{data_str}</div></td>
                     <td coluna="Hora Ultimo Reg. Env."><div>{hora_str}</div></td>
                     <td coluna="Log Filial p/ Sinc."><div></div></td>
                 </tr>'''
        
        html = self.criar_html_base().format(conteudo_dados=dados_html)
        result = parse_status_page(html)
        
        # Verifica que não há problema no log
        self.assertEqual(result['problema_envio'], '')
        self.assertEqual(result['data_ultimo_envio'], data_str)
        self.assertEqual(result['hora_ultimo_envio'], hora_str)
    
    def test_cenario_problema_log_simples(self):
        """Testa cenário PROBLEMA: Log com conteúdo."""
        agora = datetime.now()
        data_str = agora.strftime('%d/%m/%Y')
        hora_str = agora.strftime('%H:%M:%S')
        
        dados_html = f'''
                 <tr>
                     <td coluna="Cód. Local"><div>1</div></td>
                     <td coluna="Filial"><div>FILIAL TESTE</div></td>
                     <td coluna="Data Ult. Reg. Env."><div>{data_str}</div></td>
                     <td coluna="Hora Ultimo Reg. Env."><div>{hora_str}</div></td>
                     <td coluna="Log Filial p/ Sinc."><div>Erro de sincronismo</div></td>
                 </tr>'''
        
        html = self.criar_html_base().format(conteudo_dados=dados_html)
        result = parse_status_page(html)
        
        # Verifica que há problema no log
        self.assertIn('Erro de sincronismo', result['problema_envio'])
    
    def test_cenario_tempo_excedido_simples(self):
        """Testa cenário PROBLEMA: Tempo limite excedido."""
        # Tempo passado (mais de 5 minutos atrás)
        tempo_passado = datetime.now() - timedelta(minutes=6)
        data_str = tempo_passado.strftime('%d/%m/%Y')
        hora_str = tempo_passado.strftime('%H:%M:%S')
        
        dados_html = f'''
                 <tr>
                     <td coluna="Cód. Local"><div>1</div></td>
                     <td coluna="Filial"><div>FILIAL TESTE</div></td>
                     <td coluna="Data Ult. Reg. Env."><div>{data_str}</div></td>
                     <td coluna="Hora Ultimo Reg. Env."><div>{hora_str}</div></td>
                     <td coluna="Log Filial p/ Sinc."><div></div></td>
                 </tr>'''
        
        html = self.criar_html_base().format(conteudo_dados=dados_html)
        result = parse_status_page(html)
        
        # Verifica que há problema de tempo
        self.assertIn('Tempo limite excedido', result['problema_envio'])
    
    def test_cenario_multiplas_filiais_simples(self):
        """Testa cenário com múltiplas filiais."""
        agora = datetime.now()
        
        # Filial 1: OK
        tempo_ok = agora - timedelta(minutes=2)
        data_ok = tempo_ok.strftime('%d/%m/%Y')
        hora_ok = tempo_ok.strftime('%H:%M:%S')
        
        # Filial 2: Tempo excedido
        tempo_excedido = agora - timedelta(minutes=6)
        data_excedido = tempo_excedido.strftime('%d/%m/%Y')
        hora_excedido = tempo_excedido.strftime('%H:%M:%S')
        
        dados_html = f'''
                 <tr>
                     <td coluna="Cód. Local"><div>1</div></td>
                     <td coluna="Filial"><div>FILIAL A</div></td>
                     <td coluna="Data Ult. Reg. Env."><div>{data_ok}</div></td>
                     <td coluna="Hora Ultimo Reg. Env."><div>{hora_ok}</div></td>
                     <td coluna="Log Filial p/ Sinc."><div></div></td>
                 </tr>
                 <tr>
                     <td coluna="Cód. Local"><div>2</div></td>
                     <td coluna="Filial"><div>FILIAL B</div></td>
                     <td coluna="Data Ult. Reg. Env."><div>{data_excedido}</div></td>
                     <td coluna="Hora Ultimo Reg. Env."><div>{hora_excedido}</div></td>
                     <td coluna="Log Filial p/ Sinc."><div></div></td>
                 </tr>'''
        
        html = self.criar_html_base().format(conteudo_dados=dados_html)
        result = parse_status_page(html)
        
        # Deve reportar o problema da filial B
        self.assertIn('Tempo limite excedido', result['problema_envio'])
        # Não deve mencionar a filial A que está OK
        self.assertNotIn('FILIAL A', result['problema_envio'])

if __name__ == '__main__':
    # Executa os testes
    unittest.main(verbosity=2)