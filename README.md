# Verificador de Status de Sincronismo para Zabbix

Este projeto contém um script Python para verificar o status de sincronismo de um ERP (baseado no Tecnicon) e foi projetado para ser usado como um *External Script* no Zabbix.

## 🎯 Funcionalidades Principais

- **Monitoramento Completo**: Detecta erros de sincronismo em qualquer linha da tabela
- **Análise Multi-Tabela**: Identifica automaticamente a tabela correta de sincronismo
- **Detecção Inteligente de Erros**: 
  - Status HTTP 500
  - Células com fundo amarelo/vermelho
  - Textos com palavras-chave de erro ("ERRO", "PROBLEMA", "INVÁLIDO")
  - Classes CSS indicadoras de erro
- **Seleção Automática de Empresa**: Gerencia o fluxo completo de login incluindo seleção de empresa
- **Logs Detalhados**: Sistema de logging com rotação diária
- **Testes Automatizados**: Suite de testes para validação das funcionalidades
- **Integração Zabbix**: Pronto para uso como external script com códigos de retorno apropriados

## 🏗️ Arquitetura

```
zabbix_erp_sincronismo/
├── check_sincronismo.py          # Script principal de monitoramento
├── configure_password.sh       # Configurador simplificado de senhas
├── tests/                      # Testes unitários e de integração
│   ├── test_check_sincronismo.py   # Testes unitários principais
│   ├── teste_parsing.py          # Testes de parsing HTML
│   └── teste_sincronismo.py      # Testes de sincronismo completo
├── utils/                      # Utilitários e scripts auxiliares
│   ├── inspect_viecry.py       # Inspeção da criptografia Viecry (legado)
│   ├── inspect_viecry_detailed.py  # Inspeção detalhada Viecry (legado)
│   └── main.py                 # Template principal (não utilizado)
├── debug/                      # Arquivos de debug e logs HTML
│   ├── debug_login_response.html
│   ├── login_response_debug.html
│   ├── login_step1_debug.html
│   ├── login_step2_debug.html
│   └── empresa_selection_debug.html
├── tmp/                        # Arquivos temporários e de exemplo
│   └── teste_html_exemplo.html # HTML de exemplo para testes
├── docs/                       # Documentação técnica
│   └── TECHNICAL.md          # Documentação técnica detalhada
├── logs/                       # Arquivos de log (gitignored)
├── .env                        # Configurações do ambiente (gitignored)
├── .env.example                # Exemplo de configuração
├── setup.sh                    # Script de instalação para Zabbix
├── pyproject.toml              # Configuração do projeto Python
├── requirements.txt            # Dependências Python
└── uv.lock                     # Lock file do uv
```

## ⚙️ Configuração Local (Desenvolvimento)

### 1. Configuração do Ambiente
```bash
# Clone o repositório
git clone https://github.com/ftonioloviemar/zabbix_erp_sincronismo.git
cd zabbix_erp_sincronismo

# Configure o ambiente Python com uv
uv venv
uv sync

# Configure as variáveis de ambiente
cp .env.example .env
# Edite .env com suas configurações
```

### 2. Configuração das Variáveis de Ambiente
Edite o arquivo `.env` com suas configurações:
```bash
# URL base do sistema ERP
ERP_BASE_URL="http://erpdireto:8080"

# Limite de tempo em segundos para considerar o sincronismo atrasado
MAX_SECONDS_DELAY=300
```

### 3. Configuração da Senha
```bash
# Configure a senha no arquivo .env (simplificado - sem criptografia)
bash configure_password.sh
# Ou edite manualmente o arquivo .env e adicione: ERP_PASSWORD="sua_senha"
```

### 4. Execução dos Testes
```bash
# Execute os testes unitários principais
uv run pytest tests/test_check_sincronismo.py

# Ou execute testes específicos
uv run python tests/teste_parsing.py      # Testa parsing HTML
uv run python tests/teste_sincronismo.py  # Testa sincronismo completo
```

