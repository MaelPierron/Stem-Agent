# Bug file 04: shadowing builtins, == None instead of is None, == True
def check_status(value):
    if value == None:  # should use 'is None'
        return "empty"
    if value == True:  # should use 'is True' or just truthiness
        return "active"
    return "unknown"

def process_list(list, dict, str):  # shadows built-in names
    result = []
    for item in list:
        result.append(str(item))
    return result

def find_item(items, target):
    for i in range(len(items)):  # should use enumerate
        if items[i] == target:
            return i
    return -1
