import sys
import os
import socket
import rsa
import zlib
import random
import threading

from rich import print
from rich.console import Console
from rich.tree import Tree 
from rich.align import Align

console = Console()
s = socket.socket()

#var
buffer = 1024

def cls():
    os.system('cls' if os.name == 'nt' else 'clear')

class Chat:
    def __init__(self, priv_key, pub_key) -> None:
        self.priv_key = priv_key
        self.pub_key = pub_key
    def send(self, msg:str):
        s.send(rsa.encrypt(msg.encode(), self.pub_key))
    def recv(self, buffer: int):
        msg = s.recv(buffer)
        return rsa.decrypt(msg, self.priv_key).decode()

class Main:
    def __init__(self) -> None:
        pass

    class UI:
            def __init__(self) -> None:
                pass
            def random_color(self):
                #color list: https://rich.readthedocs.io/en/stable/appendix/colors.html
                colors = ["red", "blue", "cyan", "yellow", "magenta", "green", "purple", "violet", "gold"]
                
                #random choice from array
                color = random.choice(colors)
                return color
            def banner(self):
                print(Align("""[purple]
  __________________
 / ___/ __/ __/ ___/
/ /___\ \/ _// /__  
\___/___/___/\___/
""","center"))
            def get_server(self):
                server_ip = console.input("[b]Insert server address[/b] [purple]>>[/purple] ")
                server_port =  int(console.input("[b]Insert server port[/b] [purple]>>[/purple] "))
                return server_ip, server_port

            def get_username(self):
                username = console.input("[b]Insert your username[/b] [purple]>>[/purple] ")
                #random color set
                color = self.random_color()
                username_styled = f"<[{color}]{username}[/{color}]>"
                return username, username_styled

            def start(self):
                self.banner()
                ip, port = self.get_server()
                username, username_styled = self.get_username()
                return ip, port, username, username_styled

    class Load_keys:
        def __init__(self, pub_key, priv_key) -> None:
            self.pub_key = pub_key
            self.priv_key = priv_key
        
        def private(self):
            return rsa.PrivateKey.load_pkcs1(self.priv_key)

        def public(self):
            return rsa.PublicKey.load_pkcs1(self.pub_key)

        def load_all(self):
            return rsa.PrivateKey.load_pkcs1(self.priv_key), rsa.PublicKey.load_pkcs1(self.pub_key)


    def connect(self):
        while True:
            try:
                s.connect((self.ip, self.port))
            except ConnectionRefusedError:
                cls()
                print("[red]ERROR[/red]: Connection refused")
                UI = Main.UI()
                self.ip, self.port = UI.get_server()
                self.username = UI.get_username()
            else:
                break
        
        buffer = self.get_buffer()

        #decompress keys with zlib
        private_key = zlib.decompress(s.recv(buffer))
        public_key = zlib.decompress(s.recv(buffer))
        
        #key load
        client_key = self.Load_keys(public_key, private_key)
        self.private_key, self.public_key = client_key.load_all()
        
        #API
        self.chat_sock = Chat(self.private_key, self.public_key)

        #check username existing
        self.check_username(self.username)
        
        cls()
        print(Align(self.chat_sock.recv(buffer),"center"))
    
    def check_username(self, username: str):
        s.send(username.encode())
        status_code = s.recv(buffer)
        print(status_code)
        status_code = status_code.decode()
        if status_code == "False":
            s.close()
            print("[red]ERROR[/red]: This user exist")
            quit()

    def get_buffer(self):
        return int(s.recv(buffer).decode())

    def chat(self):
        def receive():
            while True:
                print(self.chat_sock.recv(buffer))
        def write():
            while True:
                msg = input()
                
                #remove input
                sys.stdout.write("\033[F")
                
                if (len(msg.strip()) > 0):
                    #switch - commands
                    match msg:
                        case _:
                            self.chat_sock.send(self.username_styled+" "+msg)
                            print("<[green][i]You[i][/green]> "+msg)
        receive_process = threading.Thread(target=receive)
        receive_process.start()
        write_process = threading.Thread(target=write)
        write_process.start()

    def run(self):
        UI = Main.UI()
        self.ip, self.port, self.username, self.username_styled = UI.start()
        self.connect()
        self.chat()
        
if __name__ == "__main__":
    main_start = Main()
    main_start.run()