import os
import socket
import getpass
from vieutil import Viecry

print("--- Inspecao Detalhada da Classe Viecry ---")

# 1. Inicializacao
diretorio = os.path.abspath('.')
host = socket.gethostname()
user = getpass.getuser()
print(f"Inicializando com: dir='{diretorio}', host='{host}', user='{user}'")
cry = Viecry(diretorio, host, user)

# 2. Geracao de Chave (se necessario)
key_file = cry.key_file_name
if not os.path.exists(key_file):
    print(f"Arquivo de chave '{key_file}' nao encontrado. Gerando nova chave...")
    cry.generate_key()
    if os.path.exists(key_file):
        print("Chave gerada com sucesso.")
    else:
        print("ERRO: generate_key() foi chamado, mas o arquivo de chave nao foi criado.")
else:
    print(f"Usando chave existente: {key_file}")

# 3. Tentativa de Criptografia
password_to_encrypt = "4px9Uh"
print(f"\nChamando encrypt('{password_to_encrypt}')...")
result = cry.encrypt(password_to_encrypt)
print(f"Resultado retornado por encrypt(): {result}")

# 4. Verificando se arquivos foram criados/modificados
print("\nVerificando arquivos no diretorio:")
files = os.listdir('.')
print(files)

pwd_file = cry.pwd_file_name
print(f"O nome do arquivo de senha esperado e: '{pwd_file}'")
if os.path.exists(pwd_file):
    print(f"Arquivo de senha '{pwd_file}' ENCONTRADO.")
    with open(pwd_file, 'rb') as f:
        content = f.read()
    print(f"Conteudo do arquivo de senha (bytes): {content}")

    # 5. Tentativa de Descriptografia
    print(f"\nChamando decrypt() com o conteudo do arquivo...")
    try:
        decrypted_result = cry.decrypt(content)
        print(f"Resultado da descriptografia: {decrypted_result}")
    except Exception as e:
        print(f"Erro ao chamar decrypt(content): {e}")
else:
    print(f"ERRO: Arquivo de senha '{pwd_file}' NAO foi encontrado.")
