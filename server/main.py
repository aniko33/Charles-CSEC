import rsa
import socket
import zlib
import time
import json
import _thread as thd

from rich import print

#start 
config_file = "config.json"
with open(config_file, "r") as f:
    config_json = json.load(f)

#vars
clients = []
username = {}

#config
ip = config_json["ip"]
port = config_json["port"]
buffer = config_json["buffer"]
welcome_message = config_json["welcome_message"]

#create socket
server = socket.socket()

#start listing
server.bind((ip,port))
server.listen(32)

#creating RSA key
def create_keys(buffer: int):
    public_key, private_key = rsa.newkeys(buffer)
    return public_key, private_key

class Chat:
    def __init__(self, priv_key, pub_key) -> None:
        self.priv_key = priv_key
        self.pub_key = pub_key
    def send(self, s, msg:str):
        s.send(rsa.encrypt(msg.encode(), self.pub_key))
    def recv(self, s, buffer: int):
        msg = s.recv(buffer)
        return rsa.decrypt(msg, self.priv_key)

class Send_keys:
    def __init__(self,pub_key, priv_key, client) -> None:
        self.client = client
        self.pub_key = pub_key
        self.priv_key = priv_key

    def private(self):
        private_key_exported = rsa.PrivateKey.save_pkcs1(self.priv_key)
        #compressing
        private_key_exported = zlib.compress(private_key_exported, 4)
        self.client.send(private_key_exported)

    def public(self):
        public_key_exported = rsa.PublicKey.save_pkcs1(self.pub_key)
        #compressing
        public_key_exported = zlib.compress(public_key_exported, 4)
        self.client.send(public_key_exported)

class Main:
    def __init__(self) -> None:
        pass

    def chat(client, public_key, private_key):
        def send_buffer():
            client.send(str(buffer).encode())

        def remove_connection(client_socket):
            if client_socket in clients:
                #remove client socket
                clients.remove(client_socket)
                #remove username
                username.pop(client_socket)
                print("[[yellow]?[/yellow]] Client disconnected")

        def send_to_clients(msg):
            for client_socket in clients:
                if client != client_socket:
                    try:
                        client_socket.send(msg)
                    except:
                        client_socket.close()
                        remove_connection(client_socket)

        def check_username():
            exist = False
            
            username_unchecked = client.recv(buffer).decode()
            for user in username:
                if not exist:
                    if username[user] == username_unchecked:
                        exist = True
            #send code status and close connection
            if exist:
                client.send("False".encode())
                remove_connection(client)
            #send code status and add username
            else: 
                client.send("True".encode())
                username[client] = username_unchecked
        def middle():
            while True:
                try:
                    msg = client.recv(buffer)
                    if msg.decode() == "/users":
                        users = ""
                        for user in username:
                            users += username[user]+","
                        client.send(users.encode())
                    else:
                        if msg:
                            send_to_clients(msg)
                        else:
                            remove_connection(client)
                except:
                    continue
        
        send_buffer()
        
        #init class for send RSA keys
        client_key = Send_keys(public_key, private_key, client)
        
        #send keys
        client_key.private(); time.sleep(0.5)
        client_key.public()
        
        #API
        chat_sock = Chat(private_key, public_key)

        time.sleep(0.5)

        #check username
        check_username()
        
        time.sleep(0.5)

        #welcome message
        chat_sock.send(client, welcome_message)

        middle()
    def run(self):
        stopped = False
        
        print(f"[[cyan]+[/cyan]] Buffer: {buffer}")

        print("[[cyan]+[/cyan]] Creating RSA keys...")
        self.public_key, self.private_key = create_keys(buffer)
        print("[[cyan]+[/cyan]] RSA keys created")
        
        while (not stopped):
            client, addr = server.accept()
            print("[[yellow]?[/yellow]] Client connected")
            #add 
            clients.append(client)

            #start in idle
            thd.start_new_thread(Main.chat, (client, self.public_key, self.private_key))

if __name__ == "__main__":
    main_start = Main()
    main_start.run()
