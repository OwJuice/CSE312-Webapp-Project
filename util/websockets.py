import hashlib
import base64
import json

class Parsed_Frame:
    def __init__(self):
        self.fin_bit = 0
        self.opcode = 0
        self.payload_length = 0
        self.payload = bytearray()

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
    
    output_object.payload = bytearray(frame) #This payload data is still masked. We must XOR with the mask to unmask

    if masking_bit == 1:
        for index in range(len(output_object.payload)):
            mask_index = index % 4
            output_object.payload[index] = output_object.payload[index] ^ mask_key[mask_index]

    # print("---PRINTING THE TYPES---")
    # print("finbit", type(output_object.fin_bit))
    # print("opcode", type(output_object.opcode))
    # print("payload len", type(output_object.payload_length))
    # print("payload", type(output_object.payload))
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

#---extract_payload_message---#
#  -Objective: A helper function that takes a given payload and extracts only the message from it. It ignores the messageTypes.
#  -Parameters: A bytearray of the payload for a frame
#  -Return: message in string format
def extract_payload_message(payload):
    print("97-------PAYLOAD IN EXTRACT PAYLOAD MESSAGE:", payload)
    json_string = payload.decode()
    print("98-------Received JSON string:", json_string)
    json_data = json.loads(json_string) #Our data is only from one frame
    message = json_data.get('message', '')
    return message

def extract_payload_type(payload):
    json_string = payload.decode()
    json_data = json.loads(json_string) #Our data is only from one frame
    messageType = json_data.get('messageType', '')
    return messageType

# recieve_bytes takes a socket as a parameter to recv bytes from the socket
def recieve_bytes(socket):
    recieved_data = bytearray(socket.request.recv(2))
    #Get opcode by masking with 0b00001111
    opcode = (recieved_data[0] & 0b00001111)
    payload_len = (recieved_data[1] & 0b01111111)
    masking_bit = (recieved_data[1] & 0b10000000) >> 7

    # Counter variable for the amount of extra bytes we need
    extra_bytes = 0

    # Don't return any bytes if we get a disconnect opcode of 8
    if opcode == 8:
        return None
    else:
        # Check how many more bytes we need to receive depending on payload length
        if payload_len == 126:
            recieved_data.extend(bytearray(socket.request.recv(2)))
            payload_length = int.from_bytes(recieved_data[2:4], byteorder="big")
            extra_bytes += payload_length
        elif payload_len == 127:
            recieved_data.extend(bytearray(socket.request.recv(8)))
            payload_length = int.from_bytes(recieved_data[2:10], byteorder="big")
            extra_bytes += payload_length
        else:
            payload_length = payload_len
            extra_bytes += payload_length
    
        # Add on 4 bytes if we have a mask
        if masking_bit == 1:
            recieved_data.extend(bytearray(socket.request.recv(4)))

        # Keep reading data until we have extra bytes
        while extra_bytes != 0:
            recieved_data.extend(bytearray(socket.request.recv(1)))
            extra_bytes -= 1

        return recieved_data