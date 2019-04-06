import requests
import json
import os
import re
import datetime, time
import stripe
from datetime import date
from flask import url_for, render_template, flash, redirect, request, escape, make_response
from flask_moment import Moment
from flask_bootstrap import Bootstrap
from flask_login import login_required, current_user, LoginManager, login_user, logout_user
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from myModels import app
from myForms import LoginForm, RecoverPasswordForm, RegistrationForm, QuotationForm, ResetPasswordForm, NewRateForm, MessageForm, ChangeQuoteStatus
from myEmail import sendEmail


Bootstrap(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

moment = Moment(app)
from myModels import db, User, Rate, Quote, Payment, Status, ChangeLog, Message

migrate = Migrate(app, db)



# USER LOADER
@login_manager.user_loader
def load_user(user_id):
  return User.query.get(int(user_id))

# Unauthorised handler
@login_manager.unauthorized_handler
def unauthorized():
  flash('Please login to access your account.', 'info')
  return redirect(url_for('login'))




# Main page
@app.route('/', methods=['GET','POST'])
def index():
  form = QuotationForm()
  current_rate = Rate.get_current_rate()
  return render_template('public/home.html', form=form, current_rate=current_rate)


# register route
@app.route('/register', methods=['GET', 'POST'])
def register():
  if current_user.is_authenticated:
    return redirect(url_for('profile'))

  registerform = RegistrationForm()

  if request.method == 'POST' and registerform.validate_on_submit():

    # escape all inputs
    name = escape(registerform.name.data)
    surname = escape(registerform.surname.data)
    address = escape(registerform.address.data)
    postcode = escape(registerform.postcode.data)
    email = escape(registerform.email.data)
    password = generate_password_hash(escape(registerform.password.data), method='sha256')

    # check email is not already in use
    email_exists = User.query.filter_by(email=email).first()
    if email_exists:
      flash('There is an account already in use with that email ({}).'.format(email), 'info')
      return redirect(url_for('login'))

    # create a new user
    newuser = User(name=name, surname=surname, address=address, postcode=postcode, email=email, password=password)

    # commit to db
    db.session.add(newuser)
    db.session.commit()

    # send email with verification token
    registered_user = User.query.filter_by(email=email).first()
    verify_token = registered_user.get_verify_email_token()
    url = url_for('confirm_email', verify_token=verify_token, _external=True)
    html = render_template('email_templates/confirm_email_t.html', confirm_url=url)
    sendEmail(email_subject='Confirm your email!', recipients=[registered_user.email], email_html=html)

    # notify user and redirect
    flash('New user created! Check your email for the verification process.', 'success')
    return redirect(url_for('login'))

  return render_template('public/register.html', form=registerform)


# check email is not alreay register 
@app.route('/api/email', methods=['POST'])
def api_email():
  if request.method == 'POST':
    email_to_verify = escape(request.form.get('e'))
    user = User.query.filter_by(email=email_to_verify).first()
    print(user)
    if user:
      response = {'valid':False}
    else:
      response = {'valid': True}
    return json.dumps(response) 



@app.route('/confirm_email/<verify_token>')
def confirm_email(verify_token):
  # check token is valid
  user = User.verify_email_token(verify_token)

  if not user:
    flash('The recover token is invalid or has expired. Log into your account to request a new confirmation link.', 'info')
    return redirect(url_for('login'))

  if user.verified_user:
    flash('This email has already been verified.', 'info')
    return redirect(url_for('login'))

  validate = user.validate_user()
  db.session.commit()

  flash('Your email has been validated successfully!', 'success')
  return redirect(url_for('login'))


# login route
@app.route('/login', methods=['GET', 'POST'])
def login():
  if current_user.is_authenticated:
    return redirect(url_for('profile'))

  loginform = LoginForm()
  recoverpasswordform = RecoverPasswordForm()

  # get parameter if the user has made a simple quote on the home page. Content is B64 encoded and stored as cookie 'h'
  next_variable = request.args.get('h')

  if request.method == 'POST' and loginform.validate_on_submit():
    # escape user input
    escaped_email = escape(loginform.email.data)
    # search db for user
    user = User.query.filter_by(email=escaped_email).first()
    
    if user:
      # check password match
      if check_password_hash(user.password, loginform.password.data):
      # login user
        login_user(user)
        flash('Welcome {}!'.format(user.name),'success')

        # redirect to profile (protected area)
        return redirect(url_for('profile'))
      else:
        flash('Wrong password or email.', 'danger')
    else:
      # notify and redirect to login
      flash('That email is not registered.','info')

    return redirect(url_for('login')) 

  if request.method == 'POST' and recoverpasswordform.validate_on_submit():
    # escape user input
    escaped_email = escape(recoverpasswordform.email.data)
    # search db for user
    user = User.query.filter_by(email=escaped_email).first()

    if user:
      # user found
      recover_token = user.get_recover_password_token()
      url = url_for('reset_password', recover_token=recover_token, _external=True)
      html = render_template('email_templates/reset_password_email_t.html', confirm_url=url)
      sendEmail(email_subject='Reset your password', recipients=[user.email], email_html=html)
      flash('An email has been sent to "{}" with the password reset link. You have 10 minutes until it expires.'.format(escaped_email), 'info')
    else:
      flash('That email is not registered.', 'info')

    return redirect(url_for('login'))
   
  # handle response
  resp = make_response(render_template('public/login.html', loginform=loginform, form2=recoverpasswordform))
  
  # check next variable is valid and set it as cookie. Expires in 5 minutes.
  if next_variable:
    try:
      User.validate_cookie(next_variable)
      resp.set_cookie('h', next_variable, expires=int(time.time())+300)
    except:
      pass
  return resp 


@app.route('/reset_password/<recover_token>', methods=['GET','POST'])
def reset_password(recover_token):
  # if user is logged in, no need to reset password.
  if current_user.is_authenticated:
    return redirect(url_for('profile'))

  # verify token in GET request
  user = User.verify_reset_password_token(recover_token)
  if not user:
    flash('The recover token is invalid or has expired. Request a new one to reset your password.', 'info')
    return redirect(url_for('login'))

  # Handle reset form / token is valid
  form = ResetPasswordForm()
  if request.method == 'POST' and form.validate_on_submit():
    if form.password.data != form.password2.data:
      flash('Those passwords did not match. Try again!','danger')
      return redirect(url_for('login'))

    hashed_password = generate_password_hash(form.password.data, method='sha256')
    user.password = hashed_password
    db.session.commit()
    flash('Your password has been successfully reseted. Log into your account.', 'success')
    return redirect(url_for('login'))

  return render_template('public/reset_password.html',form=form, token=recover_token)


# profile route
@app.route('/profile', methods=['GET'])
@login_required
def profile():
  if not current_user.verified_user:
    flash('Your account is not verified. Verify your account now to be able to use all features.', 'danger')

  # check if cookie 'h' is set (validity has been check in previour route)
  h = request.cookies.get('h')
  if h: 
    flash('Looks like you have performed a simple quote.', 'info')


  active_quotes = [i for i in current_user.quotes if i.is_active()]
  return render_template('protected/profile.html', active_quotes=active_quotes)

  
# quotation route
@app.route('/quotation', methods=['GET','POST'])
@login_required
def quotation():
  if not current_user.verified_user:
    return redirect(url_for('profile'))

  form = QuotationForm()

  # check user can borrow
  if not  current_user.can_borrow():
    flash('You currently have an open quote. Please close this quote to be able to apply again.','info')
    return redirect(url_for('profile'))

  # handle quote form
  if request.method == 'POST' and form.validate_on_submit():
    # escape input from form
    amount_requested = form.amount_requested.data
    duration_in_days = form.duration_in_days.data
    rate_id = Rate.get_current_rate().id
    status_id = Status.query.filter_by(name='Quote sent').first().id

    # new quote
    new_quote = Quote(user_id=current_user.id, 
      amount_requested=amount_requested, duration_in_days=duration_in_days, rate_id=rate_id, status_id=status_id)
    db.session.add(new_quote)
    db.session.commit()

    # send email confirmation
    html = render_template('email_templates/quote_email_confirmation.html', new_quote=new_quote)
    sendEmail(email_subject='Your quote', recipients=[current_user.email], email_html=html)

    flash('Your quote has been sent! You will shortly receive an email confirmation with all the details of your quote.', 'success')
    return redirect(url_for('profile'))
  
  current_rate = Rate.get_current_rate()
  return render_template('protected/quotation.html', form=form, current_rate=current_rate)


# cancel quotation
@app.route('/quotation/<quote_id>', methods=['GET','POST'])
@login_required
def cancel_quote(quote_id):
  if not current_user.verified_user:
    return redirect(url_for('profile'))

  if request.method == 'POST':
    quote = Quote.query.get(escape(quote_id))
    if quote:
      quote.change_status()

  else:
    return redirect(url_for('profile'))


# calendat route
@app.route('/calendar', methods=['GET','POST'])
@login_required
def user_calendar():
  if not current_user.verified_user:
    return redirect(url_for('profile'))

  user_quotes = current_user.quotes
  quotes_for_calendar = [{'title': '#{} Initial request\n £{:0.2f}'.format(i.id, i.amount_requested), 'start': str(i.creation_timestamp)} for i in user_quotes]
  for x in user_quotes:
    quotes_for_calendar += [{'title': '#{} {}'.format(i.quote_id, i.get_status_name()), 'start': str(i.timestamp)} for i in x.change_log]
  quotes_for_calendar += [{'title':'#{} Payment due\n £{:0.2f}'.format(i.id, i.get_total_payable()), 'start': str(i.get_due_date()) } for i in user_quotes]

  return render_template('protected/calendar.html', quotes_for_calendar=quotes_for_calendar)


@app.route('/reports', methods=['GET','POST'])
@login_required
def reports():
  if not current_user.verified_user:
    return redirect(url_for('profile'))

  return render_template('protected/reports.html')


@app.route('/pay', methods=['GET','POST'])
@login_required
def pay():
  if not current_user.verified_user:
    return redirect(url_for('profile'))

  if request.method == 'POST':
    print(request.form)

  amount_due = current_user.get_amount_due() 
  amount_due_in_cents = amount_due * 100
  return render_template('protected/pay.html', amount_due_in_cents=amount_due_in_cents, amount_due=amount_due)


@app.route('/help', methods=['GET','POST'])
@login_required
def help():
  if not current_user.verified_user:
    return redirect(url_for('profile'))

  messageform = MessageForm()

  if request.method == 'POST' and messageform.validate_on_submit():
    text = escape(messageform.text.data)
    new_message = Message(text=text,user_id=current_user.id)
    db.session.add(new_message)
    db.session.commit()
    flash('Message sent successfully!','success')
    return redirect(url_for('help'))

  return render_template('protected/help.html', messageform=messageform)





















# Admin area route
@app.route('/admin', methods=['GET'])
@login_required
def admin():
  if not current_user.is_admin:
    flash('This is a protected route for our admins. This attempt has been recorded.', 'info')
    return redirect(url_for('login'))
  totals = {
  'users_total': len(User.query.all()),
  'quotes_total': len(Quote.query.all()),
  'payments_total': len(Payment.query.all())
  }
  # this gets whatever rate it is (default/or custom).
  current_rate=Rate.get_current_rate()
  # this checks whether it is a custom or default rate.
  rate_set = Rate.check_is_rate_set()
  return render_template('protected/admin/admin_area.html', totals=totals, rate_set=rate_set , current_rate=current_rate)


# Admin/users area route
@app.route('/admin/users', methods=['GET'])
@login_required
def admin_users():
  if not current_user.is_admin:
    flash('This is a protected route for our admins. This attempt has been recorded.', 'info')
    return redirect(url_for('login'))
  users = User.query.all()
  return render_template('protected/admin/admin_users.html', users=users)


@app.route('/admin/user/<user_id>', methods=['GET'])
@login_required
def admin_user(user_id):
  if not current_user.is_admin:
    flash('This is a protected route for our admins. This attempt has been recorded.', 'info')
    return redirect(url_for('login'))

  user = User.query.get(user_id)
  if not user:
    flash('That user id is not valid.','info')
    return redirect(url_for('admin_users'))
  active_quotes = [i for i in user.quotes if i.is_active()]
  return render_template('protected/admin/admin_user.html', user=user, active_quotes=active_quotes)


# Admin/rates area route
@app.route('/admin/rates', methods=['GET', 'POST'])
@login_required
def admin_rates():
  if not current_user.is_admin:
    flash('This is a protected route for our admins. This attempt has been recorded.', 'info')
    return redirect(url_for('login'))

  form = NewRateForm()
  if request.method == 'POST' and form.validate_on_submit():
    # escape form input
    new_rate_start_date = Rate.convert_date_to_datetime(form.start_date.data)
    new_rate_end_date = Rate.convert_date_to_datetime(form.end_date.data)
    new_rate_value = escape(form.value.data)
    
    # ensure no rate exists during same period
    all_rates = Rate.query.all()
    conflict = False

    # if there is a rate such that the new rate falls between the dates, then there is a conflict.
    # ("rate_start" < "new rate start date" < "rate_end")
    for rate in all_rates:
      if rate.start_date < new_rate_start_date < rate.end_date:
        conflict = True
        break
    for rate in all_rates:
      if rate.start_date < new_rate_end_date < rate.end_date:
        conflict = True
        break
    
    if conflict:
      flash('There is at least one rate conflicting with this new rate.','danger')
      return redirect(url_for('admin_rates'))
    else:
      # create new rate
      new_rate = Rate(start_date=new_rate_start_date, end_date=new_rate_end_date, value=new_rate_value, user_id=current_user.id)
      db.session.add(new_rate)
      db.session.commit()
      flash('New rate added successfully.','success')
      return redirect(url_for('admin_rates'))

  rates = Rate.query.all()
  rates_for_calendar = [{'title' : str(i.value) + '% / day','start' : str(i.start_date),'end' : str(i.end_date)} for i in rates]
  return render_template('protected/admin/admin_rates.html', form=form, rates=rates ,rates_for_calendar=rates_for_calendar)


@app.route('/admin/quotes', methods=['GET', 'POST'])
@login_required
def admin_quotes():
  if not current_user.is_admin:
    flash('This is a protected route for our admins. This attempt has been recorded.', 'info')
    return redirect(url_for('login'))

  quotes = Quote.query.all()
  return render_template('protected/admin/admin_quotes.html', quotes=quotes)

@app.route('/admin/quote/<quote_id>', methods=['GET', 'POST'])
@login_required
def admin_quote(quote_id):
  if not current_user.is_admin:
    flash('This is a protected route for our admins. This attempt has been recorded.', 'info')
    return redirect(url_for('login'))

  quote_id = escape(quote_id)
  quote = Quote.query.get(quote_id)

  if not quote:
    flash('That quote id is not valid.','danger')
    return redirect(url_for('admin_quotes'))

  form = ChangeQuoteStatus()
  form.new_status.choices = [(i.id, i.name) for i in Status.query.all()]

  if request.method == 'POST' and form.validate_on_submit():
    quote.change_status(escape(form.new_status.data))
    db.session.commit()

    #log changes
    new_log = ChangeLog(new_status=quote.get_status().id, quote_id=quote.id)
    db.session.add(new_log)
    db.session.commit()

    flash('Quote updated successfully.','success')
    return redirect(url_for('admin_quotes'))

  return render_template('protected/admin/admin_quote.html', quote=quote, form=form)


@app.route('/admin/messages', methods=['GET','POST'])
@login_required
def admin_messages():
  if not current_user.is_admin:
    flash('This is a protected route for our admins. This attempt has been recorded.', 'info')
    return redirect(url_for('login'))

  # ajax request through POST method 
  if request.method == 'POST':
    # message_id get variable
    mid = escape(request.form.get('mid'))
    if mid:        
      message = Message.query.get(mid)
      message.mark_read()
      db.session.commit()
    return json.dumps({'message':str(message.text), 'user' : str(message.get_user().name) , 'timestamp' : str(message.creation_timestamp)})

  messageform=MessageForm()
  messages_array = Message.query.all()
  return render_template('protected/admin/admin_messages.html', messageform=messageform, messages_array=messages_array)



# Logout route
@app.route('/logout', methods=['GET'])
@login_required
def logout():
  logout_user()
  return redirect(url_for('index'))


#Start app
if __name__ == '__main__':
  app.run(debug=True)