from UAP import Message,UAP
from Network import Client
from ThreadedNetwork import ThreadedClient
from ThreadedUAP import UAPClient

host = "192.168.43.230"
port = 12300
seq = 0
sID = 0

if __name__ == "__main__":
    
    # Initialize the client
    client = Client(host, port)
    helloMessage = Message(UAP.CommandEnum.HELLO, seq, sID, "")
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
