import socket
from UAP import Message, UAP
class Server:

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_socket.bind((host, port))
        print(f"Server waiting on {host}:{port}")

    # def DecodePacket(self, data: bytes):
    #     # Override this method to decode the received data as needed
    #     return data.decode('utf-8')
    
    def HandlePacket(self, data, client_addr):
        msg = Message.decode(data)
        session_id = msg.session_id

        if session_id not in self.sessions:
            self.sessions[session_id] = client_addr  # Store client's address for this session

        # Handle the message based on its type and the session it belongs to
        if msg.command == UAP.CommandEnum.HELLO:
            print(f"Received HELLO from session {session_id}: {msg.data}")
            
    def Run(self):
        while True:
            self.ReceivePacket()
            # Add other methods or logic here

    def ReceivePacket(self):
        """
        Function to receive a packet
        """
        data, client_addr = self.server_socket.recvfrom(1024)
        while not data:
            data, clientAddr = self.server_socket.recvfrom(1024)
        self.HandlePacket(data, client_addr)

    def Exit(self):
        """
        Gracefully shut down the server.
        """
        print("Server shutting down.")
        self.server_socket.close()


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


