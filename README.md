# Verificador de Status de Sincronismo para Zabbix

Este projeto contem um script Python para verificar o status de sincronismo de um ERP (baseado no Tecnicon) e foi projetado para ser usado como um *External Script* no Zabbix.

O script executa a mesma logica de um antigo servico WebMethods, que consiste em:
1.  Fazer login no sistema ERP para obter um cookie de sessao e um token de autorizacao.
2.  Usar o token para acessar uma pagina web interna que contem os dados de status do sincronismo.
3.  Analisar o conteudo HTML dessa pagina para extrair informacoes criticas.
4.  Verificar se ha problemas reportados ou se o tempo desde o ultimo sincronismo excede um limite pre-definido.
5.  Retornar `STATUS_OK` ou `STATUS_PROBLEMA` com uma descricao do erro.

## Configuracao do Ambiente

O projeto utiliza `uv` para gerenciamento de pacotes e ambiente virtual.

1.  **Instale o uv:**
    ```bash
    pip install uv
    ```

2.  **Crie o ambiente virtual:**
    ```bash
    uv venv
    ```

3.  **Instale as dependencias:**
    ```bash
    uv pip install -r requirements.txt
    ```
    (Nota: O `pyproject.toml` contem as dependencias, o `requirements.txt` pode ser gerado com `uv pip freeze > requirements.txt`)

## Configuracao do Script

As configuracoes necessarias para o script podem ser fornecidas de duas maneiras:

### 1. Arquivo `.env` (para desenvolvimento local)

Crie um arquivo chamado `.env` na raiz do projeto, copiando o conteudo do `.env.example` e preenchendo com os valores corretos.

```dotenv
# URL base do sistema ERP
ERP_BASE_URL="http://erp.exemplo.com.br:8080"

# Credenciais de acesso para o usuario de monitoramento
ERP_USERNAME="SEU_USUARIO_MONITOR"
ERP_PASSWORD="SUA_SENHA_MONITOR"

# Limite de tempo em segundos para considerar o sincronismo atrasado
MAX_SECONDS_DELAY=300
```

### 2. Argumentos de Linha de Comando (para producao/Zabbix)

Voce pode passar os parametros diretamente ao executar o script. Isso sobrescreve os valores do arquivo `.env`.

- `--url`: URL base do ERP.
- `--username`: Usuario de monitoramento.
- `--password`: Senha do usuario.
- `--max-delay`: Atraso maximo em segundos.

## Execucao

### Teste Local

Para testar o script localmente, apos configurar o `.env`, ative o ambiente virtual e execute:

```bash
# Ativar ambiente no Windows
.venv\Scripts\activate

# Executar o script
python check_sincronismo.py
```

### Seguranca: Criptografando a Senha

Para evitar armazenar a senha do ERP em texto plano nas macros do Zabbix, o script utiliza a biblioteca `vieutil` para descriptografar a senha em tempo de execucao.

Siga os passos abaixo para gerar a senha criptografada:

1.  **Execute o script auxiliar `encrypt_password.py`:**
    No seu ambiente local (Windows ou Linux), com as dependencias instaladas, execute:
    ```bash
    python encrypt_password.py "sua-senha-em-texto-plano"
    ```

2.  **Copie a Saida:**
    O script ira imprimir a senha criptografada. Copie essa string longa.

3.  **Cole no Zabbix:**
    No Zabbix, vá ate a macro `{$ERP.PASSWORD}` do seu host e cole a senha **criptografada** que voce copiou.

O script principal `check_sincronismo.py` ira se encarregar de descriptografar este valor antes de usa-lo.

## Integracao com Zabbix

1.  **Copie o Script:** Coloque o script `check_sincronismo.py` no diretorio de scripts externos do seu Zabbix Server ou Zabbix Proxy (geralmente `/usr/lib/zabbix/externalscripts`).

2.  **Permissao de Execucao:**
    ```bash
    chmod +x /usr/lib/zabbix/externalscripts/check_sincronismo.py
    ```

3.  **Crie o Item no Zabbix:**
    - **Name:** Verificador de Sincronismo ERP
    - **Type:** `External check`
    - **Key:** `check_sincronismo.py["--url", "{$ERP.URL}", "--username", "{$ERP.USER}", "--password", "{$ERP.PASSWORD}", "--max-delay", "{$MAX.DELAY}"]`
    - **Type of information:** `Text`
    - **Update interval:** Conforme sua necessidade (ex: 5m).

4.  **Crie as Macros no Host/Template:**
    - `{$ERP.URL}`: `http://erpdireto:8080`
    - `{$ERP.USER}`: `MONITORSINCRONISMO`
    - `{$ERP.PASSWORD}`: `4px9Uh` (Recomendado usar o tipo "Secret text" do Zabbix)
    - `{$MAX.DELAY}`: `300`

5.  **Crie uma Trigger:**
    - **Name:** `ERP - Sincronismo com Problema`
    - **Expression:** `find(/Seu-Host/check_sincronismo.py...,,"like","STATUS_PROBLEMA")=1`
    - **Severity:** High (ou conforme sua necessidade)
