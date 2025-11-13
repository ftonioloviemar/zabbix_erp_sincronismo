#!/bin/bash
# Script de Setup para Monitoramento Zabbix ERP Sincronismo

PROJECT_DIR="/usr/lib/zabbix/externalscripts/zabbix_erp_sincronismo"
ZABBIX_EXTERNAL_SCRIPTS_DIR="/usr/lib/zabbix/externalscripts" # Diretorio pai
LAUNCHER_SCRIPT_NAME="check_erp_sincronismo.sh"
PYTHON_SCRIPT_NAME="check_sincronismo.py"
ENCRYPT_SCRIPT_NAME="encrypt_password.py"
# UV_INSTALL_PATH="/root/.local/bin/uv" # Removido: uv sera chamado diretamente

echo "--- Iniciando Setup do Monitoramento Zabbix ERP Sincronismo ---"

# 1. Verificar se esta rodando como root
if [ "$EUID" -ne 0 ]; then
    echo "Por favor, execute este script como root (sudo bash setup.sh)."
    exit 1
fi

# 2. Clonar ou Atualizar o repositorio
# Garante que o diretorio pai exista e tenha permissoes adequadas
mkdir -p "$ZABBIX_EXTERNAL_SCRIPTS_DIR"
chown root:root "$ZABBIX_EXTERNAL_SCRIPTS_DIR"
chmod 755 "$ZABBIX_EXTERNAL_SCRIPTS_DIR"

if [ -d "$PROJECT_DIR" ]; then
    echo "Diretorio do projeto '$PROJECT_DIR' ja existe. Atualizando..."
    cd "$PROJECT_DIR"
    git pull origin main
else
    echo "Clonando repositorio para '$PROJECT_DIR'"
    # TROQUE A URL PELA URL DO SEU REPOSITORIO
    git clone https://github.com/ftonioloviemar/zabbix_erp_sincronismo.git "$PROJECT_DIR"
    cd "$PROJECT_DIR"
fi

# 3. Configurar ambiente Python com uv (uv run fara isso automaticamente)
echo "Configurando ambiente Python (uv run cuidara disso)..."

# 4. Configurar senha no .env (simplificado - sem criptografia)
echo "Configurando senha no arquivo .env..."
if [ ! -f ".env" ]; then
    echo "ERRO: Arquivo .env não encontrado. Copie .env.example para .env e configure as variáveis."
    exit 1
fi

# Solicitar senha e atualizar .env
read -s -p "Digite a senha do ERP: " ERP_PASSWORD_PLAINTEXT
echo "" # Nova linha apos a senha

# Atualizar a senha no .env (substituir linha existente ou adicionar)
if grep -q "ERP_PASSWORD=" .env; then
    # Substituir linha existente
    sed -i "s|ERP_PASSWORD=.*|ERP_PASSWORD=\"$ERP_PASSWORD_PLAINTEXT\"|" .env
else
    # Adicionar nova linha
    echo "ERP_PASSWORD=\"$ERP_PASSWORD_PLAINTEXT\"" >> .env
fi

# Ajustar permissões do .env (apenas owner pode ler)
chown zabbix:zabbix .env
chmod 600 .env
echo "Senha configurada no .env com permissões restritas."

# 6. Verificar se o script wrapper já existe no projeto
if [ -f "check_erp_sincronismo.sh" ]; then
    echo "Script wrapper já existe no projeto. Ajustando permissões..."
    chmod +x check_erp_sincronismo.sh
    chown root:root check_erp_sincronismo.sh
else
    echo "Criando script lancador para o Zabbix em '$PROJECT_DIR/$LAUNCHER_SCRIPT_NAME'..."
    cat <<EOF > "$PROJECT_DIR/$LAUNCHER_SCRIPT_NAME"
#!/bin/bash
# Wrapper para executar o script python no seu ambiente virtual
# Este script e chamado pelo Zabbix.

# Navega para o diretorio do projeto (onde este script esta)
cd "/usr/lib/zabbix/externalscripts/zabbix_erp_sincronismo" || { echo "Erro: Nao foi possivel navegar para o diretorio do projeto."; exit 1; }

# Executa o script Python usando uv run, que gerencia o ambiente virtual e dependencias
# e passa todos os argumentos recebidos pelo Zabbix ($@)
uv run "$PYTHON_SCRIPT_NAME" "\$@"
EOF
    chmod +x "$PROJECT_DIR/$LAUNCHER_SCRIPT_NAME"
    chown root:root "$PROJECT_DIR/$LAUNCHER_SCRIPT_NAME"
    echo "Script lancador criado e configurado."
fi

echo "--- Setup Concluido! ---"
echo "Por favor, configure o item no Zabbix com a seguinte chave:"
echo "Key: zabbix_erp_sincronismo/${LAUNCHER_SCRIPT_NAME}[\"--url\",\"{\$ERP.URL}\",\"--username\",\"{\$ERP.USER}\",\"--max-delay\",\"{\$MAX.DELAY}\"]"
echo "Lembre-se de definir as macros {\$ERP.URL}, {\$ERP.USER} e {\$MAX.DELAY} no Zabbix."