import socket

class Client:
    def __init__(self, host, port, timeout=5):
        self.host = host
        self.port = port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.client_socket.bind(("0.0.0.0",2048))
        self.client_socket.connect((host, port))
        print(f"Connected to server at {host}:{port}")

        self.timeout = timeout

    def SendPacket(self, message):
        self.client_socket.sendall(message)

    def HandlePacket(self, message: str, isEOF: bool = False):
        self.SendPacket(message)
        

    def Exit(self):
        self.client_socket.close()


