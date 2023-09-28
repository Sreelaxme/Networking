class UAP:

    class CommandEnum:
        HELLO = 0
        DATA = 1
        ALIVE = 2
        GOODBYE = 3

    def __init__(self, magic, version, command, sequence, session, message):
        self.magic = magic
        self.version = version
        self.command = command
        self.sequence = sequence
        self.session = session
        self.message = message

    def encode(self):
        header = (
            (self.magic << 96) |
            (self.version << 68) |
            (self.command << 40) |
            (self.sequence << 8) |
            self.session
        )
        return header.to_bytes(24, 'big') + self.message.encode()

    @classmethod
    def decode(cls, data):
        header_bytes = data[:24]
        message_bytes = data[24:]
        
        header = int.from_bytes(header_bytes, 'big')
        
        magic = header >> 96
        version = (header >> 68) & 0xFF
        command = (header >> 40) & 0xFF
        sequence = (header >> 8) & 0xFFFFFFFF
        session = header & 0xFFFFFFFF
        
        message = message_bytes.decode('utf-8')
        
        return cls(magic, version, command, sequence, session, message)

    def __str__(self):
        return (
            f"Magic: {self.magic}\n"
            f"Version: {self.version}\n"
            f"Command: {self.command}\n"
            f"Sequence: {self.sequence}\n"
            f"Session: {self.session}\n"
            f"Message: {self.message}\n"
        )

class Message:

    def __init__(self, command, sequence_no, session_id, message):
        self.command = command
        self.sequence_no = sequence_no
        self.session_id = session_id
        self.message = message
        self.version = 1
        self.magic = UAP.MAGIC_NUMBER

    def __str__(self):
        return (
            f"| Magic: {self.magic} "
            f"| Version: {self.version} "
            f"| Command: {self.command} "
            f"| Sequence: {self.sequence_no} "
            f"| Session: {self.session_id} "
            f"| Message: {self.message} |"
        )

    def __repr__(self):
        return str(self)

    @staticmethod
    def encode_message(command, sequence_no, session_id, message):
        header_num = UAP.MAGIC_NUMBER << UAP.SHIFTS["MAGIC"]
        header_num += 1 << UAP.SHIFTS["VERSION"]
        header_num += command << UAP.SHIFTS["COMMAND"]
        header_num += sequence_no << UAP.SHIFTS["SEQUENCE"]
        header_num += session_id << UAP.SHIFTS["SESSION"]

        return header_num.to_bytes(24, 'big') + message.encode()

    def encode(self):
        return self.encode_message(self.command, self.sequence_no, self.session_id, self.message)

    @classmethod
    def decode_message(cls, message_bytes):
        message_num = int.from_bytes(message_bytes, "big")

        magic = UAP.MagicBits(message_num)
        version = UAP.VersionBits(message_num)

        if magic != UAP.MAGIC_NUMBER:
            raise ValueError(f"Magic number does not match. Obtained magic number: {magic}")

        if version != 1:  # This is a v1 agent
            raise ValueError(f"Version mismatch. Obtained version: {version}")

        command = UAP.CommandBits(message_num)
        sequence_no = UAP.SequenceBits(message_num)
        session_id = UAP.SessionBits(message_num)
        message_str = (UAP.MessageBits(message_num).to_bytes(message_num.bit_length() // 4 + 1, "big")).decode("utf-8")

        return cls(command, sequence_no, session_id, message_str)

    @classmethod
    def decode(cls, message_bytes):
        return cls.decode_message(message_bytes)


if __name__ == "__main__":

    m = Message(1, 0, 0, "Hello world")

    print("Input Message:")
    print(m)

    m_enc = m.EncodeMessage()

    m_dec = Message.DecodeMessage(m_enc)

    print("Output Message:")
    print(m_dec)
