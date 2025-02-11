import json
FORMAT = "utf-8"
INT_SIZE = 4


def packing(data):
    """
    Packs the data into a format that can be sent over the network.
    Format:
    - version: [1 byte] ("1" or "2")
    - type: [2 bytes] ("00" to "16")
    - info: [list/dictionary bytes from packing_data]
    """
    version_byte = data["version"].encode(FORMAT)
    type_bytes = data["type"].encode(FORMAT)
    
    # Pack the info field, which can be a dictionary, list, or string
    info_bytes = packing_data(data["info"])
    
    ret_data = version_byte + type_bytes + info_bytes
    return ret_data


def packing_data(data):
    """
    Packs different data types:
    - If data is a list: packs as a list of dictionaries
    - If data is a dictionary: packs as a single dictionary
    - If data is a string: packs as a string
    """
    # if isinstance(data, list):
    # Pack list length first
    packed_data = len(data).to_bytes(INT_SIZE, "big")
    # Pack each dictionary in the list
    for item in data:
        item_bytes = packing_dictionary(item)
        # Pack the length of the dictionary bytes first
        packed_data += len(item_bytes).to_bytes(INT_SIZE, "big")
        packed_data += item_bytes
    return packed_data
    # elif isinstance(data, dict):
    #     return packing_dictionary(data)
    # else:
    #     # For string data, pack with length prefix
    #     str_bytes = str(data).encode(FORMAT)
    #     return len(str_bytes).to_bytes(INT_SIZE, "big") + str_bytes


def packing_dictionary(data): 
    """Packs a single dictionary into bytes"""
    packed_data = b""
    for key, value in data.items():
        # Convert key and value to bytes
        key_bytes = str(key).encode(FORMAT)
        value_bytes = str(value).encode(FORMAT)
        
        # Pack key_length, key, value_length, value
        packed_data += len(key_bytes).to_bytes(INT_SIZE, "big")
        packed_data += key_bytes
        packed_data += len(value_bytes).to_bytes(INT_SIZE, "big")
        packed_data += value_bytes
    
    return packed_data


def unpacking(data):
    """
    Unpacks the data from the network format.
    Format matches packing function above.
    """
    decoded_data = {}
    
    # Get version (1 byte)
    decoded_data["version"] = data[0:1].decode(FORMAT)
    
    # Get type (2 bytes)
    decoded_data["type"] = data[1:3].decode(FORMAT)
    
    # Get remaining data for info
    remaining = data[3:]
    
    # Try to unpack the info field
    decoded_data["info"] = unpacking_data(remaining)
    
    return decoded_data

def unpacking_data(data):
    """
    Unpacks data based on its format:
    - If it starts with a list length: unpacks as list of dictionaries
    - Otherwise: tries to unpack as dictionary
    """
    if not data:
        return None
        
    
    # Try to read as a list first
    list_length = int.from_bytes(data[0:INT_SIZE], "big")
    pos = INT_SIZE
    result = []
    
    # Read each dictionary in the list
    for _ in range(list_length):
        # Read dictionary length
        dict_length = int.from_bytes(data[pos:pos+INT_SIZE], "big")
        pos += INT_SIZE
        # Read and unpack dictionary
        dict_data = data[pos:pos+dict_length]
        result.append(unpacking_dictionary(dict_data))
        pos += dict_length
        
    return result
    # except:
    #     # If not a list, try as dictionary
    #     try:
    #         return unpacking_dictionary(data)
    #     except:
    #         # If not a dictionary, try as string
    #         try:
    #             str_length = int.from_bytes(data[0:INT_SIZE], "big")
    #             return data[INT_SIZE:INT_SIZE+str_length].decode(FORMAT)
    #         except:
    #             return None

def unpacking_dictionary(data): 
    """Unpacks a single dictionary from bytes"""
    info_dict = {}
    dict_pos = 0
    
    while dict_pos < len(data):
        # Read key length
        key_len = int.from_bytes(data[dict_pos:dict_pos+INT_SIZE], "big")
        dict_pos += INT_SIZE
        
        # Read key
        key = data[dict_pos:dict_pos+key_len].decode(FORMAT)
        dict_pos += key_len
        
        # Read value length
        value_len = int.from_bytes(data[dict_pos:dict_pos+INT_SIZE], "big")
        dict_pos += INT_SIZE
        
        # Read value
        value = data[dict_pos:dict_pos+value_len].decode(FORMAT)
        dict_pos += value_len
        
        info_dict[key] = value

    return info_dict
            
    