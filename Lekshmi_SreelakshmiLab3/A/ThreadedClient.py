from UAP import Message,UAP
from Network import Client
import random
import time
import socket
import threading
import sys

# host = "localhost"
# port = 12345
sID = random.getrandbits(32)
seq = 0

isRunning = False
timerStart = 0

timeout = 10
STATES = {
        "Hello wait": 0,
        "Ready": 1,
        "Ready Timer": 2,
        "Closing": 3,
        "": 4,
    }
currState = STATES["Hello wait"]
def sendPacket(client : Client,message : Message):
    global seq
    client.SendPacket(message.encode())
    seq +=1

def ReceivePacket(client):
    global isRunning, timerStart , currState
    while isRunning:
        try:
            data, _ = client.client_socket.recvfrom(1024)
            msg = Message.decode(data)
            if msg.command == UAP.CommandEnum.HELLO:
                print("Received Hello from server")
            if msg.command == UAP.CommandEnum.GOODBYE:
                isRunning = False
                print("GOODBYE from server")
                
            if msg.command == UAP.CommandEnum.ALIVE:
                if currState == STATES["Ready Timer"]:
                    currState = STATES["Ready"]
                    timerStart = time.time()
        except socket.timeout:
            pass

if __name__ == "__main__":    
    # Initialize the client
    if len(sys.argv) != 3:
        print("Usage: python your_script.py <host> <port>")
        sys.exit(1)

    host = sys.argv[1]
    port = int(sys.argv[2])
    client =Client(host, port)
    
    helloMessage = Message(UAP.CommandEnum.HELLO, seq, sID, "Hii")
    sendPacket(client,helloMessage)
    client.client_socket.settimeout(timeout)

    # Wait for hello
    try:
        
        while True:
            try:
                data, _ = client.client_socket.recvfrom(1024)

                if not data:
                    continue
                msg = Message.decode(data)
                if msg.session_id == sID and msg.command == UAP.CommandEnum.HELLO:
                    currState = STATES["Ready"]
                    break
            except TimeoutError:
                currState = STATES["Closing"]

        isRunning = True
        recieverThread = threading.Thread(target=ReceivePacket, args=(client,))
        recieverThread.daemon = True
        recieverThread.start()
        timerStart = time.time()
        while currState in [STATES["Ready"],STATES["Ready Timer"]]:
            if not isRunning:
                break
            try:
                m  = input()
                message = m.encode('utf-8',errors="ignore")
                m = message.decode('utf-8')  
                if(m == None or len(m)==0):
                    continue
                if(m == "eof"):   
                    currState = STATES["Closing"]
                    break 
            except EOFError:
                currState = STATES["Closing"]
                break
            except KeyboardInterrupt : 
                currState = STATES["Closing"]
                break

            if time.time() - timerStart > timeout and currState is STATES["Ready Timer"]:
                currState = STATES["Closing"]
                break
            
            
            message = Message(UAP.CommandEnum.DATA,seq,sID,m)
            sendPacket(client,message)
            currState = STATES["Ready Timer"]

        if currState == STATES["Closing"]:
            sendPacket(client, Message(UAP.CommandEnum.GOODBYE, seq, sID, "POi"))
        while isRunning:
            if time.time() - timerStart >timeout:
                isRunning = False

    except Exception as e:
        pass
    finally:
        # print("heyy")
        isRunning = False
        client.Exit()
    # Close the client
    client.Exit()
