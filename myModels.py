from datetime import datetime, timedelta, date
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
from flask_login import UserMixin
from time import time
from config_file import app_settings
import jwt 
import base64 

app = Flask(__name__)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = app_settings['SQLALCHEMY_DATABASE_URI']
app.config['SECRET_KEY'] = app_settings['SECRET_KEY']
app.config['SECURITY_PASSWORD_SALT'] = app_settings['SECURITY_PASSWORD_SALT']

db = SQLAlchemy(app)

class User(db.Model, UserMixin):
  __tablename__ = "user"

  id = db.Column(db.Integer, primary_key=True)
  creation_timestamp = db.Column(db.DateTime(), default=datetime.now())
  name = db.Column(db.String(30), nullable=False)
  surname = db.Column(db.String(30) ,nullable=False)
  address = db.Column(db.String(20), nullable=False)
  postcode = db.Column(db.String(20), nullable=False)
  email = db.Column(db.String(20), unique=True, nullable=False)
  password = db.Column(db.String(85), nullable=False)
  quotes = db.relationship('Quote', backref='user', lazy=True)
  verified_user = db.Column(db.Boolean, default=False)
  is_admin = db.Column(db.Boolean, default=False)
  rates = db.relationship('Rate', backref='user', lazy=True)
  payments = db.relationship('Payment', backref='user', lazy=True)
  messages = db.relationship('Message', backref='user', lazy=True)

  def get_recover_password_token(self, expires_in=600):
    return jwt.encode({'reset_password': self.id, 'exp': time() + expires_in}, app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

  @staticmethod
  def verify_reset_password_token(token):
    try:
        id = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])['reset_password']
    except:
        return
    return User.query.get(id)


  def get_verify_email_token(self, expires_in=600):
    return jwt.encode({'current_user': self.id, 'email': self.email , 'exp': time() + expires_in}, app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')


  @staticmethod
  def verify_email_token(token):
    try:
        t = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
    except:
        return
    return User.query.get(t['current_user'])


  def get_reset_email_token(self, new_email ,expires_in=600):
    return jwt.encode({'current_user': self.id, 'new_email': new_email , 'exp': time() + expires_in}, app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')


  @staticmethod
  def verify_reset_email_token(token):
    try:
        t = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
    except:
        return
    return (User.query.get(t['current_user']), t['new_email'] )


  @staticmethod
  def validate_cookie(cookie):
    b = base64.b64decode(cookie.encode('utf-8'))
    if b'a' in b and b'b' in b:
      return True
    return False

  def validate_user(self):
    self.verified_user = True
    return True 


  def make_admin(self):
    self.is_admin = True
    return True


  def can_borrow(self):
    for quote in self.quotes:
      if quote.is_active():
        return False
    return True


  def get_amount_due(self):
    for quote in self.quotes:
      if quote.is_active():
        return quote.get_total_payable()
    return 0


  def get_quotes_stats(self):
    stat = {
    'total_quotes': len(self.quotes),
    'total_amount_requested' : 0,
    'total_money_borrowed' : 0,
    'total_interest_paid' : 0
    }

    for quote in self.quotes:
      stat['total_amount_requested'] += quote.amount_requested

      if quote.get_status().name == 'Paid':
        stat['total_money_borrowed'] += quote.amount_requested
        stat['total_interest_paid'] += quote.get_interest_amount()

    return stat        




class Rate(db.Model):
  __tablename__ = "rate"
  
  id = db.Column(db.Integer, primary_key=True)
  user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
  creation_timestamp = db.Column(db.DateTime(), default=datetime.now())
  start_date = db.Column(db.DateTime())
  end_date = db.Column(db.DateTime())
  value = db.Column(db.Float)
  quotes = db.relationship('Quote', backref='rate', lazy=True)

  def get_user_details(self):
    return User.query.get(self.user_id)

  @staticmethod
  def get_current_rate():
    today = datetime.today()
    rates = Rate.query.all()

    for i in rates:
      if today >= i.start_date and today <= i.end_date:
        return i

    return rates[0]

  @staticmethod
  def check_is_rate_set():
    today = datetime.today()
    rates = Rate.query.all()

    for i in rates:
      if today >= i.start_date and today <= i.end_date:
        return True
    return False


  @staticmethod
  def convert_date_to_datetime(date_string):
    date_array = str(date_string).split('-')
    d = datetime(int(date_array[0]),int(date_array[1]),int(date_array[2]),14,30)
    return d



class Quote(db.Model):
  __tablename__ = "quote"

  id = db.Column(db.Integer, primary_key=True)
  creation_timestamp = db.Column(db.DateTime(), default=datetime.now())
  user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
  amount_requested = db.Column(db.Float())
  duration_in_days = db.Column(db.Integer())
  rate_id = db.Column(db.Integer, db.ForeignKey('rate.id'), nullable=False)
  payments = db.relationship('Payment', backref='quote', lazy=True)
  status_id = db.Column(db.Integer, db.ForeignKey('status.id'), nullable=False)
  change_log = db.relationship('ChangeLog', backref='quote', lazy=True)

  def get_status(self):
    return Status.query.get(self.status_id)

  def is_overdue(self):
    today = datetime.now()
    return today > self.get_due_date() 

  def get_due_date(self):
    return self.creation_timestamp + timedelta(days=self.duration_in_days)

  def get_rate(self):
    return Rate.query.get(self.rate_id) 

  def get_interest_amount(self):
    rate = self.get_rate().value
    return round(self.amount_requested * self.duration_in_days * rate * 0.01, 2)

  def get_total_payable(self):
    return round(self.amount_requested + self.get_interest_amount(), 2)

  def get_user(self):
    return User.query.get(self.user_id)

  def change_status(self, new_status_id):
    valid_status = Status.query.get(new_status_id)
    if valid_status:
      self.status_id = new_status_id
    return

  def is_active(self):
    return self.get_status().name in ['In review', 'Approved', 'Monies Released', 'Quote sent']  



class Status(db.Model):
  ''' ['In review', 'Approved', 'Declined', 'Monies Released', 'Paid', 'Cancelled', 'Quote sent'] '''
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(30), nullable=False)
  quotes = db.relationship('Quote', backref='status', lazy=True)




class ChangeLog(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  quote_id = db.Column(db.Integer, db.ForeignKey('quote.id'), nullable=False)
  timestamp = db.Column(db.DateTime(), default=datetime.now())
  new_status = db.Column(db.Integer(), nullable=False)

  def get_status_name(self):
    return Status.query.get(self.new_status).name



class Payment(db.Model):
  __tablename__ = "payment"

  id = db.Column(db.Integer, primary_key=True)
  creation_timestamp = db.Column(db.DateTime(), default=datetime.now())
  user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
  quote_id = db.Column(db.Integer, db.ForeignKey('quote.id'), nullable=False)
  amount = db.Column(db.Float(), nullable=False)



class Message(db.Model):
  __tablename__ = "message"

  id = db.Column(db.Integer, primary_key=True)
  creation_timestamp = db.Column(db.DateTime(), default=datetime.now())
  user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
  text = db.Column(db.Text())
  read = db.Column(db.Boolean(), default=False)

  def get_user(self):
    return User.query.get(self.user_id)

  def is_read(self):
    return self.read

  def mark_read(self):
    self.read = True
    return