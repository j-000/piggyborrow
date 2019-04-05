from flask_mail import Mail
from flask_mail import Message as MailMessage
from myModels import app
from threading import Thread
from config_file import mail_settings

app.config.update(
  DEBUG=False,
  MAIL_SERVER='smtp.gmail.com',
  MAIL_PORT=465,
  MAIL_USE_SSL=True,
  MAIL_USERNAME = mail_settings['MAIL_USERNAME'],
  MAIL_PASSWORD = mail_settings['MAIL_PASSWORD'],
  MAIL_DEFAULT_SENDER = mail_settings['MAIL_DEFAULT_SENDER']
)


mail = Mail(app)

def send_async_email(app, msg):
  with app.app_context():
    mail.send(msg)


def sendEmail(email_subject, recipients, email_text=None, email_html=None):
  msg = MailMessage(email_subject, recipients=recipients)
  msg.body = email_text
  msg.html = email_html
  Thread(target=send_async_email, args=(app, msg)).start()


def generate_confirmation_token(email):
  serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
  return serializer.dumps(email, salt=app.config['SECURITY_PASSWORD_SALT'])


def confirm_token(token, expiration=3600):
  serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
  try:
    email = serializer.loads(
        token,
        salt=app.config['SECURITY_PASSWORD_SALT'],
        max_age=expiration
    )
  except:
      return False
  return email

