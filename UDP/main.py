from UAP import Message
from Network import Client
from ThreadedNetwork import ThreadedClient

if __name__ == "__main__":
    
    # Initialize the client
    client = ThreadedClient("192.168.43.230", 10101)

    while(1):
        m = Message(1, 0, 0, input())
        m_enc = m.encode()
        client.SendPacket(m_enc)

    # Close the client
    client.Exit()
