from UAP import Message
from Network import Client
from ThreadedNetwork import ThreadedClient

host = "192.168.43.230"
port = 12300

if __name__ == "__main__":
    
    # Initialize the client
    client = Client(host, port)

    while(1):
        m = Message(0, 0, 0, input())
        m_enc = m.encode()
        print(m_enc)
        client.SendPacket(m_enc)

    # Close the client
    client.Exit()
