import struct

class UAP:

    class CommandEnum:
        HELLO = 0
        DATA = 1
        ALIVE = 2
        GOODBYE = 3

    MAGIC_NUMBER = 0xC461 

    def __init__(self, magic, version, command, sequence, session, message):
        self.magic = magic
        self.version = version
        self.command = command
        self.sequence = sequence
        self.session = session
        self.message = message

    def encode(self):
        header = struct.pack('>QIBIQ', self.magic, self.version, self.command, self.sequence, self.session)
        return header + self.message.encode()

    @classmethod
    def decode(cls, data):
        print(data)
        if len(data) != 25:
            raise ValueError("Input data must have 25 bytes to unpack.")
        
        header_bytes = data[:24]
        message_bytes = data[24:]
        
        magic, version, command, sequence, session = struct.unpack('>QIBIQ', header_bytes)
        
        message = message_bytes.decode('utf-8')
        
        return cls(magic, version, command, sequence, session, message)


class Message:

    def __init__(self, command, sequence_no, session_id, message):
        self.command = command
        self.sequence_no = sequence_no
        self.session_id = session_id
        self.message = message
        self.version = 1
        self.magic = UAP.MAGIC_NUMBER

    def encode(self):
        header = struct.pack('>QIBIQ', self.magic, self.version, self.command, self.sequence_no, self.session_id)
        return header + self.message.encode()

    @classmethod
    def decode(cls, data):
        if len(data) < 25:
            raise ValueError("Input data must have 25 bytes to unpack.")
        
        header_bytes = data[:25]
        message_bytes = data[25:]
        
        magic, version, command, sequence, session = struct.unpack('>QIBIQ', header_bytes)
        
        message = message_bytes.decode('utf-8')
        
        return cls(command, sequence, session, message)
    
    def __str__(self):
        return (f"| {self.magic} | {self.version} | {self.command} | {self.sequence_no} | {self.session_id} | {self.message} |")

if __name__ == "__main__":
    m = Message(1, 0, 0, "Hello world")

    print("Input Message:")
    print(m)

    m_enc = m.encode()

    m_dec = Message.decode(m_enc)

    print("Output Message:")
    print(m_dec)
