import asyncio
import socket
from UAP import Message, UAP

class AsyncServer:

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.loop = asyncio.get_event_loop()
        self.server_socket = None
        self.sessions = {}

    async def send_hello(self, session_id, addr):
        # Send a HELLO message
        hello_message = Message(
            command=UAP.CommandEnum.HELLO,
            sequence_no=0,
            session_id=session_id,
            message="Hello from server"
        )
        await self.send_message(hello_message, addr)

    async def send_alive(self, session_id, addr):
        # Send an ALIVE message
        alive_message = Message(
            command=UAP.CommandEnum.ALIVE,
            sequence_no=0,
            session_id=session_id,
            message="ALIVE"
        )
        await self.send_message(alive_message, addr)

    async def send_message(self, message, addr):
        # Send a message to the client
        encoded_message = message.encode()
        self.server_socket.sendto(encoded_message, addr)

    async def handle_packet(self, data, addr):
        try:
            msg = Message.decode(data)
        except ValueError as e:
            print(f"Invalid message received from {addr}: {e}")
            return

        session_id = msg.session_id

        if session_id not in self.sessions:
            # Create a new session when a new session ID is encountered
            if msg.command != UAP.CommandEnum.HELLO:
                # Terminate session if the initial message is not HELLO
                self.terminate_session(session_id)
                return
            self.sessions[session_id] = {
                "expected_sequence": 0,
                "last_received_sequence": -1,
                "timer": None,
                "client_address": addr  # Store the client's address for later use
            }

        session = self.sessions[session_id]

        if msg.command == UAP.CommandEnum.HELLO:
            await self.send_hello(session_id, addr)
            self.set_timer(session_id)

        elif msg.command == UAP.CommandEnum.DATA:
            sequence_number = msg.sequence_no
            if sequence_number == session["expected_sequence"]:
                print(f"Received DATA from session {session_id}: {msg.message}")
                await self.send_alive(session_id, addr)
                session["expected_sequence"] += 1
                self.cancel_timer(session_id)
            elif sequence_number > session["expected_sequence"]:
                for missing_sequence in range(session["expected_sequence"], sequence_number):
                    print(f"Lost packet in session {session_id}: {missing_sequence}")
                session["expected_sequence"] = sequence_number + 1
            else:
                print(f"Duplicate packet in session {session_id}: {sequence_number}")

        elif msg.command == UAP.CommandEnum.GOODBYE:
            self.terminate_session(session_id)

    def set_timer(self, session_id):
        if session_id in self.sessions:
            session = self.sessions[session_id]
            session["timer"] = self.loop.call_later(10, self.terminate_session, session_id)

    def cancel_timer(self, session_id):
        if session_id in self.sessions:
            session = self.sessions[session_id]
            if session["timer"] is not None:
                session["timer"].cancel()
                session["timer"] = None

    def terminate_session(self, session_id):
        if session_id in self.sessions:
            session = self.sessions.pop(session_id)
            self.cancel_timer(session_id)
            goodbye_message = Message(UAP.CommandEnum.GOODBYE, 0, session_id, "Goodbye from server")
            self.send_message(goodbye_message, session["client_address"])

    async def start_server(self):
        self.server_socket = await asyncio.create_datagram_endpoint(
            lambda: asyncio.DatagramProtocol(),
            local_addr=(self.host, self.port)
        )

        while True:
            data, addr = await self.loop.sock_recv(self.server_socket[0], 1024)
            if not data:
                continue
            await self.handle_packet(data, addr)

    def run(self):
        try:
            self.loop.run_until_complete(self.start_server())
        except KeyboardInterrupt:
            pass
        finally:
            if self.server_socket:
                self.server_socket.close()

if __name__ == "__main__":
    server = AsyncServer('localhost', 12345)
    server.run()
