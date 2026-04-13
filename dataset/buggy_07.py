# Bug file 07: % formatting with wrong types, implicit string concat
def build_query(table, limit):
    return "SELECT * FROM %s LIMIT %s" % (table, limit)  # SQL injection risk, %s for int

def greet(name, age):
    msg = "Hello " + name + ", you are " + age + " years old"  # TypeError if age is int
    return msg

LONG_STRING = ("This is part one "
               "this is part two "
               "this is part three")  # implicit concat OK but can hide missing comma in lists

def log_error(code, msg):
    print("Error [" + str(code) + "]: " + msg)  # verbose, should use f-string
