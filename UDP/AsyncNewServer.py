import asyncio
import asyncudp
from UAP import Message, UAP
from Server import Session, send_goodbye_to_active_sessions
import sys

class AsyncServer:

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.loop = asyncio.get_event_loop()
        self.server_socket = None
        self.sessions = {}

    async def send_hello(self, session):
        hello_message = Message(
            command=UAP.CommandEnum.HELLO,
            sequence_no=0,
            session_id=session.session_id,
            message="Hello from server"
        )
        await self.send_message(hello_message, session.client_address)

    async def send_alive(self, session):
        alive_message = Message(
            command=UAP.CommandEnum.ALIVE,
            sequence_no=0,
            session_id=session.session_id,
            message="ALIVE"
        )
        await self.send_message(alive_message, session.client_address)

    async def send_message(self, message, addr):
        encoded_message = message.encode()
        self.server_socket.sendto(encoded_message, addr)

   
    # async def handle_packet(self, data, client_address):
    #     try:
    #         received_message = Message.decode(data)
    #         session_id = received_message.session_id

    #         if received_message.command == UAP.CommandEnum.HELLO:
    #             if session_id not in self.sessions:
    #                 new_session = Session(session_id, client_address, self.server_socket, self.sessions)
    #                 if not new_session.is_hello(received_message):
    #                     return
    #                 self.sessions[session_id] = new_session
    #             else:
    #                 self.sessions[session_id].close_session()
    #                 return

    #             self.sessions[session_id].update_activity_time()
    #             await self.send_hello(self.sessions[session_id])
    #             print("Replies sent")

    #         elif received_message.command == UAP.CommandEnum.DATA:
    #             if session_id in self.sessions:
    #                 await self.sessions[session_id].messages.put(received_message)
    #         elif received_message.command == UAP.CommandEnum.GOODBYE:
    #             session_id = received_message.session_id
    #             if session_id in self.sessions:
    #                 await self.send_goodbye(self.sessions[session_id])
    #                 self.terminate_session(session_id)
    #     except KeyboardInterrupt:
    #         print("handle_packet got keyboard interrupt")
    #     except asyncio.exceptions.CancelledError:
    #         pass

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
            self.send_goodbye(session)
            session.close_session()

    async def start_server(self):
        port = self.port
        host = self.host
        server_address = (host, port)
        self.server_socket = await asyncudp.create_socket(local_addr=server_address)  # Initialize the server_socket
        print(f"Waiting on host {host} and port {port}")

        try:
            while True:
                data, client_address = await self.server_socket.recvfrom()  # Receive data and client address
                if not data:
                    continue
                await self.handle_packet(data, client_address)
        except asyncio.CancelledError:
            pass
        except KeyboardInterrupt:
            pass
        except ValueError as e:
            print(f"Invalid message received from {client_address}: {e}")
        finally:
            send_goodbye_to_active_sessions(self.sessions.copy(), self.server_socket)  # Pass the server_socket
            self.server_socket.close()

if __name__ == "__main__":
    port = 12345
    server = AsyncServer('localhost', port)
    asyncio.run(server.start_server())
