# Bug file 05: logic errors, off-by-one, wrong boolean operators
def is_valid_age(age):
    if age > 0 and age < 18 or age > 120:  # missing parentheses, logic unclear
        return False
    return True

def get_last_elements(lst, n):
    return lst[len(lst) - n: len(lst) - 1]  # off-by-one: misses last element

def clamp(value, min_val, max_val):
    if value < min_val:
        value = min_val
    if value > max_val:  # should be elif
        value = max_val
    return value

def has_duplicates(lst):
    seen = []
    for item in lst:
        if item in seen:
            return True
        seen.append(item)
    return False  # correct logic but O(n^2), seen should be a set
