# Verificador de Status de Sincronismo para Zabbix

Este projeto contem um script Python para verificar o status de sincronismo de um ERP (baseado no Tecnicon) e foi projetado para ser usado como um *External Script* no Zabbix.

## Seguranca: Criptografia de Senha Baseada em Arquivo

Para maximizar a seguranca e evitar senhas em texto plano ou mesmo senhas criptografadas em macros do Zabbix, o script utiliza a biblioteca `vieutil` que opera com um par de arquivos de chave (`.key`) e senha (`.bin`).

O fluxo de trabalho e o seguinte:

### Na sua Maquina Local (uma unica vez):

1.  **Execute o script `encrypt_password.py`:**
    Este script ira gerar dois arquivos importantes, baseados no nome do seu host e usuario (ex: `SEU_PC_SEU_USUARIO.key` e `SEU_PC_SEU_USUARIO.bin`).
    ```bash
    # Ative o ambiente virtual se necessario
    # uv venv
    python encrypt_password.py "sua-senha-em-texto-plano"
    ```

2.  **Copie os Arquivos Gerados:**
    Voce tera dois novos arquivos na pasta do projeto. Voce precisa copiá-los de forma segura (usando `scp`, por exemplo) para o servidor Zabbix.

### No Servidor Zabbix:

1.  **Cole os Arquivos:**
    Coloque os arquivos `.key` e `.bin` que voce copiou dentro da pasta do projeto no servidor (ex: `/opt/zabbix_erp_sincronismo/`).

2.  **Ajuste o Dono e Permissao (Importante!):**
    O usuario `zabbix` precisa ser capaz de ler estes arquivos.
    ```bash
    sudo chown zabbix:zabbix /opt/zabbix_erp_sincronismo/*.key /opt/zabbix_erp_sincronismo/*.bin
    sudo chmod 600 /opt/zabbix_erp_sincronismo/*.key /opt/zabbix_erp_sincronismo/*.bin
    ```

O script `check_sincronismo.py` ira automaticamente localizar e usar esses arquivos para descriptografar a senha em tempo de execucao. Nenhuma senha precisa ser passada como argumento.

## Integracao com Zabbix

1.  **Script Lançador:**
    Use o script lançador em `/usr/lib/zabbix/externalscripts/check_erp_sincronismo.sh` conforme descrito anteriormente.

2.  **Item no Zabbix (Simplificado):**
    A chave do item agora e mais simples, pois nao precisa mais da macro de senha.
    - **Key:** `check_erp_sincronismo.sh["--url","{$ERP.URL}","--username","{$ERP.USER}","--max-delay","{$MAX.DELAY}"]`

3.  **Macros no Host/Template:**
    - `{$ERP.URL}`: `http://erpdireto:8080`
    - `{$ERP.USER}`: `MONITORSINCRONISMO`
    - `{$MAX.DELAY}`: `300`
    (A macro `{$ERP.PASSWORD}` nao e mais necessaria).