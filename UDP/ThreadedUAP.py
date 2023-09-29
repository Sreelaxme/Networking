import random
from UAP import Message, UAP
from Network import Client

class UAPClient(Client):

    STATES = {
        "Hello wait"    : 0,
        "Ready"         : 1,
        "Ready Timer"   : 2,
        "Closing"       : 3,
        ""              : 4,
    }

    def __init__(self, client: Client):
        super().__init__(client.host, client.port)
        self.instance = client
        self.state = UAPClient.STATES["Hello wait"]

        self.instance.SendPacket = self.SendPacket
        self.instance.HandlePacket = self.HandlePacket
        self.instance.ReceivePackets = self.ReceivePackets

    def SendPacket(self, message: Message):
        self.client_socket.sendall(message.encode())

    def HandlePacket(self, message: str, isEOF: bool = False):
        if isEOF:
            self.SendPacket(Message(UAP.CommandEnum.GOODBYE,self.seq,self.sID,"EOF"))
            while self.instance.running.is_set():
                pass
            return
        if message == "q":
            message = Message(
                UAP.CommandEnum.GOODBYE,
                self.seq,
                self.sID,
                ""
            )
        else:
            message = Message(
                UAP.CommandEnum.DATA, 
                self.seq, 
                self.sID, 
                message
            )
        self.SendPacket(message)

    def ReceivePackets(self):
        try:
            while self.running.is_set():
                data, _ = self.client_socket.recvfrom(1024)
                msg = Message.decode(data)
                if msg.command == UAP.CommandEnum.GOODBYE:
                    self.Exit("GOODBYE from server")
        except KeyboardInterrupt:
            pass

    def Run(self):
        # Session start hello
        self.sID = random.getrandbits(32)
        self.seq = 0
        helloMessage = Message(UAP.CommandEnum.HELLO, self.seq, self.sID, "")
        self.SendPacket(helloMessage)

        # Wait for hello
        while True:
            data, _ = self.client_socket.recvfrom(1024)
            msg = Message.decode(data)
            if msg.sID == self.sID and msg.command == UAP.CommandEnum.HELLO:
                self.state = UAPClient.STATES["Ready"]
                break

        self.instance.Run()

    def Exit(self, reason):
        self.instance.Exit(reason)
