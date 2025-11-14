#!/usr/bin/env python3
"""Script de debug direto para a função parse_status_page."""

import os
import sys
from datetime import datetime

# Adiciona o diretório atual ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bs4 import BeautifulSoup
import logging

# Configura logging básico
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def parse_status_page_debug(html_content):
    """Versão debug da função parse_status_page."""
    try:
        soup = BeautifulSoup(html_content, 'lxml')
        
        print("=== DEBUG PARSE_STATUS_PAGE ===")
        
        # Encontra a tabela de sincronismo
        tabela = None
        todas_tabelas = soup.find_all('table')
        
        print(f"Total de tabelas encontradas: {len(todas_tabelas)}")
        
        for idx, t in enumerate(todas_tabelas):
            print(f"\n--- Analisando Tabela {idx} ---")
            linhas = t.find_all('tr')
            print(f"Total de linhas: {len(linhas)}")
            
            if len(linhas) > 0:
                # Analisa primeira linha
                primeira_linha = linhas[0].find_all(['th', 'td'])
                texts_primeira = [h.get_text(strip=True) for h in primeira_linha]
                print(f"Primeira linha: {texts_primeira}")
                
                # Verifica se parece ser cabeçalho
                parece_cabecalho = False
                for texto in texts_primeira:
                    texto_upper = texto.upper()
                    if any(termo in texto_upper for termo in ['LOG', 'FILIAL', 'DATA', 'HORA', 'ENV', 'SINC']):
                        parece_cabecalho = True
                        break
                
                print(f"Parece cabeçalho: {parece_cabecalho}")
                
                if parece_cabecalho:
                    tabela = t
                    print("✅ Usando esta tabela!")
                    break
        
        if not tabela:
            print("❌ Nenhuma tabela de sincronismo encontrada")
            return None
        
        # Analisa estrutura da tabela escolhida
        print(f"\n=== ANÁLISE DA TABELA ESCOLHIDA ===")
        todas_linhas = tabela.find_all('tr')
        print(f"Total de linhas: {len(todas_linhas)}")
        
        # Analisa estrutura
        primeira_linha = todas_linhas[0].find_all(['th', 'td'])
        primeira_linha_texts = [h.get_text(strip=True) for h in primeira_linha]
        print(f"Primeira linha: {primeira_linha_texts}")
        
        # Verifica se é cabeçalho ou dados
        parece_cabecalho = False
        for texto in primeira_linha_texts:
            texto_upper = texto.upper()
            if any(termo in texto_upper for termo in ['LOG', 'FILIAL', 'DATA', 'HORA', 'ENV', 'SINC']):
                parece_cabecalho = True
                break
        
        print(f"Primeira linha é cabeçalho: {parece_cabecalho}")
        
        if parece_cabecalho:
            header_texts = primeira_linha_texts
            linhas_dados = todas_linhas[1:]  # Pula cabeçalho
            print(f"Usando cabeçalho: {header_texts}")
        else:
            print("Primeira linha é dados - usando mapeamento por posição")
            header_texts = primeira_linha_texts
            linhas_dados = todas_linhas  # Usa todas as linhas como dados
        
        # Encontra índices das colunas
        print(f"\n=== PROCURANDO ÍNDICES DAS COLUNAS ===")
        coluna_log_idx = None
        coluna_data_envio_idx = None
        coluna_hora_envio_idx = None
        
        print(f"Estrutura de colunas: {header_texts}")
        
        for idx, header in enumerate(header_texts):
            header_upper = header.upper().strip()
            print(f"Coluna {idx}: '{header}' -> '{header_upper}'")
            
            # Procura por coluna de log (prioridade máxima)
            if 'LOG FILIAL' in header_upper and 'SINC' in header_upper:
                coluna_log_idx = idx
                print(f"✅ Log Filial p/ Sinc. encontrado no índice: {idx}")
            
            # Procura por data de envio
            elif 'DATA' in header_upper and 'ENV' in header_upper and 'ULT' in header_upper:
                coluna_data_envio_idx = idx
                print(f"✅ Data Ult. Reg. Env. encontrado no índice: {idx}")
            
            # Procura por hora de envio
            elif 'HORA' in header_upper and ('ENV' in header_upper or 'ULT' in header_upper):
                coluna_hora_envio_idx = idx
                print(f"✅ Hora Ultimo Reg. Env. encontrado no índice: {idx}")
        
        print(f"\nÍndices encontrados:")
        print(f"  Log: {coluna_log_idx}")
        print(f"  Data: {coluna_data_envio_idx}")
        print(f"  Hora: {coluna_hora_envio_idx}")
        
        # Se não encontrou, tenta índices padrão baseado na estrutura típica
        if coluna_data_envio_idx is None and len(header_texts) > 7:
            coluna_data_envio_idx = 7
            print(f"Usando índice padrão para data: {coluna_data_envio_idx}")
            
        if coluna_hora_envio_idx is None and len(header_texts) > 8:
            coluna_hora_envio_idx = 8
            print(f"Usando índice padrão para hora: {coluna_hora_envio_idx}")
            
        if coluna_log_idx is None and len(header_texts) > 12:
            coluna_log_idx = 12
            print(f"Usando índice padrão para log: {coluna_log_idx}")
        
        print(f"\nÍndices finais:")
        print(f"  Log: {coluna_log_idx}")
        print(f"  Data: {coluna_data_envio_idx}")
        print(f"  Hora: {coluna_hora_envio_idx}")
        
        # Analisa dados
        print(f"\n=== ANALISANDO DADOS ===")
        print(f"Total de linhas de dados: {len(linhas_dados)}")
        
        if len(linhas_dados) > 0:
            # Pega a primeira linha de dados
            primeira_dados = linhas_dados[0].find_all('td')
            dados_texts = [d.get_text(strip=True) for d in primeira_dados]
            print(f"Primeira linha de dados: {dados_texts}")
            
            # Verifica valores das colunas importantes
            if coluna_log_idx is not None and coluna_log_idx < len(dados_texts):
                print(f"Valor Log Filial p/ Sinc. (idx {coluna_log_idx}): '{dados_texts[coluna_log_idx]}'")
            
            if coluna_data_envio_idx is not None and coluna_data_envio_idx < len(dados_texts):
                print(f"Valor Data Ult. Reg. Env. (idx {coluna_data_envio_idx}): '{dados_texts[coluna_data_envio_idx]}'")
            
            if coluna_hora_envio_idx is not None and coluna_hora_envio_idx < len(dados_texts):
                print(f"Valor Hora Ultimo Reg. Env. (idx {coluna_hora_envio_idx}): '{dados_texts[coluna_hora_envio_idx]}'")
        
        # Prepara resultados
        log_com_conteudo = False
        conteudo_log = []
        ultima_data_envio = None
        ultima_hora_envio = None
        
        # Analisa cada linha de dados
        for idx, linha in enumerate(linhas_dados):
            celulas = linha.find_all('td')
            if len(celulas) <= max(coluna_log_idx or 0, coluna_data_envio_idx or 0, coluna_hora_envio_idx or 0):
                continue
            
            # Verifica a coluna de log
            if coluna_log_idx is not None and coluna_log_idx < len(celulas):
                texto_log = celulas[coluna_log_idx].get_text(strip=True)
                if texto_log:
                    log_com_conteudo = True
                    conteudo_log.append(texto_log)
            
            # Pega a data/hora do último registro
            if coluna_data_envio_idx is not None and coluna_hora_envio_idx is not None:
                if coluna_data_envio_idx < len(celulas) and coluna_hora_envio_idx < len(celulas):
                    data_texto = celulas[coluna_data_envio_idx].get_text(strip=True)
                    hora_texto = celulas[coluna_hora_envio_idx].get_text(strip=True)
                    
                    if data_texto and hora_texto:
                        ultima_data_envio = data_texto
                        ultima_hora_envio = hora_texto
        
        print(f"\n=== RESULTADOS FINAIS ===")
        print(f"Log com conteúdo: {log_com_conteudo}")
        print(f"Conteúdo do log: {conteudo_log}")
        print(f"Última data envio: {ultima_data_envio}")
        print(f"Última hora envio: {ultima_hora_envio}")
        
        # Prepara problema_envio
        problema_envio = ""
        if log_com_conteudo:
            problema_envio = f"Log com problema: {' | '.join(conteudo_log)}"
        
        data = {
            'data_ultimo_envio': ultima_data_envio or "",
            'hora_ultimo_envio': ultima_hora_envio or "",
            'problema_envio': problema_envio,
            'problema_receb': "",
        }
        
        return data
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Função principal de debug."""
    # Lê o HTML salvo
    try:
        with open('debug/status_page_debug.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        print(f"HTML carregado - tamanho: {len(html_content)} caracteres")
        
        # Executa o debug
        result = parse_status_page_debug(html_content)
        
        if result:
            print(f"\n=== RESULTADO FINAL ===")
            print(f"Data: {result['data_ultimo_envio']}")
            print(f"Hora: {result['hora_ultimo_envio']}")
            print(f"Problema: {result['problema_envio']}")
        
    except Exception as e:
        print(f"❌ Erro geral: {e}")

if __name__ == "__main__":
    main()