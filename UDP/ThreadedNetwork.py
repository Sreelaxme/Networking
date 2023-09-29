from Network import Client
import socket
import threading

class ThreadedClient(Client):
    def Run(self):
        try:
            # Start a function to receive packets in a background thread
            receiver_thread = threading.Thread(target=self.ReceivePackets)
            receiver_thread.daemon = True
            receiver_thread.start()

            while True:
                try:
                    message = input()
                    isEOF = False
                except EOFError:
                    message = ""
                    isEOF = True

                if not self.running.is_set():
                    break

                packet_thread = threading.Thread(target=self.HandlePacket, args=(message, isEOF))
                packet_thread.start()

        except KeyboardInterrupt:
            pass
        finally:
            self.Exit("Exiting")

    def Exit(self, reason):
        print("Reason:", reason)
        self.running.clear()
        super().Exit()
