#!/bin/bash
# Wrapper para executar o script Python no ambiente do Zabbix
# Este script é chamado pelo Zabbix.

set -e

# Navega para o diretório do projeto (onde este script está)
cd "/usr/lib/zabbix/externalscripts/zabbix_erp_sincronismo" || { echo "Erro: Não foi possível navegar para o diretório do projeto."; exit 1; }

# Seleciona o comando uv adequado
UV_CMD="uv"
if [ -x "/var/lib/zabbix/.local/bin/uv" ]; then
  UV_CMD="/var/lib/zabbix/.local/bin/uv"
fi

# Garante HOME apropriado para o usuário zabbix (necessário para uv)
export HOME=/var/lib/zabbix

# Executa o script Python usando uv run e passa todos os argumentos
exec "$UV_CMD" run "check_sincronismo.py" "$@"
