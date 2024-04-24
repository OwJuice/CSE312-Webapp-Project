import hashlib
import base64

class Parsed_Frame:
    def __init__(self):
        self.fin_bit = None
        self.opcode = None
        self.payload_length = None
        self.payload = None

def compute_accept(websocket_key):
    guid = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
    concatenated_key = websocket_key + guid
    encoded_key = concatenated_key.encode()
    sha1_hash = hashlib.sha1(encoded_key).digest()
    accept_key = base64.b64encode(sha1_hash).decode()

    return accept_key

# parse_ws_frame takes a frame, which is just an array of bytes, as a parameter
def parse_ws_frame(frame):
    output_object = Parsed_Frame()

    # NOTE: Result of bitwise operations in python get converted to ints
    #Get Fin bit by masking with 0b10000000
    output_object.fin_bit = (frame[0] & 0b10000000) >> 7 #This shifts right by 7 and only gets the fin bit.
    
    #Get opcode by masking with 0b00001111
    output_object.opcode = (frame[0] & 0b00001111)

    #Get masking bit
    masking_bit = (frame[1] & 0b10000000) >> 7
    #Get payload length
    payload_len = frame[1] & 0b01111111

    #Determine the payload length mode
    if payload_len == 126:
        #NOTE: Reminder that splicing is [<Inclusive index>, <exclusive index>]
        output_object.payload_length = int.from_bytes(frame[2:4], byteorder="big")
        frame = frame[4:] #Only leaves masking key and/or payload data
    elif payload_len == 127:
        output_object.payload_length = int.from_bytes(frame[2:10], byteorder="big")
        frame = frame[10:] #Only leaves masking key and/or payload data
    else:
        output_object.payload_length = payload_len
        frame = frame[2:] #Only leaves masking key and/or payload data

    if masking_bit == 1:
        mask_key = frame[:4]
        frame = frame[4:]
    
    output_object.payload = frame #This payload data is still masked. We must XOR with the mask to unmask

    if masking_bit == 1:
        for index in range(len(output_object.payload)):
            mask_index = index % 4
            output_object.payload[index] = bytes(output_object.payload[index] ^ mask_key[mask_index])

    print("---PRINTING THE TYPES---")
    print("finbit", type(output_object.fin_bit))
    print("opcode", type(output_object.opcode))
    print("payload len", type(output_object.payload_length))
    print("payload", type(output_object.payload))
    return output_object

def generate_ws_frame(payload):
    payload_len = len(payload)
    frame = bytearray()
    frame.append(0b10000001)
    if payload_len < 126:
        frame.append(payload_len)
        frame.extend(payload)
    elif payload_len < 65536:
        frame.append(126)
        frame.extend(payload_len.to_bytes(2, byteorder="big"))
        frame.extend(payload)
    else:
        frame.append(127)
        frame.extend(payload_len.to_bytes(8, byteorder="big"))
        frame.extend(payload)

    return bytes(frame)