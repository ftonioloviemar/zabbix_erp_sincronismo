# Changelog

Todas as alterações notáveis deste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2024-11-13

### Simplificado
- **Removida criptografia de senhas**: Senha agora é armazenada em texto aberto no .env
- **Simplificado processo de configuração**: Não precisa mais gerar arquivos .key/.bin
- **Adicionado configure_password.sh**: Script simples para configurar senha
- **Atualizado setup.sh**: Agora configura senha diretamente no .env
- **Atualizado update.sh**: Remove backup de arquivos de criptografia

### Segurança
- **Permissões restritas no .env**: Arquivo configurado com chmod 600 (apenas owner)
- **Propriedade zabbix:zabbix**: Arquivo .env pertence ao usuário zabbix
- **Aviso em .env.example**: Documentado que senha está em texto aberto

### Benefícios da Simplificação
- **Mais fácil atualização**: Não perde mais credenciais durante git pull
- **Processo mais simples**: Elimina complexidade da criptografia
- **Manutenção facilitada**: Configurações centralizadas no .env
- **Menos dependências**: Remove dependência do vieutil

## [1.1.0] - 2024-11-13

### Adicionado
- Estrutura de pastas organizada seguindo melhores práticas Python
- Pasta `tests/` para arquivos de teste
- Pasta `utils/` para utilitários e scripts auxiliares
- Pasta `debug/` para arquivos HTML de debug
- Pasta `tmp/` para arquivos temporários e de exemplo
- CHANGELOG.md para registro de alterações

### Alterado
- **Reorganização completa da estrutura do projeto:**
  - `teste_parsing.py` → `tests/teste_parsing.py`
  - `teste_sincronismo.py` → `tests/teste_sincronismo.py`
  - `inspect_viecry.py` → `utils/inspect_viecry.py`
  - `inspect_viecry_detailed.py` → `utils/inspect_viecry_detailed.py`
  - `main.py` → `utils/main.py`
  - `debug_login_response.html` → `debug/debug_login_response.html`
  - `login_response_debug.html` → `debug/login_response_debug.html` (arquivo duplicado na raiz removido)
  - `login_step1_debug.html` → `debug/login_step1_debug.html`
  - `login_step2_debug.html` → `debug/login_step2_debug.html`
  - `teste_html_exemplo.html` → `tmp/teste_html_exemplo.html`

### Atualizado
- **Documentação:**
  - `README.md` atualizado com nova estrutura de pastas
  - `docs/TECHNICAL.md` atualizado com diagrama de arquivos reorganizado
  - Instruções de teste atualizadas com novos caminhos

- **Scripts de teste:**
  - `tests/teste_parsing.py`: Atualizado caminhos para arquivos HTML
  - `tests/teste_sincronismo.py`: Atualizado importações e caminhos

### Mantido
- Funcionalidade completa do sistema de monitoramento
- Scripts principais (`check_sincronismo.py`, `encrypt_password.py`) permanecem na raiz
- Configurações e arquivos de ambiente permanecem na raiz
- Estrutura de logs e funcionamento do sistema inalterados

### Benefícios da Reorganização
- **Melhor organização:** Arquivos agrupados por função
- **Facilidade de manutenção:** Estrutura clara e intuitiva
- **Padrões Python:** Segue convenções da comunidade Python
- **Escalabilidade:** Facilita adição de novos componentes
- **Clareza:** Separacao clara entre código, testes, utilitários e arquivos temporários

## [1.0.0] - 2024-11-12

### Adicionado
- Sistema completo de monitoramento de sincronismo ERP
- Detecção automática de erros em tabelas HTML
- Suporte a múltiplos critérios de erro (HTTP 500, fundo amarelo, texto de erro)
- Criptografia segura de senhas com Fernet
- Sistema de logging com rotação diária
- Testes unitários e de integração
- Documentação técnica completa
- Script de instalação automatizado
- Integração com Zabbix via external scripts

### Funcionalidades
- Monitoramento de sincronismo entre ERP e filiais
- Detecção de erros de XML e caracteres inválidos
- Relatórios detalhados por filial
- Integração nativa com Zabbix
- Logs estruturados com rotação automática
- Tratamento de autenticação e seleção de empresa