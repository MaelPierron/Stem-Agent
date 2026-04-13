# Bug file 08: missing return values, inconsistent return types
def get_discount(user_type):
    if user_type == "premium":
        return 0.2
    elif user_type == "student":
        return 0.1
    # missing else: returns None implicitly

def find_user(users, user_id):
    for user in users:
        if user["id"] == user_id:
            return user
    # no explicit return None — implicit

def validate(value):
    if isinstance(value, int):
        return True
    if isinstance(value, str):
        return value.strip() != ""
    # returns None for other types — inconsistent
