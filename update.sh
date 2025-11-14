#!/bin/bash
# Script de Update para Monitoramento Zabbix ERP Sincronismo
# Atualiza o projeto forçando reset para a última versão do main,
# preserva .env e garante permissões adequadas para o usuário zabbix.

set -e

PROJECT_DIR="/usr/lib/zabbix/externalscripts/zabbix_erp_sincronismo"
BRANCH="main"
REMOTE="origin"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_DIR="/tmp/zabbix_erp_backup_${TIMESTAMP}"

echo "--- Atualizando Monitoramento Zabbix ERP Sincronismo ---"

# 1. Verificar se está rodando como root
if [ "$EUID" -ne 0 ]; then
    echo "Por favor, execute este script como root (sudo bash update.sh)."
    exit 1
fi

# 2. Verificar se o diretório do projeto existe
if [ ! -d "$PROJECT_DIR" ]; then
    echo "ERRO: Diretório do projeto '$PROJECT_DIR' não encontrado."
    echo "Execute o setup.sh primeiro para instalar o projeto."
    exit 1
fi

cd "$PROJECT_DIR"

# 3. Fazer backup dos arquivos de configuração
echo "Fazendo backup de arquivos de configuração..."
mkdir -p "$BACKUP_DIR"
cp -v .env "$BACKUP_DIR/" 2>/dev/null || true
cp -v ./*.key "$BACKUP_DIR/" 2>/dev/null || true
cp -v ./*.bin "$BACKUP_DIR/" 2>/dev/null || true

# 4. Atualizar via git (forçando reset para evitar ficar preso em versões legadas)
echo "Atualizando projeto via git (reset forçado)..."
git fetch "$REMOTE"
PREV_REF="$(git rev-parse --short HEAD || echo 'desconhecido')"
git reset --hard "$REMOTE/$BRANCH"
NEW_REF="$(git rev-parse --short HEAD || echo 'desconhecido')"

# 5. Garantir permissões adequadas (wrapper, .env, logs, debug)
echo "Ajustando permissões..."
# Scripts
for f in check_erp_sincronismo.sh setup.sh update.sh configure_password.sh; do
  if [ -f "$f" ]; then
    chmod 755 "$f"
  fi
done
if [ -f "check_erp_sincronismo.sh" ]; then
  chown root:root check_erp_sincronismo.sh
fi

# .env
if [ -f .env ]; then
  chown zabbix:zabbix .env
  chmod 600 .env
fi

# diretórios obrigatórios
mkdir -p "$PROJECT_DIR/logs" "$PROJECT_DIR/debug" "$PROJECT_DIR/tmp"
chown -R zabbix:zabbix "$PROJECT_DIR/logs" "$PROJECT_DIR/debug"
chmod 700 "$PROJECT_DIR/logs" "$PROJECT_DIR/debug"
chmod 755 "$PROJECT_DIR/tmp"

# 6. Verificar se o .env ainda existe
if [ ! -f .env ]; then
    echo "AVISO: Arquivo .env não encontrado após atualização."
    echo "Restaurando do backup..."
    cp "$BACKUP_DIR"/.env . 2>/dev/null || echo "ERRO: Não foi possível restaurar .env"
    if [ -f .env ]; then
      chown zabbix:zabbix .env
      chmod 600 .env
    fi
fi

# 7. Testar se o script ainda funciona (como root)
echo "Testando execução do script (root)..."
if uv run check_sincronismo.py --help >/dev/null 2>&1; then
    echo "✅ Script executando corretamente como root!"
else
    echo "❌ ERRO: Script não está executando corretamente como root após atualização."
fi

# 8. Testar execução como usuário zabbix (para validar permissões de logs e .env)
echo "Testando execução do script como usuário zabbix..."
UV_CMD="uv"
if [ -x "/var/lib/zabbix/.local/bin/uv" ]; then
  UV_CMD="/var/lib/zabbix/.local/bin/uv"
fi
if sudo -u zabbix HOME=/var/lib/zabbix $UV_CMD run check_sincronismo.py --help >/dev/null 2>&1; then
  echo "✅ Script executando corretamente como zabbix!"
else
  echo "❌ ERRO: Execução como zabbix falhou. Verifique permissões de 'logs/' e '.env'."
fi

# 9. Limpar backups antigos (mantém apenas os 5 mais recentes)
echo "Limpando backups antigos..."
find /tmp -maxdepth 1 -name "zabbix_erp_backup_*" -type d | sort -r | tail -n +6 | xargs rm -rf 2>/dev/null || true

echo "--- Atualização Concluída! ---"
echo "Data da atualização: $(date)"
echo "Versão anterior: ${PREV_REF}"
echo "Versão atual: ${NEW_REF}"
echo ""
echo "Arquivos de configuração preservados:"
ls -la ./*.key ./*.bin .env 2>/dev/null || echo "Nenhum arquivo de configuração encontrado"
