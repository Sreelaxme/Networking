import asyncio
import asyncudp
from UAP import Message, UAP
from Server import Session, send_goodbye_to_active_sessions
import sys
import time

TIMEOUT = 10
SESSIONS = {}
def PrintMessage(msg : Message, 
                 alternativeMessage = None,
                 alternativeSequence = None):
        if alternativeMessage:
            msg.message = alternativeMessage
        if alternativeSequence:
            msg.seq = alternativeSequence
        print(f"{hex(msg.session_id)} [{msg.sequence_no}] {msg.message}")
class Session:
    def __init__(self, session_id, client_address, server_socket, active_sessions):
        self.session_id = session_id
        self.client_address = client_address
        self.last_activity_time = time.time()
        self.expected_sequence_number = 1
        self.server_socket = server_socket  # Store the server socket
        self.active_sessions = active_sessions  # Store the active sessions dictionary

        self.messages = asyncio.Queue() # Queue of packets for this session
        self.task = None

    def is_hello(self, message : Message) -> bool:
        return message.command == UAP.CommandEnum.HELLO and message.sID == self.session_id

    def update_activity_time(self):
        self.last_activity_time = time.time()

    def is_timedout(self):
        return time.time() - self.last_activity_time > TIMEOUT

    async def send_hello(self):
        hello_message = Message(
            command=UAP.CommandEnum.HELLO,
            sequence_no=0,
            session_id=self.session_id,
            message="Hello from server"
        )
        await self.send_message(hello_message, self.client_address)

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

    
    
    def terminate_session(self):
        goodbye_message = Message(UAP.CommandEnum.GOODBYE, 0, self.session_id, "GOODBYE")
        encoded_goodbye_message = goodbye_message.encode()
        self.server_socket.sendto(encoded_goodbye_message, self.client_address)
        
 
    def process_packet(self, received_message):
        # print(received_message)
        # Extract the sequence number from the received message
        received_sequence_number = received_message.sequence_no

        if received_sequence_number == self.expected_sequence_number:
            # Process the packet as expected
            # print(f"Received packet with sequence number {received_sequence_number}: {received_message.message}")
            PrintMessage(received_message)
            self.expected_sequence_number += 1  # Update the expected sequence number
        elif received_sequence_number < self.expected_sequence_number:
            # Handle out-of-order packet (protocol error)
            # print(f"Received out-of-order packet with sequence number {received_sequence_number}.")
            PrintMessage(received_message, "Message out of order")
            #self.close_session()
        else:
            # Handle missing packets
            for missing_sequence_number in range(self.expected_sequence_number, received_sequence_number):
                # print(f"Lost packet with sequence number {missing_sequence_number}")
                PrintMessage(received_message, 
                             alternativeMessage="Packet Lost",
                             alternativeSequence=missing_sequence_number)
            # Update the expected sequence number
            self.expected_sequence_number = received_sequence_number + 1
async def session_handler(server_socket, session_id):

    # Send a reply HELLO message back to the client
    session = SESSIONS[session_id]
    reply_message = Message(UAP.CommandEnum.HELLO, 0, session_id, "Reply HELLO")
    encoded_reply_message = reply_message.encode()
    server_socket.sendto(encoded_reply_message, session.client_address)
    # print("Replies sent")
    PrintMessage(reply_message, "Session Started")

    try:
        while True:
                # print('*')

                # Fetch session data from shared dictionary
                session = SESSIONS[session_id]

                client_address = session.client_address
                try:
                    # print("GETTING")
                    received_message = await asyncio.wait_for(session.messages.get(), TIMEOUT)
                except asyncio.exceptions.TimeoutError:
                    PrintMessage(Message(   
                        0,
                        session.expected_sequence_number,
                        session_id,
                        "Closing session due to timeout"
                    ))

                    session.terminate_session()
                except Exception as e:
                    raise e
                    
                #print(f"Received data from {client_address}: {received_message}")

                if received_message.session_id != session_id:
                    raise RuntimeError("Recieved wrong session packet")
                
                if received_message.command == UAP.CommandEnum.HELLO:
                    raise RuntimeError("Recieved hello packet in task")

                elif received_message.command == UAP.CommandEnum.DATA:

                    # Update the session's last activity time
                    session.update_activity_time()
                    session.process_packet(received_message)
                    # Send an ALIVE message in response to the DATA message
                    alive_message = Message(UAP.CommandEnum.ALIVE, 0, session_id, "ALIVE")
                    encoded_alive_message = alive_message.encode()
                    server_socket.sendto(encoded_alive_message, client_address)
                
                elif received_message.command == UAP.CommandEnum.GOODBYE:
                    #print("\necievd goodbye\n")

                    PrintMessage(received_message, "Closing session")
                    session.close_session()
                    break
    except asyncio.exceptions.CancelledError:
        pass



