# Bug file 01: unused variables, unreachable code
def calculate_discount(price, discount):
    unused_var = "this is never used"
    tax = 0.2
    result = price - (price * discount / 100)
    return result
    print("Discount applied")  # unreachable code

def get_user(user_id):
    debug_flag = True  # unused
    temp = []          # unused
    return {"id": user_id, "name": "Alice"}
