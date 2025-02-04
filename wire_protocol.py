FORMAT = 'utf-8'
def packing(data): 
    ret_data = data["version"].encode(FORMAT) + data["type"].encode(FORMAT) + data["info"].encode(FORMAT)
    return ret_data 

def unpacking(data): 
    data = data.decode(FORMAT)
    decoded_data = {}
    decoded_data["version"] = data[0]
    decoded_data["type"] = data[1:3]
    decoded_data["info"] = data[3:]
    return decoded_data