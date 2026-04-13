# Bug file 02: mutable default argument, broad except, bare except
def append_item(item, lst=[]):
    lst.append(item)
    return lst

def read_config(path):
    try:
        with open(path) as f:
            return f.read()
    except:
        pass

def process(data, results=[]):
    for item in data:
        results.append(item * 2)
    return results
