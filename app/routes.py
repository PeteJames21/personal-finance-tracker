"""Handles the urls that the module supports"""
from app import app, db
from flask import render_template, flash, redirect, url_for
from app.forms import LoginForm, RegistrationForm, TransactionForm, AddAccountForm
from flask_login import login_user, logout_user, login_required, current_user
from .models.user import User
from werkzeug.security import generate_password_hash, check_password_hash
from .utils.stats import get_summary_stats
from .utils.flask_utils import get_current_profile


@app.route('/')
@app.route('/index')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    return render_template('index.html', title='Welcome Page')


@app.route('/home')
@login_required
def home():
    db.reload()
    profile = get_current_profile()
    stats = {}
    if profile:
        stats = get_summary_stats(current_user.username, profile)
    return render_template('home.html', title='Home',
                           user=current_user, stats=stats)


@app.route('/login', methods=['POST', 'GET'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = db.get_user_by_username(form.username.data)
        if user and check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect(url_for('home'))
        else:
            flash('Login unsuccessful. Please check username and password')
    return render_template('login.html', title='Sign In', form=form)


@app.route('/register', methods=['POST', 'GET'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        user = User(username=form.username.data, email=form.email.data,
                    password=hashed_password)
        db.add_user(user)
        db.save()
        flash(f'Account has been created for {form.username.data}. '
              f'You can now login!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html',
                           title='Register', form=form)


@app.route('/balances')
def balances():
    user = {
        'username': 'Pete',
        'account': 'Personal',
        'account_categories': {
            'income': {'salary': 5000, 'bonus': 1000},
            'expense': {'rent': 1200, 'utilities': 200, 'food': 400}
        }
    }

    # Calculate sums
    total_income = sum(user['account_categories']['income'].values())
    total_expenses = sum(user['account_categories']['expense'].values())
    balance = total_income - total_expenses

    return render_template(
        'balances.html',
        title='Balances',
        user=user,
        total_income=total_income,
        total_expenses=total_expenses,
        balance=balance
    )


@app.route('/account', methods=['POST', 'GET'])
def account():
    """Serves page with summary"""
    return render_template('home.html')


@app.route('/income', methods=['POST', 'GET'])
def income():
    """Serves page with summary"""
    return render_template('income.html')


@app.route('/expense', methods=['POST', 'GET'])
def expense():
    """Serves page with summary"""
    return render_template('expense.html')


@app.route('/logout')
def logout():
    flash('You have been logged out!')
    logout_user()
    return redirect(url_for('index'))

# Route for adding a transaction
@app.route('/add_transaction', methods=['GET', 'POST'])
@login_required
def add_transaction():
    username = current_user.username
    user_profile = db.get_profiles(username)[0]
    form = TransactionForm()
    if form.validate_on_submit():
        username = current_user.username
        profile = user_profile
        category = form.category.data
        amount = form.amount.data
        account_debited = form.account_debited.data
        account_credited = form.account_credited.data
        subcategory = form.subcategory.data
        date = form.date.data.strftime("%Y-%m-%d")

        # Create a Transaction object
        transaction_details = {
            'amount': amount,
            'account_debited': account_debited,
            'account_credited': account_credited,
            'subcategory' : subcategory,
            'time': date,
            # Include other transaction details here
        }

        try:
            db.add_transaction(username, profile, category, **transaction_details)
            db.save()
            flash('Transaction added successfully', 'success')
            return redirect(url_for('home'))  # Redirect to the dashboard or another page
        except ValueError as e:
            error_message = str(e)
            flash(error_message, 'error')

    return render_template('add_transaction.html', form=form)

# Route for adding a an account
@app.route('/add_account', methods=['GET', 'POST'])
@login_required
def add_account():
    username = current_user.username
    user_profile = db.get_profiles(username)[0]
    form = AddAccountForm()
    if form.validate_on_submit():
        username = current_user.username
        profile = user_profile
        account = form.account.data
        balance = form.balance.data
        description = form.description.data

        try:
            db.add_account(username, profile, account, balance, description)
            db.save()
            flash('Account added successfully', 'success')
            return redirect(url_for('home'))
        except ValueError as e:
            error_message = str(e)
            flash(error_message, 'error')
    return render_template('add_account.html', form=form)
