from app import db, User, Rate, generate_password_hash, Status
from datetime import datetime, date

def restart():
	db.drop_all()
	db.create_all()
	create_admin()
	create_test_user()
	create_initial_rate()
	create_status()

def create_admin():
	admin = User(name='Joao', 
		surname='Oliveira', 
		address='General Office', 
		postcode='NA1 1AH', email='jjasilva85@gmail.com', 
		password=generate_password_hash('123456789',method='sha256'),
		verified_user=True,
		is_admin=True)
	db.session.add(admin)
	db.session.commit()

def create_test_user():
	test_user = User(name='Test', surname='Oliveira', address='Test Address', 
		postcode='NA1 1AH', 
		email='jjasilva84@l.com', 
		password=generate_password_hash('123456789',method='sha256'), 
		verified_user=True,
		is_admin=False)
	db.session.add(test_user)
	db.session.commit()

def create_initial_rate():
	rate = Rate(start_date=datetime(2019,3,20,14,30), end_date=datetime(2019,3,25,14,30), value=0.4, user_id=1)
	db.session.add(rate)
	db.session.commit()


def create_status():
	for i in ['In review', 'Approved', 'Declined', 'Monies Released', 'Paid', 'Cancelled', 'Quote sent']:
		status = Status(name=i)
		db.session.add(status)

	db.session.commit()