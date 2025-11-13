#!/bin/bash
# Script para configurar/reconfigurar senha no .env
# Útil quando as credenciais são perdidas durante atualizações

PROJECT_DIR="/usr/lib/zabbix/externalscripts/zabbix_erp_sincronismo"

echo "--- Configurador de Senha Simplificado ---"

# Verificar se está rodando como root
if [ "$EUID" -ne 0 ]; then
    echo "Por favor, execute este script como root (sudo bash configure_password.sh)."
    exit 1
fi

cd "$PROJECT_DIR" || { echo "ERRO: Não foi possível acessar $PROJECT_DIR"; exit 1; }

# Verificar se .env existe
if [ ! -f ".env" ]; then
    echo "Arquivo .env não encontrado. Criando a partir do exemplo..."
    cp .env.example .env
fi

# Solicitar configurações
echo "Configuração de credenciais do ERP para monitoramento:"
read -p "URL do ERP [padrão: http://erpdireto:8080]: " ERP_URL
read -p "Usuário [padrão: MONITORSINCRONISMO]: " ERP_USER
read -s -p "Senha: " ERP_PASS
echo ""

# Usar valores padrão se não fornecidos
ERP_URL=${ERP_URL:-"http://erpdireto:8080"}
ERP_USER=${ERP_USER:-"MONITORSINCRONISMO"}

# Atualizar .env
echo "Atualizando .env..."

# Atualizar URL
if grep -q "ERP_BASE_URL=" .env; then
    sed -i "s|ERP_BASE_URL=.*|ERP_BASE_URL=\"$ERP_URL\"|" .env
else
    echo "ERP_BASE_URL=\"$ERP_URL\"" >> .env
fi

# Atualizar usuário
if grep -q "ERP_USERNAME=" .env; then
    sed -i "s|ERP_USERNAME=.*|ERP_USERNAME=\"$ERP_USER\"|" .env
else
    echo "ERP_USERNAME=\"$ERP_USER\"" >> .env
fi

# Atualizar senha
if grep -q "ERP_PASSWORD=" .env; then
    sed -i "s|ERP_PASSWORD=.*|ERP_PASSWORD=\"$ERP_PASS\"|" .env
else
    echo "ERP_PASSWORD=\"$ERP_PASS\"" >> .env
fi

# Ajustar permissões
chown zabbix:zabbix .env
chmod 600 .env

echo "✅ Configuração concluída!"
echo "URL: $ERP_URL"
echo "Usuário: $ERP_USER"
echo "Senha: [configurada]"
echo ""
echo "Permissões do .env ajustadas para segurança."
echo "Testando conexão..."

# Testar conexão
if uv run check_sincronismo.py --help >/dev/null 2>&1; then
    echo "✅ Script executando corretamente!"
else
    echo "❌ ERRO: Problema ao executar script. Verifique as configurações."
fi