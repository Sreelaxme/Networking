import socket
import UAP
import threading
import sys
import time
import queue
clients = {}
server_socket = None
timeout = 10
def StartServer(port, timeout=5):
    global server_socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(("localhost",int(port)))
    print(f"Waiting on port {port}")

def finish_all_clients():
    # Create a goodbye message
    for session_id in clients.keys():
        message = UAP.Message(UAP.UAP.CommandEnum.GOODBYE,0,session_id,"GOODBYE")
        server_socket.sendto(message.encode(), clients[session_id]['client_address'])

def send_goodbye(session_id):
    message = UAP.Message(UAP.UAP.CommandEnum.GOODBYE,0,session_id,"GOODBYE")
    server_socket.sendto(message.encode(), clients[session_id]['client_address'])
    
    
def thread_handler(session_id):
    # When thread is created, first we will have to send a hello message back
    message = UAP.Message(UAP.UAP.CommandEnum.HELLO,0,session_id,"HELLO")
    clients[session_id]['sequence_no'] = 1
    server_socket.sendto(message.encode(), clients[session_id]['client_address'])
    print(f"{session_id} [0] Session created")
    while True:
        if (clients[session_id]['timer']-time.time()) > timeout:
            send_goodbye(session_id)
            print(f"{session_id} Session Closed : Timeout")
            break
        try:
            msg = clients[session_id]['message_queue'].get(block=False)
        except:
            continue
        if((msg.sequence_no)+1 == clients[session_id]['sequence_no']):
            print(f"{session_id} [{clients[session_id]['sequence_no']-1}] Duplicate packet!")
        elif(msg.sequence_no > clients[session_id]['sequence_no']):
            while(clients[session_id]['sequence_no'] != msg.sequence_no):
                print(f"{session_id} [{clients[session_id]['sequence_no']}] Lost packet!")
                clients[session_id]['sequence_no'] = clients[session_id]['sequence_no']+1
        elif(msg.sequence_no < clients[session_id]['sequence_no']):
            send_goodbye(session_id)
            break
        
        if msg.command == UAP.UAP.CommandEnum.GOODBYE:
            send_goodbye(session_id)
            print(f"{session_id} Session Closed")
            break
        elif msg.command == UAP.UAP.CommandEnum.DATA :
            print(f"{session_id} [{msg.sequence_no}] {msg.message}")
            message = UAP.Message(UAP.UAP.CommandEnum.ALIVE,0,session_id,"ALIVE")
            server_socket.sendto(message.encode(), clients[session_id]['client_address'])
            clients[session_id]['sequence_no'] = clients[session_id]['sequence_no']+1
            
def ReceivePacket():
    try:
        while True:
            data, client_address = server_socket.recvfrom(1024)
            if not data:
                continue
            msg = UAP.Message.decode(data)
            if(msg.magic!=50273 or msg.version!=1):
                continue
            if(msg.session_id not in clients.keys()):
                if(msg.command == UAP.UAP.CommandEnum.HELLO and msg.sequence_no == 0):
                    clients[msg.session_id] = {'thread':None,'message_queue':queue.Queue(),'client_address':client_address}
                    clients[msg.session_id]['thread'] = threading.Thread(target=thread_handler,args=(msg.session_id,))
                    clients[msg.session_id]['thread'].start()
                    clients[msg.session_id]['timer'] = time.time()
            elif(msg.command in [UAP.UAP.CommandEnum.DATA, UAP.UAP.CommandEnum.GOODBYE]):
                clients[msg.session_id]['message_queue'].put(msg)
                clients[msg.session_id]['timer'] = time.time()

    except Exception as e:
        print(e)
    


if __name__ == "__main__": 
    if len(sys.argv) != 2:
        print("Requires command line input of the form \"./server <port>\"")
    port = sys.argv[1]
    StartServer(port)
    receive_thread = threading.Thread(target = ReceivePacket)
    receive_thread.daemon = True
    receive_thread.start()
    try:
        while True:
            command_line_input = input()
            if command_line_input == "q":
                print("Server quitting")
                quit()
    except KeyboardInterrupt:
        print("Server is quitting : keyboard interrupt.")
        quit()
    except Exception as e:
        print(e)
    # finally:
    # Send GOODBYE message to all active sessions
    finish_all_clients()
    print(server_socket)
    server_socket.close()
