from collections import defaultdict


def get_transactions_total(transactions: list[dict]):
    """Compute the sum of the value of all the given transactions."""
    return sum(int(t['amount']) for t in transactions)


def get_totals_by_subcategories(transactions: list[dict]) -> list[tuple[str, int]]:
    """
    Compute totals by subcategory.

    Sample output: [('food', 100), ('electricity', 40), ...]
    """
    totals = defaultdict(int)
    for t in transactions:
        totals[t['subcategory']] += int(t['amount'])

    # Sort results by amount in descending order
    return sorted(list(totals.items()), key=lambda x: x[1], reverse=True)
