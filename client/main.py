import sys
import os
import socket
import rsa
import time
import zlib
import random
import threading

from rich import print
from rich.console import Console
from rich.tree import Tree
from rich.align import Align

global buffer

# Vars
console = Console()
s = socket.socket()
buffer = 1024


"""
def cls:
    Clear terminal screen
"""


def cls():
    if os.name == 'nt':
        os.system('cls')

    else:
        os.system("clear")


class API:
    """
    class Chat:
        arg: private_key, public_key

        def send (message: str):
            Allows you to send an encrypted message to the server

        def recv (buffer: int):
            Receives a message from the encrypted server

    class Load_keys:
        arg: private_key, public_key

        def private:
            Load the private key

        def public:
            Load the public key

        def load_all:
            Load the private and public key
    """
    class Chat:
        def __init__(self, priv_key, pub_key) -> None:
            self.priv_key = priv_key
            self.pub_key = pub_key

        def send(self, msg: str):
            s.send(rsa.encrypt(msg.encode(), self.pub_key))

        def recv(self, buffer: int):
            msg = s.recv(buffer)
            return rsa.decrypt(msg, self.priv_key).decode()

    class Load_keys:
        def __init__(self, pub_key, priv_key) -> None:
            self.pub_key = pub_key
            self.priv_key = priv_key

        def private(self):
            return rsa.PrivateKey.load_pkcs1(self.priv_key)

        def public(self):
            return rsa.PublicKey.load_pkcs1(self.pub_key)

        def load_all(self):
            return rsa.PrivateKey.load_pkcs1(
                self.priv_key), rsa.PublicKey.load_pkcs1(self.pub_key)


class UI:
    """
    def random_color:
        It will take a random color and be entered as the username color

    def banner:
        The ASCII banner that will be centered

    def get_server:
        Get the server ip and port

    def get_username:
        Get the username from the input will send it to the server

    def run:
        Where the code will start
    """

    def __init__(self) -> None:
        pass

    def random_color(self):
        # Color list:
        # https://rich.readthedocs.io/en/stable/appendix/colors.html
        colors = [
            "red",
            "blue",
            "cyan",
            "yellow",
            "magenta",
            "green",
            "purple",
            "violet",
            "gold"]

        # Random choice from array
        color = random.choice(colors)
        return color

    def banner(self):
        print(Align(r"""[purple]
  _____  _____ ______ _____
 / ____|/ ____|  ____/ ____|
 | |    | (___ | |__ | |
 | |     \___ \|  __|| |
 | |____ ____) | |___| |____
 \_____|_____/|______\_____|
""", "center"))

    def get_server(self):

        server_ip = console.input(
            "[b]Insert server address[/b] [purple]>>[/purple] ")

        server_port = int(
            console.input("[b]Insert server port[/b] [purple]>>[/purple] "))

        # If server_ip == "local"... change server_ip to 127.0.0.1

        match server_ip:
            case "local" | "localhost" | "::1":
                server_ip = "127.0.0.1"

        return server_ip, server_port

    def get_username(self):
        username = console.input(
            "[b]Insert your username[/b] [purple]>>[/purple] ")

        # Random color set
        color = self.random_color()
        username_styled = f"<[{color}]{username}[/{color}]>"
        return username, username_styled

    def start(self):
        self.banner()
        ip, port = self.get_server()
        username, username_styled = self.get_username()
        return ip, port, username, username_styled


class Chat:
    """
    class chat_api: RSA custom socket

    var (str) username_syled: (<Username>) {
        It is the username but compliant for sending via socket
        making all the username available
    }

    var (str) username: Current username

    fun receive: Receive messages via socket
    fun write: Where the user will put the message, it will be encrypted
    fun run: Where the code will start
    """

    def __init__(self, chat_api, username_styled, username) -> None:
        self.chat_api = chat_api
        self.username_styled = username_styled
        self.username = username

    def receive(self):
        while True:
            try:
                print(self.chat_api.recv(buffer))
            except rsa.pkcs1.DecryptionError:
                pass

    def write(self):
        try:
            while True:
                msg = input()

                # Remove line up
                sys.stdout.write("\033[F")

                if (len(msg.strip()) > 0):
                    match msg:
                        case "/nick":
                            print(self.username)
                        case _:
                            self.chat_api.send(self.username_styled + " " + msg)

                            print("<[green][i]You[/i][/green]> " + msg)
        except KeyboardInterrupt:
            s.send("/exit".encode())

    def run(self):
        receive_process = threading.Thread(target=self.receive)
        receive_process.start()
        write_process = threading.Thread(target=self.write)
        write_process.start()


class Main:
    """
    def connect:
        It allows you to connect to the server, you will receive the RSA keys

    def send_username:
        Send yours username to server

    def get_buffer:
        Get from server buffer - RSA size and message size

    def get_welcome_message:
        Get welcome message from server

    def run:
        Where the code will start
    """

    def __init__(self) -> None:
        pass

    def connect(self):
        while True:
            try:
                s.connect((self.ip, self.port))
            except ConnectionRefusedError:
                cls()
                print("[red]ERROR[/red]: Connection refused")
                UI = Main.UI()
                self.ip, self.port = UI.get_server()
                self.username, self.username_styled = UI.get_username()
            else:
                break

        # Send username to server and wait 0.5s
        self.send_username(self.username)
        time.sleep(0.5)

        # Get buffer from server
        buffer = self.get_buffer()

        # Decompress keys with zlib
        public_key = zlib.decompress(s.recv(buffer))
        private_key = zlib.decompress(s.recv(buffer))

        # Key load
        client_key = API.Load_keys(public_key, private_key)
        self.private_key, self.public_key = client_key.load_all()

        # API
        self.chat_api = API.Chat(self.private_key, self.public_key)

        # Welcome screen
        cls()
        self.get_welcome_message()

        chat = Chat(self.chat_api, self.username_styled, self.username)
        chat.run()

    def send_username(self, username: str):
        s.send(username.encode())
        # Confirm: /exit or /accepted
        confirm = s.recv(1024).decode()

        if confirm != "/accepted":
            print("[red]ERROR[/red]: Username exist")
            s.close()
            quit()

    def get_buffer(self):
        return int(s.recv(buffer).decode())

    def get_welcome_message(self):
        print(Align(self.chat_api.recv(1024), "center"))

    def run(self):
        ui = UI()
        self.ip, self.port, self.username, self.username_styled = ui.start()
        self.connect()


if __name__ == "__main__":
    main = Main()
    main.run()
