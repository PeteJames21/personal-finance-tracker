"""
Create a demo user in the db with sample data.
"""
import random
from datetime import datetime, timedelta
from app import db

ACCOUNTS = ['cash', 'pay pal', 'bank']
INCOME_SOURCES = ['Turing', 'Upwork', 'Business', 'misc']
EXPENSES = ['food', 'travel', 'entertainment', 'shopping', 'pet']
D1 = datetime(2020, 1, 1)
D2 = datetime(2024, 2, 15)
N_TRANSACTIONS = 1000  # The number of transactions to generate
USERNAME = 'demo'
PROFILE = 'personal'


def random_date(start_date: datetime, end_date: datetime) -> str:
    """
    Generate a random timestamp between start_year and end_year.

    Args:
        start_date (int): Start year for the timestamp.
        end_date (int): End year for the timestamp.

    Returns:
        datetime: Random timestamp str in the format %Y-%m-%d.
    """
    time_difference = end_date - start_date
    random_days = random.randint(0, time_difference.days)

    random_timestamp = start_date + timedelta(days=random_days)

    return random_timestamp.strftime('%Y-%m-%d')


def generate_expense(category):
    if category == 'food':
        return random.randint(100, 1000)
    elif category in ('travel', 'entertainment'):
        return random.randint(1000, 5000)
    elif category == 'shopping':
        return random.randint(300, 3000)
    elif category == 'pet':
        return random.randint(500, 1000)


def generate_income():
    return random.randint(1000, 5000)


def random_transaction(category, start_date, end_date):
    account = random.choice(ACCOUNTS)
    date = random_date(start_date, end_date)
    if category == 'incomes':
        subcategory = random.choices(INCOME_SOURCES, weights=[0.1, 0.4, 0.3, 0.2])[0]
        amount = generate_income()
    elif category == 'expenses':
        subcategory = random.choices(EXPENSES, weights=[0.3, 0.2, 0.2, 0.2, 0.1])[0]
        amount = generate_expense(subcategory)
    else:
        raise ValueError(f'Unknown category: "{category}"')

    t = {
        'amount': amount,
        'subcategory': subcategory,
        'time': date,
    }
    if category == 'incomes':
        t['account_debited'] = account
    elif category == 'expenses':
        t['account_credited'] = account
    else:
        raise Exception('Invalid Category')

    return t


def add_transactions():
    """Insert random transactions into the specified profile."""
    categories = ['incomes', 'expenses']
    for i in range(N_TRANSACTIONS):
        category = random.choices(categories, weights=[0.6, 0.4])[0]
        transaction = random_transaction(category, D1, D2)
        db.add_transaction(USERNAME, PROFILE, category, **transaction)


if __name__ == '__main__':
    # Add profile
    if PROFILE not in db.get_profiles(USERNAME):
        db.add_profile(USERNAME, PROFILE, default=True)
    # Add accounts
    for account in ACCOUNTS:
        if account not in db.get_accounts(USERNAME, PROFILE):
            db.add_account(USERNAME, PROFILE, account, balance=100000)
    # Generate transactions and add them to the database
    add_transactions()
    db.save()
    print("Transactions successfully added to demo account")
