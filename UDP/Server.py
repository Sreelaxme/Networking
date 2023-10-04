import socket
import struct
from Network import Server
# # Constants
# MAGIC_NUMBER = 0x12345678
# VERSION = 1

# class Session:
#     def __init__(self, session_id):
#         self.session_id = session_id

#     def handle_packet(self, packet):
#         # Process the packet for this session
#         print(f"Received packet for session {self.session_id}: {packet}")

# class Server:
#     def __init__(self, host, port):
#         self.sessions = {}
#         self.host = host
#         self.port = port

#     def run(self):
#         # Create a socket and bind it to the specified host and port
#         with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server_socket:
#             server_socket.bind((self.host, self.port))
#             print("Server is listening...")

#             while True:
#                 data, addr = server_socket.recvfrom(1024)  # Receive data from clients
#                 magic, version, session_id, packet = self.parse_packet(data)

#                 if magic != MAGIC_NUMBER or version != VERSION:
#                     print("Invalid packet. Magic number or version mismatch.")
#                     continue

#                 if session_id in self.sessions:
#                     session = self.sessions[session_id]
#                 else:
#                     session = Session(session_id)
#                     self.sessions[session_id] = session

#                 session.handle_packet(packet)

#     def parse_packet(self, data):
#         magic, version, session_id, packet = struct.unpack('!IIB', data[:9])
#         return magic, version, session_id, packet

# if __name__ == "__main__":
#     server = Server('localhost', 12345)
#     server.run()

if __name__ == "__main__":
    server = Server('localhost', 12345)
    server.Run()
