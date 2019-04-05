from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, TextAreaField, DecimalField, SelectField, DateTimeField, TimeField, IntegerField, SelectMultipleField, DateField, FileField, SubmitField
from wtforms.validators import InputRequired, Email, Length, EqualTo


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[InputRequired(), Email(message='Invalid email!')])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=4, max=40, message='Your password must be at least 6 characters long and a mix of letters, numbers and special symbols.')])


class RecoverPasswordForm(FlaskForm):
    email = StringField('Email', id='email2' , validators=[InputRequired(), Email(message='Invalid email!')])


class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password', id='p1' ,validators=[InputRequired(), Length(min=6, max=40, message='Your password must be at least 6 characters long and a mix of letters, numbers and special symbols.')])
    password2 = PasswordField('Confirm Password', id='p2' ,validators=[InputRequired(), Length(min=6, max=40, message='Your password must be at least 6 characters long and a mix of letters, numbers and special symbols.')])


class RegistrationForm(FlaskForm):
	name = StringField('Name', validators=[InputRequired()])
	surname = StringField('Surname', validators=[InputRequired()])
	email = StringField('Email', validators=[InputRequired(), Email(message='Invalid email!')])
	address = StringField('Address', validators=[InputRequired()])
	postcode = StringField('Postcode', validators=[InputRequired()])
	password = PasswordField('Password', validators=[InputRequired(),  Length(min=4, max=40, message='Your password must be at least 6 characters long and a mix of letters, numbers and special symbols.')])
	password2 = PasswordField('Confirm Password', validators=[InputRequired(),EqualTo('password', message='Passwords must match!')])


class QuotationForm(FlaskForm):
	amount_requested = SelectField('Amount', id='amount_field', coerce=float, choices=[(0,'Select the amount'),(50,'£50.00'),(75,'£75.00'),(100,'£100.00'),(150,'£150.00'),(200,'£200.00'),(300,'£300.00')] ,validators=[InputRequired()])
	duration_in_days = SelectField('Period', id='period_field', coerce=int, choices=[(0,'Select the period'),(30,'30 days'),(45,'45 days'),(60,'60 days'),(90,'90 days')], validators=[InputRequired()])


class NewRateForm(FlaskForm):
	start_date = DateField('Start date', format='%d-%m-%Y', id='datepicker1', validators=[InputRequired()])
	end_date = DateField('End date', format='%d-%m-%Y', id='datepicker2', validators=[InputRequired()])
	value = SelectField('Rate value (daily)', coerce=float, choices=[(round(i*0.1, 2) , str(round(i*0.1,2)) + '%') for i in range(1, 9) ] ,validators=[InputRequired()])


class ChangeQuoteStatus(FlaskForm):
	new_status = SelectField('Status', coerce=int)


class MessageForm(FlaskForm):
	text = TextAreaField('Message', validators=[InputRequired()])
