FORMAT = "utf-8"


def packing(data):
    ret_data = (
        data["version"].encode(FORMAT)
        + data["type"].encode(FORMAT)
        + data["info"].encode(FORMAT)
    )
    return ret_data


def unpacking(data):
    data = data.decode(FORMAT)
    decoded_data = {}
    decoded_data["version"] = data[0]
    decoded_data["type"] = data[1:3]
    info_str = data[3:]
    
    # Parse the info string if it contains key-value pairs
    if "=" in info_str:
        info_dict = {}
        pairs = info_str.split("&")
        for pair in pairs:
            key, value = pair.split("=")
            info_dict[key] = value
        decoded_data["info"] = info_dict
    else:
        decoded_data["info"] = info_str
    
    return decoded_data
