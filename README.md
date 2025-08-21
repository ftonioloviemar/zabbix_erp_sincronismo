# Verificador de Status de Sincronismo para Zabbix

Este projeto contem um script Python para verificar o status de sincronismo de um ERP (baseado no Tecnicon) e foi projetado para ser usado como um *External Script* no Zabbix.

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
