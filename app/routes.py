"""Handles the urls that the module supports"""
from app import app, db
from flask import render_template, flash, redirect, url_for, request, session
from app.forms import LoginForm, RegistrationForm, TransactionForm, AddAccountForm, AddProfileForm
from flask_login import login_user, logout_user, login_required, current_user
from .models.user import User
from werkzeug.security import generate_password_hash, check_password_hash
from .utils.stats import get_summary_stats, get_summary_graphs, count_charts, get_income_plots, get_expense_plots
from .utils.flask_utils import get_current_profile, get_request_args
from .models.engine.db_engine import IntegrityError


@app.route('/')
@app.route('/index')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    return render_template('index.html', title='Welcome Page')


@app.route('/home', methods=['GET', 'POST'])
@login_required
def home():
    all_profiles = db.get_profiles(current_user.username)
    data = get_request_args(request)
    stats = get_summary_stats(current_user.username, data['profile'],
                              from_=data['start_date'], to=data['end_date'])
    data.update(stats)
    # Generate visualizations.
    # Format: charts = { 'chart_name': ('title', 'base64-encoded chart'), ... }
    charts = get_summary_graphs(
        username=current_user.username,
        profile=data['profile'],
        top_incomes=data['top_incomes'],
        top_expenses=data['top_expenses'],
        from_=data['start_date'],
        to=data['end_date']
    )
    n_charts = count_charts(charts)  # The number of non-empty charts
    data['charts'] = charts
    data['chart_count'] = n_charts
    return render_template('home.html', title='Home',
                           user=current_user,
                           profiles=all_profiles,  # Needed by JS.
                           data=data)


@app.route('/login', methods=['POST', 'GET'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = db.get_user_by_username(form.username.data)
        if user and check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect(url_for('home'))
        else:
            flash('Login unsuccessful. Please check username'
                  ' and password', category='error')
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
@login_required
def balances():
    data = get_request_args(request)
    profiles = db.get_profiles(current_user.username)  # Needed by JS
    profile = data['profile']
    balances = db.get_all_account_balances(current_user.username, profile)
    data['balances'] = balances
    return render_template('balances.html',
                           data=data, profiles=profiles)


@app.route('/income', methods=['POST', 'GET'])
@login_required
def income():
    """Serves incomes page"""
    all_profiles = db.get_profiles(current_user.username)
    data = get_request_args(request)
    stats = get_summary_stats(current_user.username, data['profile'],
                              from_=data['start_date'], to=data['end_date'])
    data.update(stats)
    charts = get_income_plots(current_user.username, data['profile'],
                              data['start_date'], data['end_date'])
    data['charts'] = charts
    data['chart_count'] = count_charts(charts)
    return render_template('income.html', title='Incomes',
                           user=current_user,
                           profiles=all_profiles,  # Needed by JS.
                           data=data)


@app.route('/expense', methods=['POST', 'GET'])
@login_required
def expense():
    """Serves expenses page"""
    all_profiles = db.get_profiles(current_user.username)
    data = get_request_args(request)
    stats = get_summary_stats(current_user.username, data['profile'],
                              from_=data['start_date'], to=data['end_date'])
    data.update(stats)
    charts = get_expense_plots(current_user.username, data['profile'],
                               data['start_date'], data['end_date'])
    data['charts'] = charts
    data['chart_count'] = count_charts(charts)
    return render_template('expense.html', title='Expenses',
                           user=current_user,
                           profiles=all_profiles,  # Needed by JS.
                           data=data)



@app.route('/logout')
def logout():
    # We don't want to remember these session variables the next time
    # the user logs back in after deliberately logging out.
    session.pop('start_date', None)
    session.pop('end_date', None)

    logout_user()
    return redirect(url_for('index'))

# Route for adding a transaction
@app.route('/add_transaction', methods=['GET', 'POST'])
@login_required
def add_transaction():
    username = current_user.username
    user_profile = get_current_profile()
    user_accounts = db.get_accounts(username, user_profile)

    if not user_accounts:
        flash(f'You need to create at least one account in the {user_profile} profile', 'alert')
        return redirect(url_for('add_account'))

    form = TransactionForm(user_accounts=user_accounts)


    if form.validate_on_submit():
        username = current_user.username
        profile = get_current_profile()
        category = form.category.data
        amount = form.amount.data
        account_debited = form.account_debited.data
        account_credited = form.account_credited.data
        subcategory = form.subcategory.data
        date = form.date.data.strftime("%Y-%m-%d")
        description = form.description.data

        # Create a Transaction object
        transaction_details = {
            'amount': amount,
            'account_debited': account_debited,
            'account_credited': account_credited,
            'subcategory' : subcategory,
            'time': date,
            'description' : description
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
        except KeyError as e:
            error_message = f"An error occurred: {str(e)} is an invalid key"
            flash(error_message, 'error')
        except IntegrityError as e:
            error_message = str(e)
            flash(error_message, 'error')
    return render_template('add_transaction.html', form=form, title="Add Transaction", acc=user_accounts)


# Route for adding a an account
@app.route('/add_account', methods=['GET', 'POST'])
@login_required
def add_account():
    username = current_user.username
    user_profile = get_current_profile()
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
        except (ValueError, IntegrityError) as e:
            error_message = str(e)
            flash(error_message, 'error')
    return render_template('add_account.html', form=form, title="Add Acount")

#Route for adding a profile
@app.route('/add_profile', methods=['GET', 'POST'])
@login_required
def add_profile():
    username = current_user.username
    form = AddProfileForm()
    if form.validate_on_submit():
        username = username
        profile = form.profile.data
        description = form.description.data
        set_as_default = form.set_as_default.data
        try:
            db.add_profile(username, profile, description, set_as_default)
            db.save()
            flash('Profile added successfully', 'success')
            return redirect(url_for('home'))
        except ValueError as e:
            error_message = str(e)
            flash(error_message, 'error')
    return render_template('add_profile.html', form=form, title="Add Acount")
