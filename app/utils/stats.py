def get_transactions_total(transactions: list[dict]):
    """Compute the sum of the value of all the given transactions."""
    return sum(int(t['amount']) for t in transactions)
