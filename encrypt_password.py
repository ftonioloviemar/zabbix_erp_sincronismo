#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import os
import socket
import getpass
from vieutil import Viecry

def main():
    """Criptografa e salva a senha em um arquivo .bin para uso futuro."""
    parser = argparse.ArgumentParser(
        description="Criptografa e salva a senha do ERP em um arquivo."
    )
    parser.add_argument(
        "password",
        help="A senha em texto plano a ser criptografada."
    )
    args = parser.parse_args()

    try:
        diretorio = os.path.abspath('.')
        host = socket.gethostname()
        user = getpass.getuser()
        cry = Viecry(diretorio, host, user)
        
        # Garante que a chave exista
        if not os.path.exists(cry.key_file_name):
            print(f"Gerando nova chave em {cry.key_file_name}...")
            cry.generate_key()

        # Criptografa e salva a senha no arquivo .bin
        cry.encrypt(args.password)
        print(f"Senha salva com sucesso no arquivo: {cry.pwd_file_name}")
        print("\nCopie este arquivo e o arquivo .key correspondente para o diretorio do projeto no servidor Zabbix.")

    except Exception as e:
        print(f"Ocorreu um erro: {e}")


if __name__ == "__main__":
    main()