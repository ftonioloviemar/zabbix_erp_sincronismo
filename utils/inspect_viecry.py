import os
import socket
import getpass
from vieutil import Viecry

diretorio = os.path.abspath('.')
host = socket.gethostname()
user = getpass.getuser()

cry = Viecry(diretorio, host, user)

print("--- Metodos disponiveis para o objeto Viecry ---")
print(dir(cry))
