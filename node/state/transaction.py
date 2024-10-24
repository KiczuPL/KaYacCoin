class Transaction:
    def __init__(self, sender, receiver, amount, timestamp, signature):
        self.sender = sender
        self.receiver = receiver
        self.amount = amount
        self.timestamp = timestamp
        self.signature = signature

