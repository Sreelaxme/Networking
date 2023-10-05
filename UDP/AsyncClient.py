from UAP import Message, UAP
from Network import Client
import asyncio
import random
import time

host = "localhost"
port = 12345
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

async def sendPacket(client, message):
    global seq
    client.SendPacket(message.encode())
    seq += 1

async def ReceivePacket(client):
    global isRunning, timerStart, currState
    while isRunning:
        try:
            data, _ = await client.client_socket.recvfrom(1024)
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
        except asyncio.TimeoutError:
            pass

async def main():
    global isRunning, timerStart, currState

    # Initialize the client
    client = Client(host, port)

    helloMessage = Message(UAP.CommandEnum.HELLO, seq, sID, "Hii")
    await sendPacket(client, helloMessage)
    client.client_socket.settimeout(timeout)

    # Wait for hello
    try:
        while True:
            try:
                data, _ = await client.client_socket.recvfrom(1024)

                if not data:
                    continue
                msg = Message.decode(data)
                if msg.session_id == sID and msg.command == UAP.CommandEnum.HELLO:
                    currState = STATES["Ready"]
                    break
            except asyncio.TimeoutError:
                currState = STATES["Closing"]

        isRunning = True
        recieverTask = asyncio.create_task(ReceivePacket(client))

        timerStart = time.time()
        while currState in [STATES["Ready"], STATES["Ready Timer"]]:
            try:
                m = input()
            except EOFError:
                currState = STATES["Closing"]
                break
            except KeyboardInterrupt:
                currState = STATES["Closing"]
                break

            if time.time() - timerStart > timeout and currState is STATES["Ready Timer"]:
                currState = STATES["Closing"]
                break

            if not isRunning:
                break

            message = Message(UAP.CommandEnum.DATA, seq, sID, m)
            await sendPacket(client, message)
            currState = STATES["Ready Timer"]

        if currState == STATES["Closing"]:
            await sendPacket(client, Message(UAP.CommandEnum.GOODBYE, seq, sID, "POi"))

        while isRunning:
            if time.time() - timerStart > timeout:
                isRunning = False

    except Exception as e:
        print(e)
    finally:
        isRunning = False
        client.Exit()

    # Close the client
    client.Exit()

if __name__ == "__main__":
    asyncio.run(main())
