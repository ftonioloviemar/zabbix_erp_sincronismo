#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
from vieutil import Viecry


def main():
    """Gera uma senha criptografada para usar no script de monitoramento."""
    parser = argparse.ArgumentParser(
        description="Criptografa uma senha para uso no Zabbix."
    )
    parser.add_argument(
        "password",
        help="A senha em texto plano a ser criptografada."
    )
    args = parser.parse_args()

    try:
        cry = Viecry()
        encrypted_password = cry.criptografar(args.password)
        print("--- SENHA CRIPTOGRAFADA ---")
        print(encrypted_password)
        print("\nCopie a string acima e cole no campo da macro {$ERP.PASSWORD} no Zabbix.")
    except Exception as e:
        print(f"Ocorreu um erro ao criptografar a senha: {e}")


if __name__ == "__main__":
    main()
