#!/usr/bin/env python3
"""Teste debug para entender a estrutura HTML esperada."""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from check_sincronismo import parse_status_page
from bs4 import BeautifulSoup

# HTML de exemplo real
def criar_html_realistico():
    html = '''<div class='vista-role' style='position: absolute; top:0px; left:0px; bottom:4px; right:0px; overflow: auto;' role='vista' perfil='' cvista='2052' svistaaba='2902'>
   <div id='tbltblConCon2902' role='grid' class='div-grid-vistas' style='position: absolute;top: 59px;left: 0px;right: 0px;bottom: 10px;'>
     <div class="div-header-grid">
       <table id="tblHead" class="TGrid" cellpadding="0" cellspacing="0">
         <thead><tr>
           <th title="Cód. Local"><div>Cód. Local</div></th>
           <th title="Filial"><div>Filial</div></th>
           <th title="Data Ult. Reg. Env."><div>Data Ult. Reg. Env.</div></th>
           <th title="Hora Ultimo Reg. Env."><div>Hora Ultimo Reg. Env.</div></th>
           <th title="Log Filial p/ Sinc."><div>Log Filial p/ Sinc.</div></th>
         </tr></thead>
       </table>
     </div>
     <div class="div-grid-table-vistas" style='position: absolute;top: 53px;left: 0px;right: 0px;bottom: 0px;'>
       <table id="tblBody" class="TGrid" cellpadding="0" cellspacing="0">
         <tbody>
           <tr>
             <td coluna='Cód. Local'><div>1</div></td>
             <td coluna='Filial'><div>TESTE 1</div></td>
             <td coluna='Data Ult. Reg. Env.'><div>14/11/2025</div></td>
             <td coluna='Hora Ultimo Reg. Env.'><div>15:30:00</div></td>
             <td coluna='Log Filial p/ Sinc.'><div></div></td>
           </tr>
           <tr>
             <td coluna='Cód. Local'><div>2</div></td>
             <td coluna='Filial'><div>TESTE 2</div></td>
             <td coluna='Data Ult. Reg. Env.'><div>14/11/2025</div></td>
             <td coluna='Hora Ultimo Reg. Env.'><div>15:30:00</div></td>
             <td coluna='Log Filial p/ Sinc.'><div></div></td>
           </tr>
         </tbody>
       </table>
     </div>
   </div>
</div>'''
    return html

def test_html_simples():
    """Testa HTML simples para verificar estrutura."""
    html = criar_html_realistico()
    
    print("=== ANALISANDO HTML ===")
    soup = BeautifulSoup(html, 'html.parser')
    
    # Procura div vista-role
    div_vista = soup.find('div', class_='vista-role')
    print(f"Div vista-role encontrada: {div_vista is not None}")
    
    # Procura div tbltblConCon2902
    div_grid = soup.find('div', id='tbltblConCon2902', role='grid')
    print(f"Div tbltblConCon2902 encontrada: {div_grid is not None}")
    
    # Procura tabelas
    tbl_head = soup.find('table', id='tblHead')
    tbl_body = soup.find('table', id='tblBody')
    print(f"Tabela tblHead encontrada: {tbl_head is not None}")
    print(f"Tabela tblBody encontrada: {tbl_body is not None}")
    
    # Procura todas as tabelas
    todas_tabelas = soup.find_all('table')
    print(f"Total de tabelas encontradas: {len(todas_tabelas)}")
    
    for i, t in enumerate(todas_tabelas):
        print(f"Tabela {i}: ID='{t.get('id')}', classes={t.get('class', [])}")
        linhas = t.find_all('tr')
        print(f"  - Linhas: {len(linhas)}")
        if linhas:
            primeira = linhas[0].find_all(['th', 'td'])
            texts = [cell.get_text(strip=True) for cell in primeira]
            print(f"  - Primeira linha: {texts}")
    
    print("\n=== TESTANDO parse_status_page ===")
    try:
        result = parse_status_page(html)
        print(f"Resultado: {result}")
    except Exception as e:
        print(f"Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_html_simples()