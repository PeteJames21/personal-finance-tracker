from collections import defaultdict
from app import db


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


def get_summary_stats(username, profile, from_=None, to=None):
    """Get transaction summaries for the given user profile."""
    incomes = db.get_transactions(username, profile, category='incomes',
                                  from_=from_, to=to)
    expenses = db.get_transactions(username, profile, category='expenses',
                                   from_=from_, to=to)

    top_incomes = get_totals_by_subcategories(incomes, n=5)
    top_expenses = get_totals_by_subcategories(expenses, n=5)
    total_income = get_transactions_total(incomes)
    total_expense = get_transactions_total(expenses)
    net_income = total_income - total_expense

    return {
        'top_incomes': top_incomes,
        'top_expenses': top_expenses,
        'total_income': total_income,
        'total_expense': total_expense,
        'net_income': net_income
    }
