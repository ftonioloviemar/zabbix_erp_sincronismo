# Melhorias no Script de Monitoramento de Sincronismo

## Correção Principal

O script `check_sincronismo.py` foi corrigido para detectar erros em **qualquer linha** da tabela de sincronismo, não apenas na primeira linha.

### Problema Anterior
- O script só detectava erros na primeira linha da tabela
- Quando o erro estava na segunda linha (ou qualquer outra), o script não alertava

### Solução Implementada
- **Análise completa**: O script agora analisa **todas as linhas** da tabela
- **Detecção inteligente**: Detecta erros por:
  - Texto com palavras como "ERRO", "PROBL", "INVÁLIDO", "INVALID", "FALHA", "FAIL"
  - Células com fundo amarelo (`background-color: yellow`)
  - Classes CSS que indicam erro
- **Identificação da filial**: Mostra qual filial tem o problema (ex: "VMEMAR - PDA EQUIPA P 4")
- **Logs detalhados**: Registra todas as filiais analisadas e problemas encontrados

## Melhorias Adicionais

### 1. Sistema de Logging com Rotação Diária
- Logs são salvos na pasta `logs/`
- Nomenclatura: `g70k_YYYY_MM_DD.log`
- Rotação automática diária (mantém 30 dias)
- Codificação UTF-8
- Nível INFO

### 2. Testes Automatizados
- `teste_parsing.py`: Testa a detecção de erros com HTML de exemplo
- `teste_sincronismo.py`: Testa o script completo
- HTML de exemplo com a estrutura real do sistema

### 3. Melhor Tratamento de Erros
- Logs detalhados de cada etapa do processo
- Identificação clara da filial com problema
- Mensagens de erro mais informativas

## Como Funciona Agora

1. **Login no ERP**: Realiza login e obtém token de autenticação
2. **Busca status**: Obtém a página HTML com o status do sincronismo
3. **Análise completa**: 
   - Percorre **todas as linhas** da tabela
   - Para cada linha, verifica **todas as células**
   - Detecta erros por texto, estilo CSS ou classes
4. **Relatório**: 
   - Se encontrar erro em **qualquer** linha → STATUS_PROBLEMA
   - Se todas as linhas estiverem OK → STATUS_OK

## Exemplo de Detecção

```
Linha 1: BANCO TECNICON → OK ✓
Linha 2: VMEMAR - PDA EQUIPA P 4 → ERRO DETECTADO ⚠️
    Motivo: Célula com fundo amarelo + texto "ERRO: XML possui caractere inválido..."
```

## Saída para o Zabbix

- `STATUS_OK` → Sincronismo funcionando corretamente
- `STATUS_PROBLEMA: [NOME_FILIAL]: descrição do erro` → Problema detectado

## Arquivos de Teste

- `teste_html_exemplo.html`: HTML com a estrutura real mostrada na imagem
- `teste_parsing.py`: Testa a detecção de erros
- `teste_sincronismo.py`: Testa o script completo

## Verificação

Execute o teste para verificar se a correção está funcionando:

```bash
uv run teste_parsing.py
```

O teste deve mostrar que o erro na segunda linha (VMEMAR - PDA EQUIPA P 4) agora é detectado corretamente.