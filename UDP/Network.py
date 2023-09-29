import socket

class Client:
    def __init__(self, host, port, timeout=5):
        self.host = host
        self.port = port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.client_socket.connect((host, port))
        print(f"Connected to server at {host}:{port}")

        self.timeout = timeout

    def SendPacket(self, message):
        self.client_socket.sendall(message)

    def HandlePacket(self, message: str, isEOF: bool = False):
        self.SendPacket(message)

    def ReceivePackets(self):
        try:
            while True:
                data, _ = self.client_socket.recvfrom(1024)  # Adjust buffer size as needed
                message = data.decode('utf-8')
                print(f"Received from server: {message}")
        except KeyboardInterrupt:
            pass

    def Run(self):
        try:
            # Start a function to receive packets
            self.ReceivePackets()

            while True:
                try:
                    message = input()
                    self.HandlePacket(message)
                except EOFError:
                    self.HandlePacket("", isEOF=True)
        except KeyboardInterrupt:
            pass
        finally:
            self.Exit()

    def Exit(self):
        self.client_socket.close()

# if __name__ == "__main__":
#     client = Client("localhost", 12345)  # Replace with your server's address and port
#     client.Run()
