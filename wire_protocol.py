import json
FORMAT = "utf-8"
INT_SIZE = 4


def packing(data):
    """
    Packs the data into a format that can be sent over the network.
    Format:
    - version: [1 byte] ("1" or "2")
    - type: [2 bytes] ("00" to "16")
    - info: [dictionary bytes from packing_dictionary or string bytes]
    """
    # Version and type are fixed length, no need for length prefixes
    version_byte = data["version"].encode(FORMAT)
    type_bytes = data["type"].encode(FORMAT)
    
    # Pack the info dictionary
    info_bytes = packing_dictionary(data["info"]) # if isinstance(data["info"], dict) else data["info"].encode(FORMAT)
    print("Info bytes: ", info_bytes)
    
    ret_data = version_byte + type_bytes + info_bytes
    return ret_data


def packing_dictionary(data): 
    packed_data = b""
    for key, value in data.items():
        # Convert key and value to bytes
        key_bytes = str(key).encode(FORMAT)
        value_bytes = str(value).encode(FORMAT)
        
        # Get lengths of key and value
        key_length = len(key_bytes)
        value_length = len(value_bytes)
        
        # Pack key_length, key, value_length, value into bytes
        packed_data += key_length.to_bytes(INT_SIZE, "big")  # 4-byte integer for key length
        packed_data += key_bytes                     # Key bytes
        packed_data += value_length.to_bytes(INT_SIZE, "big")  # 4-byte integer for value length
        packed_data += value_bytes                  # Value bytes
    
    return packed_data


def unpacking(data):
    """
    Unpacks the data from the network format.
    Format matches packing function above.
    """
    decoded_data = {}
    pos = 0
    
    # Get version (1 byte)
    decoded_data["version"] = data[0:1].decode(FORMAT)
    
    # Get type (2 bytes)
    decoded_data["type"] = data[1:3].decode(FORMAT)
    
    # Get remaining data for info
    remaining = data[3:]

    decoded_data["info"] = unpacking_dictionary(remaining)
    

    return decoded_data

def unpacking_dictionary(data): 
    # Try to unpack as dictionary format
    info_dict = {}
    dict_pos = 0
    
    while dict_pos < len(data):
        # Read key length (4 bytes)
        key_len = int.from_bytes(data[dict_pos:dict_pos+INT_SIZE], "big")
        dict_pos += INT_SIZE
        
        # Read key
        key = data[dict_pos:dict_pos+key_len].decode(FORMAT)
        dict_pos += key_len
        
        # Read value length (4 bytes)
        value_len = int.from_bytes(data[dict_pos:dict_pos+INT_SIZE], "big")
        dict_pos += INT_SIZE
        
        # Read value
        value = data[dict_pos:dict_pos+value_len].decode(FORMAT)
        dict_pos += value_len
        
        info_dict[key] = value

    return info_dict
            
    