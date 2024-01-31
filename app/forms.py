from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, FloatField, SelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError


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
    password = PasswordField('Password', validators=[DataRequired()])
   
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

class TransactionForm(FlaskForm):
    category = SelectField('Category', choices=[('incomes', 'Income'), ('expenses', 'Expense'), ('transfers', 'Transfer')], validators=[DataRequired()])
    amount = FloatField('Amount', validators=[DataRequired()])
    account_debited = StringField('Account Debited')
    account_credited = StringField('Account Credited')
    submit = SubmitField('Add Transaction')