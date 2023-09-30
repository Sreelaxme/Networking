from UAP import Message,UAP
from Network import Client
from ThreadedNetwork import ThreadedClient
from ThreadedUAP import UAPClient

host = "localhost"
port = 12301
seq = 0
sID = 0

if __name__ == "__main__":
    
    # Initialize the client
    client = UAPClient(Client(host, port))
    
    client.Run()
    helloMessage = Message(UAP.CommandEnum.HELLO, seq, sID, "Hii")
    Client.SendPacket(helloMessage)
    

    # Wait for hello
    while True:
        data, _ = client.client_socket.recvfrom(1024)
        msg = Message.decode(data)
        if msg.sID == sID and msg.command == UAP.CommandEnum.HELLO:
            state = UAPClient.STATES["Ready"]
            break
    # client.Run()
    # while(1):
    #     m = Message(0, 0, 0, "hellppppp")
    #     m_enc = m.encode()
    #     print(m_enc)
    #     client.SendPacket(m_enc)

    # Close the client
    client.Exit()
