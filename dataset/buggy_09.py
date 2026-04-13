# Bug file 09: class-level shared state, missing __init__, bad __eq__
class BankAccount:
    balance = 0  # shared across ALL instances — should be instance variable
    transactions = []  # shared mutable list

    def deposit(self, amount):
        self.balance += amount
        self.transactions.append(("deposit", amount))

    def withdraw(self, amount):
        self.balance -= amount  # no check for negative balance


class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y  # no type check, crashes if other is None

    def distance(self):
        return (self.x**2 + self.y**2) ** 0.5  # should be to another point, not origin only
