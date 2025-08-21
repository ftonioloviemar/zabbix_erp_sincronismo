#!/bin/bash
# Script de Setup para Monitoramento Zabbix ERP Sincronismo

PROJECT_DIR="/usr/lib/zabbix/externalscripts/zabbix_erp_sincronismo"
ZABBIX_EXTERNAL_SCRIPTS_DIR="/usr/lib/zabbix/externalscripts" # Diretorio pai
LAUNCHER_SCRIPT_NAME="check_erp_sincronismo.sh"
PYTHON_SCRIPT_NAME="check_sincronismo.py"
ENCRYPT_SCRIPT_NAME="encrypt_password.py"
UV_INSTALL_PATH="/root/.local/bin/uv" # Default uv install path for root

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

# 4. Gerar arquivos de chave e senha
echo "Gerando arquivos de chave e senha..."
read -s -p "Digite a senha do ERP para criptografar: " ERP_PASSWORD_PLAINTEXT
echo "" # Nova linha apos a senha

"$UV_INSTALL_PATH" run python "$ENCRYPT_SCRIPT_NAME" "$ERP_PASSWORD_PLAINTEXT"

# 5. Ajustar permissoes dos arquivos de chave e senha
echo "Ajustando permissoes dos arquivos de chave e senha..."
# Encontra os arquivos .key e .bin gerados (nome dinamico)
KEY_FILE=$(find . -maxdepth 1 -name "*.key" -print -quit)
BIN_FILE=$(find . -maxdepth 1 -name "*.bin" -print -quit)

if [ -n "$KEY_FILE" ] && [ -n "$BIN_FILE" ]; then
    chown zabbix:zabbix "$KEY_FILE" "$BIN_FILE"
    chmod 600 "$KEY_FILE" "$BIN_FILE"
    echo "Permissoes ajustadas para $KEY_FILE e $BIN_FILE."
else
    echo "ERRO: Arquivos .key ou .bin nao encontrados apos a criptografia."
    exit 1
fi

# 6. Criar o script lancador para o Zabbix (dentro do diretorio do projeto)
echo "Criando script lancador para o Zabbix em '$PROJECT_DIR/$LAUNCHER_SCRIPT_NAME'..."
cat <<EOF > "$PROJECT_DIR/$LAUNCHER_SCRIPT_NAME"
#!/bin/bash
# Wrapper para executar o script python no seu ambiente virtual
# Este script e chamado pelo Zabbix.

# Navega para o diretorio do projeto (onde este script esta)
cd "$(dirname "$0")" || { echo "Erro: Nao foi possivel navegar para o diretorio do projeto."; exit 1; }

# Constrói a lista de argumentos para o script Python
PYTHON_ARGS=()
for arg in "$@"; do
    PYTHON_ARGS+=("$arg")
done

# Executa o script Python usando uv run, que gerencia o ambiente virtual e dependencias
# e passa todos os argumentos recebidos pelo Zabbix ($@)
"$UV_INSTALL_PATH" run python "$PYTHON_SCRIPT_NAME" -- "${PYTHON_ARGS[@]}"
EOF

chmod +x "$PROJECT_DIR/$LAUNCHER_SCRIPT_NAME"
chown root:root "$PROJECT_DIR/$LAUNCHER_SCRIPT_NAME" # Propriedade root para o launcher
echo "Script lancador criado e configurado."

echo "--- Setup Concluido! ---"
echo "Por favor, configure o item no Zabbix com a seguinte chave:"
echo "Key: zabbix_erp_sincronismo/${LAUNCHER_SCRIPT_NAME}[\"--url\",\"{\$ERP.URL}\",\"--username\",\"{\$ERP.USER}\",\"--max-delay\",\"{\$MAX.DELAY}\"]"
echo "Lembre-se de definir as macros {\$ERP.URL}, {\$ERP.USER} e {\$MAX.DELAY} no Zabbix."
