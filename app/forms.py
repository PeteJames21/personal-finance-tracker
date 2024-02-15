import datetime
import re
from app import db
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, FloatField, SelectField, DateField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, InputRequired


class LoginForm(FlaskForm):
    '''Login fields etc'''
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    '''Registration form'''
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                           validators=[DataRequired(), Email()])
    # TODO: validate password security
    password = PasswordField('Password', validators=[DataRequired()])

    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    @staticmethod
    def validate_username(self, username):
        username = username.data
        print('type: ', type(username))
        if db.get_user_by_username(username):
            raise ValidationError('Username already exists')
        p = re.compile('^(?=.{2,20}$)(?![_.])(?!.*[_.]{2})[a-zA-Z0-9._]+(?<![_.])$')
        # Username must be 2-20 chars long, must not begin/end with special chars,
        #  can only be composed of [a-zA-Z0-9._], and must not have more than
        #  two consecutive special chars within the string.
        if not p.match(username):
            raise ValidationError('Invalid username format')

    @staticmethod
    def validate_email(self, email):
        email = email.data
        if db.email_exists(email):
            raise ValidationError('Email already in use. Try a different one')


class TransactionForm(FlaskForm):
    date = DateField('Date', default=datetime.date.today, validators=[DataRequired()])
    category = SelectField('Type of Transaction', choices=[('', 'Click to select either Income, Expense or Transfer'), ('incomes', 'Income'), ('expenses', 'Expense'), ('transfers', 'Transfer')], validators=[DataRequired()])
    amount = FloatField('Amount', validators=[InputRequired()])
    account_debited = SelectField('Account Debited', coerce=str)
    account_credited = SelectField('Account Credited', coerce=str)
    subcategory = StringField('Source/Destination of the money')
    description = StringField('Description')
    submit = SubmitField('Add Transaction')

    def __init__(self, *args, user_accounts=None, **kwargs):
        super(TransactionForm, self).__init__(*args, **kwargs)
        if user_accounts is not None:
            self.set_account_choices(user_accounts)

    def set_account_choices(self, user_accounts):
        self.account_debited.choices = [(account, account) for account in user_accounts]
        self.account_credited.choices = [(account, account) for account in user_accounts]

class AddAccountForm(FlaskForm):
    account = StringField('Account Name', validators=[DataRequired()])
    balance = FloatField('Balance', validators=[InputRequired()])
    description = StringField('Description')
    submit = SubmitField('Add Account')

class AddProfileForm(FlaskForm):
    profile = StringField('Profile Name', validators=[DataRequired()])
    description = StringField('Description')
    submit = SubmitField('Add Profile')
    set_as_default = BooleanField('Set as Default Profile?', default=False)
