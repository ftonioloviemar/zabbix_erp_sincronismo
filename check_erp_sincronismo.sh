#!/bin/bash
# Wrapper para executar o script python no seu ambiente virtual
# Este script é chamado pelo Zabbix.

# Navega para o diretório do projeto (onde este script está)
cd "/usr/lib/zabbix/externalscripts/zabbix_erp_sincronismo" || { echo "Erro: Não foi possível navegar para o diretório do projeto."; exit 1; }

# Executa o script Python usando uv run, que gerencia o ambiente virtual e dependências
# e passa todos os argumentos recebidos pelo Zabbix
uv run "check_sincronismo.py" "$@"

# Alternativa com configurações mais específicas (descomente se necessário):
#!/bin/sh
#set -e
cd /usr/lib/zabbix/externalscripts/zabbix_erp_sincronismo
export HOME=/var/lib/zabbix
exec /var/lib/zabbix/.local/bin/uv run "check_sincronismo.py" "$@"