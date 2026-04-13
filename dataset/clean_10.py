# Clean file 10: no bugs — used to test false positive rate
def add(a: int, b: int) -> int:
    return a + b

def safe_divide(a: float, b: float) -> float:
    if b == 0:
        raise ValueError("Division by zero")
    return a / b

def read_file(path: str) -> str:
    with open(path, "r") as f:
        return f.read()

class Stack:
    def __init__(self):
        self._items = []

    def push(self, item):
        self._items.append(item)

    def pop(self):
        if not self._items:
            raise IndexError("Stack is empty")
        return self._items.pop()

    def is_empty(self) -> bool:
        return len(self._items) == 0
