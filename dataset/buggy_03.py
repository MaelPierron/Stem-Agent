# Bug file 03: potential division by zero, type confusion
def average(numbers):
    total = sum(numbers)
    return total / len(numbers)  # ZeroDivisionError if empty list

def format_name(first, last):
    return first + " " + last  # TypeError if None passed

def compute_ratio(a, b):
    return a / b  # no zero check

class Counter:
    count = 0  # class-level mutable shared across instances

    def increment(self):
        self.count += 1
