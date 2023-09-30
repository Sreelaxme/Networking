
import random
import socket
import sys
import time
from Network import Client
from ThreadedNetwork import ThreadedClient
from UAP import Message, UAP

class UAPClient:
    STATES = {
        "Hello wait": 0,
        "Ready": 1,
        "Ready Timer": 2,
        "Closing": 3,
        "": 4,
    }

    def __init__(self, client: Client):
        self.instance = client
        self.state = UAPClient.STATES["Hello wait"]
        self.sID = 0
        self.seq = 0
        self.timerStart = 0
        self.waitingState = False

    def SendPacket(self, message: Message):
        self.instance.client_socket.sendall(message.encode())
        self.seq += 1

    def HandlePacket(self, message: str, isEOF=False):
        if self.state == UAPClient.STATES["Closing"]:
            return

        if self.TimerTimeout():
            return self.Exit("Timeout")

        if isEOF:
            self.SendPacket(Message(
                UAP.CommandEnum.GOODBYE,
                self.seq,
                self.sID,
                "EOF"
            ))
            self.Exit(message)
            while self.instance.running.is_set():
                pass
            return
        if message == "q":
            return self.Exit("Quitting")
        else:
            message = Message(
                UAP.CommandEnum.DATA,
                self.seq,
                self.sID,
                message
            )
            self.SendPacket(message)

    def ReceivePacket(self):
        while self.instance.running.is_set():
            try:
                data, _ = self.instance.client_socket.recvfrom(1024)
                msg = Message.decode(data)
                if msg.command == UAP.CommandEnum.HELLO:
                    print("Received Hello from server")
                if msg.command == UAP.CommandEnum.GOODBYE:
                    self.Exit("GOODBYE from server")
                if msg.command == UAP.CommandEnum.ALIVE:
                    self.TimerStart()
            except socket.timeout:
                if self.waitingState:
                    self.Exit("Timeout from wait")
                else:
                    self.waitingState = True

    def Run(self):
        self.sID = random.getrandbits(32)
        self.seq = 0
        helloMessage = Message(UAP.CommandEnum.HELLO, self.seq, self.sID, "")
        self.SendPacket(helloMessage)

        self.instance.client_socket.settimeout(self.instance.timeout)
        while True:
            try:
                data, _ = self.instance.client_socket.recvfrom(1024)
                msg = Message.decode(data)
                if msg.sID == self.sID and msg.command == UAP.CommandEnum.HELLO:
                    self.state = UAPClient.STATES["Ready"]
                    break
            except KeyboardInterrupt:
                self.Exit("Keyboard interrupt")
            except socket.timeout:
                self.Exit("Timeout")
                quit()
            except ConnectionRefusedError:
                self.Exit("Connection refused")
                quit()

        self.TimerStart()
        self.instance.Run()

    def Exit(self, reason):
        print("Closing. Reason:", reason)
        self.state = UAPClient.STATES["Closing"]
        message = Message(
            UAP.CommandEnum.GOODBYE,
            self.seq,
            self.sID,
            reason
        )
        self.SendPacket(message)

    def TimerStart(self):
        self.timerStart = time.time()

    def TimerTimeout(self):
        return time.time() - self.timerStart > self.instance.timeout

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: UAPClient.py host port [client_receive_port]")
        sys.exit(1)

    if len(sys.argv) == 3:
        client = UAPClient(ThreadedClient(sys.argv[1], int(sys.argv[2])))
    else:
        client = UAPClient(ThreadedClient(sys.argv[1], int(sys.argv[2]), int(sys.argv[3])))

    client.Run()
