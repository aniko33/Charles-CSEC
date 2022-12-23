from threading import Thread
import socket
import rsa
import zlib
import sys
import time
import json

from rich import print

# Read config file
config_file = "config.json"
with open(config_file, "r") as f:
    config_json = json.load(f)

# Vars
clients = []
nicknames = []

# Config

"""
ip : The IP address where the server will start listening for connections
port : The connection port, it is recommended to keep it default (8889)
buffer : The maximum network buffer
welcome_message : Welcome message to new users
"""

ip: str = config_json["ip"]
port: int = config_json["port"]
buffer: int = config_json["buffer"]
welcome_message: str = config_json["welcome_message"]

# Create socket
server = socket.socket()

# Start listing
server.bind((ip, port))
server.listen(32)


class API:

    """
    def create_keys (buffer: int):
        Generate an RSA key

    def send_buffer (socket, buffer: int):
        Send the buffer to the client

    class Chat:
        arg: private_key, public_key

        def send (socket, message: str):
            Send encrypted message

        def recv (socketm, message: str):
            Receives a message and decrypt it

    class RSA:
        arg: public_key, private_key

        def encryption (message: str):
            Encrypt message

        def decrypt (message: bytes):
            Decrypt message
    """

    def create_keys(buffer: int):
        public_key, private_key = rsa.newkeys(buffer)
        return public_key, private_key

    def send_buffer(s, buffer: int):
        s.send(str(buffer).encode())

    class Chat:
        def __init__(self, priv_key, pub_key) -> None:
            self.priv_key = priv_key
            self.pub_key = pub_key

        def send(self, s, msg: str):
            s.send(rsa.encrypt(msg.encode(), self.pub_key))

        def recv(self, s, buffer: int):
            msg = s.recv(buffer)
            return rsa.decrypt(msg, self.priv_key)

    class Send_keys:
        def __init__(self, pub_key, priv_key, client) -> None:
            self.client = client
            self.pub_key = pub_key
            self.priv_key = priv_key

        def private(self):
            private_key_exported = rsa.PrivateKey.save_pkcs1(self.priv_key)
            # compressing
            private_key_exported = zlib.compress(private_key_exported, 4)
            self.client.send(private_key_exported)

        def public(self):
            public_key_exported = rsa.PublicKey.save_pkcs1(self.pub_key)
            # compressing
            public_key_exported = zlib.compress(public_key_exported, 4)
            self.client.send(public_key_exported)

    class RSA:
        def __init__(self, pub_key, priv_key) -> None:
            self.pub_key = pub_key
            self.priv_key = priv_key

        def encrypt(self, msg: str):
            return rsa.encrypt(msg.encode(), self.pub_key)

        def decrypt(self, msg: bytes):
            return rsa.decrypt(msg, self.priv_key)


class Chat:
    """
    Args: client (socket), private_key, public_key

    def joined (nickname: str):
        It will send a message when a client disconnect

    def welcome_message (bytes: bytes):
        It will send the clients the encrypted welcome message

    def send_to_clients (message: bytes):
        It sends clients a message, but it won't be able to send it to itself

    def remove_client (client):
        removes clients from the client list

    def middle:
        When a customer enters the chat, perform this function.
        Send clients a message announcing that a client has logged in,
        then wait for a message from the client and then send it to all

    def run:
        It's where this class will launch
    """

    def __init__(self, client, private_key, public_key) -> None:
        self.client = client
        self.private_key = private_key
        self.public_key = public_key

    def joined(self, nickname: str):
        self.send_to_clients(self.rsa_api.encrypt(
            f"[green]{nickname}[/green] has joined."))

    def welcome_message(self, welcome_message: bytes):
        self.client.send(welcome_message)

    def send_to_clients(self, msg: bytes):
        for client in clients:
            if client != self.client:
                try:
                    client.send(msg)
                except BaseException:
                    self.remove_client(client)

    def remove_client(self, client):
        print("[[yellow]?[/yellow]] Client disconnected")

        index = clients.index(client)
        # Remove from list
        clients.remove(client)
        # Get username from socket
        nickname = nicknames[index]

        self.send_to_clients(self.rsa_api.encrypt(
            f"[green]{nickname}[/green] has left."))

        # Remove nickname
        nicknames.remove(nickname)

    def middle(self):
        index = clients.index(self.client)
        nickname = nicknames[index]
        self.joined(nickname)

        while True:
            try:
                msg = self.client.recv(buffer)

                # If the length of the message is zero or content is "exit"
                # Remove client connection

                if msg == b"/exit" or len(msg) <= 0:
                    self.remove_client(self.client)
                    break

                self.send_to_clients(msg)

            except BaseException:
                self.remove_client(self.client)
                break

    def run(self):
        API.send_buffer(self.client, buffer)
        time.sleep(0.5)
        send_keys = API.Send_keys(
            self.public_key,
            self.private_key,
            self.client)

        self.rsa_api = API.RSA(self.public_key, self.private_key)
        self.chat_api = API.Chat(self.private_key, self.public_key)

        send_keys.public()
        time.sleep(0.5)
        send_keys.private()
        time.sleep(0.5)

        # Encrypt welcome_message and send to client
        self.welcome_message(self.rsa_api.encrypt(welcome_message))
        self.middle()


class Main:
    """
    def run:
        It will generate keys and wait for connections
    """
    def run():
        username_exist = False

        print(f"[[magenta]*[/magenta]] Buffer: {buffer}")

        print("[[cyan]+[/cyan]] RSA key generation...")
        public_key, private_key = API.create_keys(buffer)
        print("[[cyan]+[/cyan]] RSA key generated")

        while True:
            client, addr = server.accept()

            nickname = client.recv(buffer).decode()

            # Check username existing

            for list_nickname in nicknames:
                # If username_exist == False
                if not username_exist:
                    if nickname == list_nickname:
                        username_exist = True

            # If username_exist == False
            if not username_exist:
                # Send message: "accepted" to client
                client.send("/accepted".encode())
                print("[[yellow]?[/yellow]] Client connected")

                nicknames.append(nickname)
                clients.append(client)

                chat = Chat(client, private_key, public_key)

                multi_conn = Thread(target=chat.run)
                multi_conn.start()
            else:
                # Send message: "exit" to client
                client.send("/exit".encode())
                client.close()
                # Reset username_exist
                username_exist = False


if __name__ == "__main__":
    Main.run()
