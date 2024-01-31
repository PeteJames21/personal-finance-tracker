from collections import defaultdict


def get_transactions_total(transactions: list[dict]):
    """Compute the sum of the value of all the given transactions."""
    return sum(int(t['amount']) for t in transactions)


def get_totals_by_subcategories(transactions: list[dict],
                                n: int = None) -> list[tuple[str, int]]:
    """
    Compute totals by subcategory and return the top n subcategories.

    Transactions with no subcategory will be grouped under 'Uncategorized'.
    Sample output: [('Food', 100), ('Electricity', 40), ...]
    """
    if not transactions:
        return []
    totals = defaultdict(int)
    for t in transactions:
        # Transactions with no subcategory will be put under 'uncategorized'
        if not t.get('subcategory'):
            totals['Uncategorized'] += int(t['amount'])
        else:
            totals[t['subcategory']] += int(t['amount'])

    # Sort results by amount in descending order
    totals = list(totals.items())
    if n and n > 0:
        totals = totals[:n]
    return sorted(totals, key=lambda x: x[1], reverse=True)
