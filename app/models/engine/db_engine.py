import json
import uuid
from ..user import User
from datetime import datetime
from typing import Union


class DBEngine:
    __file = 'db.json'

    def __init__(self):
        """Initialize the database connection."""
        self.db = {}
        try:
            with open(self.__file, encoding='utf-8') as f:
                self.db = json.load(f)

        except FileNotFoundError:
            # Create the file if it does not exist
            with open(self.__file, 'w', encoding='utf-8') as f:
                json.dump(self.db, f)

    def get_transactions(self, username, profile, account=None, category=None,
                         subcategory=None, limit=None,
                         from_: Union[datetime, str, None] = None,
                         to: Union[datetime, str, None] = None) -> list[dict]:
        """
        Fetch transactions using the specified criteria.

        If @category is not specified, all transactions under the specified
        account are returned. If @account is not specified, all transactions
        from all accounts are returned.
        """
        transactions = []
        # todo: refactor to eliminate code duplication
        # todo: filter by subcategory
        if not account:
            for account in self.db[username]['profiles'][profile]['accounts'].values():
                if category:
                    transactions.extend(account['transactions'][category])
                else:
                    transactions.extend(account['transactions']['incomes'])
                    transactions.extend(account['transactions']['expenses'])
                    transactions.extend(account['transactions']['transfers'])
        else:
            account = self.db[username]['profiles'][profile]['accounts'][account]
            if category:
                transactions.extend(account['transactions'][category])
            else:
                transactions.extend(account['transactions']['incomes'])
                transactions.extend(account['transactions']['expenses'])
                transactions.extend(account['transactions']['transfers'])

        # Filter results by subcategory
        if subcategory:
            transactions = list(filter(
                lambda t: t.get('subcategory') == subcategory,
                transactions
            ))
        # Filter results by time
        if not from_ and not to:
            # Return all values if no datetime filters are specified
            return transactions[:limit]
        if to and not from_:
            raise ValueError("'from' cannot be None if 'to' is specified")
        if not to:
            # Set upper datime bound to the current date
            to = datetime.now()
        # Convert to datetime if str values are passed
        if type(from_) is str:
            from_ = datetime.fromisoformat(from_)
        if type(to) is str:
            to = datetime.fromisoformat(to)
        # Apply the filter
        transactions_filtered = []
        for t in transactions:
            dt = datetime.fromisoformat(t['time'])
            if ((dt - from_).days >= 0) and ((to - dt).days >= 0):
                transactions_filtered.append(t)

        return transactions_filtered[:limit]

    def add_user(self, user: User):
        """Add a new user to the database."""
        if user.username in self.db:
            raise ValueError(f"The username '{user.username}' already exists")
        if not user.id:
            user.id = len(self.db.keys()) + 1
        self.db[user.username] = {
            'email': user.email,
            'password': user.password,
            'id': user.id,
            'default_profile': '',
            'profiles': {},
        }
        self.add_profile(user.username, 'personal')

    def add_profile(self, username, profile, description='', default=False):
        """
        Add a new profile under the specified user.

        @default is used to specify whether to set this profile as the
        default one. If no other profile exist under this user, @profile
        will be set as the default one.
        """
        if len(self.get_profiles(username)) == 0:
            default = True
        if profile in self.db[username]['profiles']:
            raise ValueError(f"The profile '{profile}' already exists")
        self.db[username]['profiles'][profile] = {
            'description': description,
            'accounts': {}
        }
        if default:
            self.db[username]['default_profile'] = profile
            return

    def add_account(self, username, profile, account,
                    balance=0, description=''):
        """Add an account under the profile of a specific username."""
        if account in self.db[username]['profiles'][profile]['accounts']:
            raise ValueError(f"The account '{account}' already exists"
                             f"under the profile '{username}.{profile}'")
        self.db[username]['profiles'][profile]['accounts'][account] = {
            'balance': balance,
            'description': description,
            'transactions': {
                'incomes': [],
                'expenses': [],
                'transfers': []
            }
        }

    def add_transaction(self, username, profile, category, **trans_details):
        # Options for @category: incomes, expenses, transfers
        # Generate a unique ID for the transaction
        trans_id = str(uuid.uuid4())
        trans_details['id'] = trans_id
        trans_details['user_id'] = username
        trans_details['category'] = category
        # Set date to the current one if none is specified
        if not trans_details.get('time'):
            trans_details['time'] = datetime.now().strftime("%Y-%m-%d")

        account_debited = trans_details.get('account_debited')
        account_credited = trans_details.get('account_credited')
        amount = trans_details['amount']
        # TODO: wrap the conditionals using try/except and provide helpful error msg
        if account_debited:
            account_debited = self.db[username]['profiles'][profile]['accounts'][account_debited]
        if account_credited:
            account_credited = self.db[username]['profiles'][profile]['accounts'][account_credited]

        if category == 'incomes':
            if account_credited:
                raise IntegrityError("The transaction field 'account_credited'"
                                     " is not valid for expense-related transactions")
            if not account_debited:
                raise IntegrityError("The transaction field 'account_debited' must"
                                     " be specified for income transactions")
            # Debit the account and add the transaction record
            account_debited['balance'] += amount
            account_debited['transactions']['incomes'].append(trans_details)

        elif category == 'expenses':
            if account_debited:
                raise IntegrityError("The transaction field 'account_debited'"
                                     " is not valid for income transactions")
            # Credit the account and add the transaction record
            # Abort the transaction if it would cause a negative balance
            if account_credited['balance'] - amount < 0:
                raise IntegrityError('Transaction results in negative balance')
            account_credited['balance'] -= amount
            account_credited['transactions']['expenses'].append(trans_details)

        elif category == 'transfers':
            if not all([account_credited, account_debited]):
                raise IntegrityError(
                    "Both the transaction fields 'account_credited' and "
                    "'account_debited' must be specified for transfers")
            if account_credited['balance'] - amount < 0:
                raise IntegrityError('Transaction results in negative balance')
            account_credited['balance'] -= amount
            account_debited['balance'] += amount
            account_debited['transactions']['transfers'].append(trans_details)
            account_credited['transactions']['transfers'].append(trans_details)

        else:
            raise ValueError(f"The category '{category}' does not exist")

    def rollback_transaction(self, trans_id):
        """Undo a transaction"""
        # TODO: implement
        raise NotImplementedError

    def save(self):
        """Save changes to database."""
        with open(self.__file, 'w', encoding='utf-8') as f:
            json.dump(self.db, f, indent=4)

    def get_account_names(self, username, profile) -> list[str]:
        """Get a list of account names under the given profile."""
        return list(self.db[username]['profiles'][profile]['accounts'].keys())

    def get_all_account_balances(self, username, profile) -> dict:
        """
        Get the balances of all accounts.

        Returns a dict in which the keys are account names and the values are
        the corresponding account balances.
        """
        balances = {}
        accounts = self.db[username]['profiles'][profile]['accounts']
        for account in accounts:
            balances[account] = accounts[account]['balance']

        return balances

    def get_account_balance(self, username, profile, account) -> int:
        """Get the balance of the specified account."""
        return self.db[username]['profiles'][profile]['accounts'][account]['balance']

    def get_profiles(self, username) -> list[str]:
        """Get a list of profiles registered under the given user."""
        return list(self.db[username]['profiles'].keys())

    def get_total_balance(self, username, profile):
        """Return sum of balances from all accounts in the given profile."""
        balances = self.get_all_account_balances(username, profile)
        if not balances:
            return 0
        return sum(balances.values())

    def get_user_by_username(self, username):
        """
        Get a user by the username.

        :return: A User instance or None if @username is not found
        """
        if username not in self.db:
            return None
        return User(
            username=username,
            user_id=self.db[username]['id'],
            password=self.db[username]['password'],
            email=self.db[username]['email'],
            default_profile=self.db[username]['default_profile']
        )

    def get_all_usernames(self):
        """Get a list of all usernames in the database."""
        return list(self.db.keys())

    def get_user_by_id(self, id_: str):
        """
        Get a user by their ID.

        :return: A User instance or None if @id_ is not found
        """
        raise NotImplementedError

    def set_default_profile(self, username, profile):
        """
        Set the default profile for the given username.

        The profile must already exist, otherwise an IntegrityError is raised.
        """
        if profile not in self.get_profiles(username):
            raise IntegrityError("Profile does not exist")
        self.db[username]['default_profile'] = profile

    def reload(self):
        """Reload data from storage."""
        with open(self.__file, encoding='utf-8') as f:
            self.db = json.load(f)


class IntegrityError(Exception):
    """Raised if an operation violates the integrity of the data."""
    pass
