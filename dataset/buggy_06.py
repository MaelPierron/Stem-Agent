# Bug file 06: resource leaks, no context managers
def read_file(path):
    f = open(path, "r")  # never closed
    content = f.read()
    return content

def write_log(path, message):
    f = open(path, "a")
    f.write(message + "\n")
    # f.close() missing — resource leak

def load_json(path):
    import json
    file = open(path)
    data = json.load(file)
    return data  # file never closed
