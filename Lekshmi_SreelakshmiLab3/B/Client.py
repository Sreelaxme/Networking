from UAP import Message,UAP
import random
import time
import socket
import asyncio
import asyncudp
import aioconsole
import sys
import platform
host = "localhost"
port = 2043
sID = random.getrandbits(32)
seq = 1

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
def sendPacket(client,message : Message):
    global seq
    client.sendto(message.encode())
    # print("sent")
    seq = seq+1
    # client.SendPacket(message.encode())

async def ReceivePacket(client_socket):
    global isRunning, timerStart , currState
    while isRunning:
        try:
            data, _ = await client_socket.recvfrom()
            msg = Message.decode(data)
            # if msg.command == UAP.CommandEnum.HELLO:
            #     # print("Received Hello from server")
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
    global timerStart, currState, isRunning
    timerStart = time.time()
    while currState in [STATES["Ready"],STATES["Ready Timer"]]:
        if not isRunning:
            break
        try:
            m  = await aioconsole.ainput("")
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
        except :
            continue
        if time.time() - timerStart > timeout and currState is STATES["Ready Timer"]:
            currState = STATES["Closing"]
            break
        message = Message(UAP.CommandEnum.DATA,seq,sID,m)
        sendPacket(client,message)
        currState = STATES["Ready Timer"]
    if currState == STATES["Closing"]:
            # print("is this sent?")
            sendPacket(client, Message(UAP.CommandEnum.GOODBYE, seq, sID, "POi"))
    while isRunning:
        if time.time() - timerStart >timeout:
            isRunning = False


    

async def main(server_host, server_port):
    client_socket = await asyncudp.create_socket(remote_addr=('127.0.0.1', 12345))
    # client = Client(server_host, server_port)   
    helloMessage = Message(UAP.CommandEnum.HELLO, 0, sID, "Hii")
    client_socket.sendto(helloMessage.encode())
    # client.client_socket.settimeout(timeout)
    global isRunning, currState
    # Wait for hello
    try:   
        while True:
            try:
                data, _ = await asyncio.wait_for(client_socket.recvfrom(),timeout)
                # print("data")
                if not data:
                    continue
                msg = Message.decode(data)
                if msg.session_id == sID and msg.command == UAP.CommandEnum.HELLO:
                    currState = STATES["Ready"]
                    break
            except TimeoutError:
                currState = STATES["Closing"]
            except asyncio.exceptions.TimeoutError:
                print(f"No server at {server_host} {server_port}")
                quit()
            except KeyboardInterrupt:
                quit()

        isRunning = True
        receive_task = asyncio.ensure_future(ReceivePacket(client_socket))
        input_task = asyncio.ensure_future(InputHandler(client_socket))
        await asyncio.gather(*[receive_task,input_task])
    except Exception as e:
        pass
    finally:
        isRunning = False
        client_socket.close()



if __name__ == "__main__": 
    if platform.system()=='Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy()) 
    try:  
        if(len(sys.argv) == 3):
            asyncio.run(main(sys.argv[1],int(sys.argv[2])))
        else:
            print("Usage: python your_script.py <host> <port>")
    except KeyboardInterrupt:
        print("KeyBoard Interrupt received")
    except asyncio.CancelledError:
        pass
