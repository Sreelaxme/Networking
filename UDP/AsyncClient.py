from UAP import Message,UAP
from Network import Client
import random
import time
import socket
import asyncio
import asyncudp
import sys

host = "localhost"
port = 2043
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

async def ReceivePacket(client):
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

async def InputHandler(client):
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


    

async def main(server_host, server_port):
    client = Client(server_host, server_port)   
    helloMessage = Message(UAP.CommandEnum.HELLO, seq, sID, "Hii")
    sendPacket(client,helloMessage)
    client.client_socket.settimeout(timeout)
    global isRunning
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
        receive_task = asyncio.ensure_future(ReceivePacket(client))
        input_task = asyncio.ensure_future(InputHandler(client))
        _, pending = await asyncio.wait([receive_task,input_task], return_when = asyncio.FIRST_COMPLETED)
        for i in pending:
            i.cancel()
    except Exception as e:
        print(e)
    finally:
        isRunning = False
        client.Exit()



if __name__ == "__main__":    
    if(len(sys.argv) == 3):
        asyncio.run(main(sys.argv[1],int(sys.argv[2])))
    else:
        print("Usage: python your_script.py <host> <port>")
