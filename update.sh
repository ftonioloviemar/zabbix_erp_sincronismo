#!/bin/bash
# Script de Update para Monitoramento Zabbix ERP Sincronismo
# Este script atualiza o projeto sem recriar configurações

PROJECT_DIR="/usr/lib/zabbix/externalscripts/zabbix_erp_sincronismo"

echo "--- Atualizando Monitoramento Zabbix ERP Sincronismo ---"

# 1. Verificar se esta rodando como root
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

# 3. Fazer backup dos arquivos de configuração sensíveis
echo "Fazendo backup de arquivos de configuração..."
BACKUP_DIR="/tmp/zabbix_erp_backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp ./*.key ./*.bin .env "$BACKUP_DIR/" 2>/dev/null || true

# 4. Atualizar via git
echo "Atualizando projeto via git..."
git fetch origin
git pull origin main

# 5. Ajustar permissões do script wrapper (se foi atualizado)
if [ -f "check_erp_sincronismo.sh" ]; then
    echo "Ajustando permissões do script wrapper..."
    chmod +x check_erp_sincronismo.sh
    chown root:root check_erp_sincronismo.sh
fi

# 6. Verificar se os arquivos de configuração ainda existem
if [ ! -f .env ]; then
    echo "AVISO: Arquivo .env não encontrado após atualização."
    echo "Restaurando do backup..."
    cp "$BACKUP_DIR"/.env . 2>/dev/null || echo "ERRO: Não foi possível restaurar .env"
fi

# 7. Testar se o script ainda funciona
echo "Testando execução do script..."
if uv run check_sincronismo.py --help >/dev/null 2>&1; then
    echo "✅ Script executando corretamente!"
else
    echo "❌ ERRO: Script não está executando corretamente após atualização."
    echo "Verifique os logs em logs/ para mais detalhes."
fi

# 8. Limpar backup antigo (mantém apenas os 5 mais recentes)
echo "Limpando backups antigos..."
find /tmp -name "zabbix_erp_backup_*" -type d | sort -r | tail -n +6 | xargs rm -rf 2>/dev/null || true

echo "--- Atualização Concluída! ---"
echo "Data da atualização: $(date)"
echo "Versão atual: $(git rev-parse --short HEAD)"
echo ""
echo "Arquivos de configuração preservados:"
ls -la ./*.key ./*.bin .env 2>/dev/null || echo "Nenhum arquivo de configuração encontrado"