### 5. Utilitários (Legado)
```bash
# Scripts de criptografia (antigos - não necessários mais)
# uv run encrypt_password.py  # Descontinuado - use configure_password.sh

# Inspecionar criptografia Viecry
uv run utils/inspect_viecry.py
uv run utils/inspect_viecry_detailed.py
```

### 6. Execução do Script
```bash
# Execute o script de monitoramento
uv run check_sincronismo.py

# Com parâmetros personalizados
uv run check_sincronismo.py --url http://seu-erp:8080 --username MONITORSINCRONISMO --max-delay 300
```

## 📊 Saída do Script

### STATUS_OK (Código 0)
Quando não há erros de sincronismo:
```
STATUS_OK
```

### STATUS_PROBLEMA (Código 1)
Quando há erros de sincronismo:
```
STATUS_PROBLEMA: [4]: 500 | RECEBE: PROBLEMA REGISTRO RECEBIDO 2 : LOCAL: 4XML possui caracter inválido na linha 48 coluna 568 - Detalhes: An invalid XML character (Unicode: 0x2) was found in the value of attribute "HISTORYC" and element is "ROW". | 
```

## 📝 Logs e Debug

### Arquivos de Log
- Local: `logs/g70k_YYYY_MM_DD.log`
- Rotação: Diária automática (mantém 30 dias)
- Codificação: UTF-8
- Nível: INFO

### Debug de HTML
Em caso de problemas, o script salva o HTML recebido em arquivos temporários:
- Local: `%TEMP%/tmpXXXXXX.html`
- Útil para análise manual da estrutura da página

## Implantação em Produção (Servidor Zabbix)

Para implantar este monitoramento no seu servidor Zabbix (CentOS 7), siga estes passos simples:

1.  **Conecte-se ao seu servidor Zabbix via SSH.**

2.  **Clone o repositório e execute o script de setup:**
    ```bash
    # Navegue para um diretorio temporario, por exemplo, o seu home
    cd ~

    # Clone o repositorio (se ainda nao o fez)
    # TROQUE A URL PELA URL DO SEU REPOSITORIO
    git clone https://github.com/ftonioloviemar/zabbix_erp_sincronismo.git

    # Navegue para a pasta do repositorio clonado
    cd zabbix_erp_sincronismo

    # Execute o script de setup como root
    sudo bash setup.sh
    ```
    O script `setup.sh` irá:
    *   Instalar os pré-requisitos (git, python3).
    *   Clonar/Atualizar o projeto em `/usr/lib/zabbix/externalscripts/zabbix_erp_sincronismo`.
    *   Instalar e configurar o `uv` e o ambiente Python.
    *   **Pedir a senha do ERP** para criptografá-la e salvar os arquivos de chave e senha com as permissões corretas para o usuário `zabbix`.
    *   Criar o script lançador (`check_erp_sincronismo.sh`) *dentro do diretório do projeto*.

3.  **Configure o Item no Zabbix:**
    No seu frontend Zabbix, crie ou atualize o item de monitoramento com a seguinte chave:
    -   **Key:** `zabbix_erp_sincronismo/check_erp_sincronismo.sh["--url","{$ERP.URL}","--username","{$ERP.USER}","--max-delay","{$MAX.DELAY}"]`

4.  **Configure as Macros no Zabbix:**
    Defina as seguintes macros no seu host ou template no Zabbix:
    -   `{$ERP.URL}`: `http://erpdireto:8080` (ou a URL correta do seu ERP)
    -   `{$ERP.USER}`: `MONITORSINCRONISMO` (ou o usuário de monitoramento do seu ERP)
    -   `{$MAX.DELAY}`: `300` (ou o limite de atraso em segundos desejado)

O script `setup.sh` foi projetado para ser executado apenas uma vez para a configuração inicial e para atualizações futuras (basta rodar `git pull` e `sudo bash setup.sh` novamente).
