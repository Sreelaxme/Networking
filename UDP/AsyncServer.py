
import asyncio
import socket

import asyncudp
from UAP import Message, UAP
from Server import Session , send_goodbye_to_active_sessions # Import the Session class
import sys

class AsyncServer:

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.loop = asyncio.get_event_loop()
        self.server_socket = None
        self.sessions = {}

    async def send_hello(self, session, addr):
        # Send a HELLO message
        hello_message = Message(
            command=UAP.CommandEnum.HELLO,
            sequence_no=0,
            session_id=session.session_id,
            message="Hello from server"
        )
        await self.send_message(hello_message, addr)

    async def send_alive(self, session, addr):
        # Send an ALIVE message
        alive_message = Message(
            command=UAP.CommandEnum.ALIVE,
            sequence_no=0,
            session_id=session.session_id,
            message="ALIVE"
        )
        await self.send_message(alive_message, addr)

    async def send_message(self, message, addr):
        # Send a message to the client
        encoded_message = message.encode()
        self.server_socket.sendto(encoded_message, addr)

    async def handle_packet(self,data, client_address):
        
        msg = Message.decode(data)
        if msg.command == UAP.CommandEnum.HELLO:
            session_id = msg.session_id
            
            if session_id not in self.sessions:
                new_session = Session(session_id, client_address, self.server_socket, self.sessions)  # Pass server_socket and active_sessions
                
                self.sessions[session_id] = new_session
            else:
                # remove from the dictionary 
                print(self.sessions)
                del self.sessions[session_id]
                return

            # Update the session's last activity time
            self.sessions[session_id].update_activity_time()

            # Send a reply HELLO message back to the client
            # reply_message = Message(UAP.CommandEnum.HELLO, 0, session_id, "Reply HELLO")
            # encoded_reply_message = reply_message.encode()
            # self.server_socket.sendto(encoded_reply_message, client_address)
            await self.send_hello(new_session, client_address)
            print("Replies sent")

        
        elif msg.command == UAP.CommandEnum.DATA:
            session_id = msg.session_id
            if session_id not in self.sessions:
                # Terminate the session if the DATA message is received without a HELLO
                return

            # Update the session's last activity time
            self.sessions[session_id].update_activity_time()

            # Print the DATA message's data payload to stdout
            print(f"Received DATA from session {session_id}: {msg.message}")

            self.sessions[session_id].process_packet(msg)
            # Send an ALIVE message in response to the DATA message
            alive_message = Message(UAP.CommandEnum.ALIVE, 0, session_id, "ALIVE")
            encoded_alive_message = alive_message.encode()
            self.server_socket.sendto(encoded_alive_message, client_address)
        elif msg.command == UAP.CommandEnum.GOODBYE:
                #print("\necievd goodbye\n")
                session_id = msg.session_id
                if session_id not in self.sessions:
                    # Terminate the session if the DATA message is received without a HELLO
                    return 
                # Send a GOODBYE message to the client
                goodbye_message = Message(UAP.CommandEnum.GOODBYE, 0, session_id, "GOODBYE")
                encoded_goodbye_message = goodbye_message.encode()
                self.server_socket.sendto(encoded_goodbye_message, client_address)
        
                # Remove the session from active_sessions
                del self.sessions[session_id]
        

        
    def terminate_session(self, session_id):
        if session_id in self.sessions:
            session = self.sessions.pop(session_id)
            session.close_session()
            
    async def start_server(self):
        port = self.port
        host = self.host
        server_address = (host, port)
        # server_socket.bind(server_address)

        # Create asynchronous socket
        server_socket = await asyncudp.create_socket(local_addr=server_address)
        print(f"Waiting on host {host} and port {port}")

        try:
            while True:
                data, client_address = await server_socket.recvfrom( 1024)
                print(data)
                if not data:
                    print("data kittiyilla")
                    continue
                print("came here?")
                await AsyncServer.handle_packet(data, client_address)
        except asyncio.CancelledError:
            print("some error")
            pass
        except KeyboardInterrupt:
            print("Keyboard Interrupt")
        except ValueError as e:
            print(f"Invalid message received from {client_address}: {e}")
        finally:
            send_goodbye_to_active_sessions(AsyncServer.sessions.copy(), server_socket)
            server_socket.close()
    # async def start_server(self):
    #     self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    #     self.server_socket.bind((self.host, self.port))
    #     try:

    #         while True:
    #             data, client_address = await self.loop.run_in_executor(None, self.server_socket.recvfrom, 1024)
    #             if not data:
    #                 continue
    #             print("here")
    #             await self.handle_packet(data, client_address)
    #     except KeyboardInterrupt :
    #         print("Keyboard Interrupt")
    #     except ValueError as e:
    #         print(f"Invalid message received from {client_address}: {e}")
    #         return
    #     finally:
    #         send_goodbye_to_active_sessions(self.sessions.copy(),self.server_socket)
    #         self.server_socket.close()
    
    

    def run(self):
        try:
            self.loop.run_until_complete(self.start_server())
        except KeyboardInterrupt:
            pass
        finally:
            if self.server_socket:
                self.server_socket.close()

# if __name__ == "__main__":
#     server = AsyncServer('localhost', 12345)
#     server.run()

async def a_input():
        return await asyncio.get_event_loop().run_in_executor(
            None, sys.stdin.readline
        )

async def input_handler(concurrent_task : asyncio.Task,server):
    try:
        while True:
            # Wait for input and close server if input is q
            stdin = await a_input()
            if stdin.strip() == "q":
                break
    except KeyboardInterrupt:
        print("Input handler got keyboard interrupt")
    except asyncio.exceptions.CancelledError:
        pass
    finally:
        # cancel the reciever task
        concurrent_task.cancel()
        # cancel the sessions tasks
        send_goodbye_to_active_sessions(server.sessions.copy(), server.server_socket)
# async def main(port, host='0.0.0.0'):
#     # server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#     server_address = (host, port)
#     # server_socket.bind(server_address)

#     # Create asynchronous socket
#     server_socket = await asyncudp.create_socket(local_addr=server_address)
    
#     print(f"Waiting on host {host} and port {port}")
    
#     data, client_address = await server_socket.recvfrom()
#     # Define each task
#     recieve_task = asyncio.ensure_future(handle_packet(data,client_address))
#     input_task = asyncio.ensure_future(input_handler(recieve_task))

#     # Await on all parallel tasks
#     _, pending = await asyncio.wait([input_task, recieve_task], return_when=asyncio.FIRST_COMPLETED)

#     # Cancel whichever tasks have not ended yet
#     for task in pending:
#         task.cancel()

#     # Send GOODBYE message to all active sessions
#     send_goodbye_to_active_sessions(AsyncServer.sessions.copy())
#     # Close the socket and clean up
#     server_socket.close()
#     return

async def main(port, host='0.0.0.0'):
    server = AsyncServer(host,port)
    # Create a task for the server
    server_task = asyncio.ensure_future(server.run())

    # Create a task for input handling
    input_task = asyncio.ensure_future(input_handler(server_task,server))

    # Wait for either task to complete
    _, pending = await asyncio.wait([input_task, server_task], return_when=asyncio.FIRST_COMPLETED)

    # Cancel any remaining tasks
    for task in pending:
        task.cancel()

    # Wait for all tasks to finish
    await asyncio.gather(*pending)

if __name__ == "__main__":
    port = 12345
    asyncio.run(main(port))
