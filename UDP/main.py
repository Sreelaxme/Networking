from UAP import Message
from Network import Client

if __name__ == "__main__":
    
    # Initialize the client
    client = Client("192.168.43.148", 1234)

    while(1):
        m = Message(1, 0, 0, input())
        m_enc = m.encode()
        client.SendPacket(m_enc)

    # Close the client
    client.Exit()