async def handle_packet(server_socket):
    try:
        while True:
            data, client_address = await server_socket.recvfrom()
            msg = Message.decode(data)
            if msg.command == UAP.CommandEnum.HELLO:
                session_id = msg.session_id
                
                if session_id not in SESSIONS:
                    new_session = Session(session_id, client_address, server_socket, SESSIONS)  # Pass server_socket and active_sessions
                    
                    SESSIONS[session_id] = new_session
                else:
                    # remove from the dictionary 
                    print(SESSIONS)
                    del SESSIONS[session_id]
                    return

                # Update the session's last activity time
                SESSIONS[session_id].update_activity_time()

                # Send a reply HELLO message back to the client
                # reply_message = Message(UAP.CommandEnum.HELLO, 0, session_id, "Reply HELLO")
                # encoded_reply_message = reply_message.encode()
                # self.server_socket.sendto(encoded_reply_message, client_address)
                await new_session.send_hello()
                new_session.task = asyncio.ensure_future(session_handler(server_socket, session_id))
                print("Replies sent")

            
            elif msg.command == UAP.CommandEnum.DATA:
                session_id = msg.session_id
                if session_id not in SESSIONS:
                    # Terminate the session if the DATA message is received without a HELLO
                    return

                # Update the session's last activity time
                SESSIONS[session_id].update_activity_time()

                # Print the DATA message's data payload to stdout
                # print(f"Received DATA from session {session_id}: {msg.message}")
                await SESSIONS[session_id].messages.put(msg)
                # Send an ALIVE message in response to the DATA message
                alive_message = Message(UAP.CommandEnum.ALIVE, 0, session_id, "ALIVE")
                encoded_alive_message = alive_message.encode()
                server_socket.sendto(encoded_alive_message, client_address)
            elif msg.command == UAP.CommandEnum.GOODBYE:
                    #print("\necievd goodbye\n")
                    session_id = msg.session_id
                    if session_id not in SESSIONS:
                        return 
                    # Send a GOODBYE message to the client
                    goodbye_message = Message(UAP.CommandEnum.GOODBYE, 0, session_id, "GOODBYE")
                    encoded_goodbye_message = goodbye_message.encode()
                    server_socket.sendto(encoded_goodbye_message, client_address)
            
                    # Remove the session from active_sessions
                    del SESSIONS[session_id]
    except KeyboardInterrupt:
        print("recieve handler got keyboard interrupt")
    except asyncio.exceptions.CancelledError:
        pass
    except asyncudp.ClosedError:
        pass

async def handle_keyboard_input(server_socket):
    while True:
        user_input = await asyncio.to_thread(input)  # Run input() in a separate thread
        if user_input.lower() == 'q':
            # Terminate the server gracefully
            print("Terminating the server...")
            break

async def main(port, host='0.0.0.0'):
    # server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_address = (host, port)
    # server_socket.bind(server_address)

    # Create asynchronous socket
    server_socket = await asyncudp.create_socket(local_addr=server_address)
    print(f"Waiting on host {host} and port {port}")


    # Define each task
    recieve_task = asyncio.ensure_future(handle_packet(server_socket))
    input_task = asyncio.ensure_future(handle_keyboard_input(server_socket))

    # Await on all parallel tasks
    _, pending = await asyncio.wait([input_task, recieve_task], return_when=asyncio.FIRST_COMPLETED)

    # Cancel whichever tasks have not ended yet
    for task in pending:
        task.cancel()

    # Send GOODBYE message to all active sessions
    send_goodbye_to_active_sessions(SESSIONS.copy(),server_socket)
    # Close the socket and clean up
    server_socket.close()
    return
        


if __name__ == "__main__":
    import sys
    if len(sys.argv) == 1:
        print("Usage: AsyncUAPServer.py port [host]")
    elif len(sys.argv) == 2:
        asyncio.run(main(int(sys.argv[1])))
    else:
        asyncio.run(main(int(sys.argv[1]), sys.argv[2]))