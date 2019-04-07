## piggyborrow - a flask application


### [Watch the video of this application in action](https://github.com/j-000/piggyborrow/blob/master/repo_images/piggyborrow.mp4). 


Main features:
+ Recover Password
+ Reset Password 
+ Confirm account through email - uses jwt tokens.
+ Cookie setup if user is annonymous / has no account and performs a simple quote on main page. This cookie then assists in continuing that same quote after registration and email confirmation 
+ Admin area to manage Users, Quotes, Rates, Messages
+ Stripe integration for payments (test mode only)

More details of modules used in the [requirements.txt file](https://github.com/j-000/piggyborrow/blob/master/requirements.txt). 


piggyborrow main page. It uses [Bootstrap](https://getbootstrap.com/) for the layout and styling. The spinner is plain javascript and css. 
![alt text](https://github.com/j-000/piggyborrow/blob/master/repo_images/Capture.PNG "piggyborrow main page")


The server side email sending is done via an asynchromnous thread using Google's smtp and [Flask-Mail](https://pythonhosted.org/Flask-Mail/).
![alt text](https://github.com/j-000/piggyborrow/blob/master/repo_images/Capture2.PNG "piggyborrow quote email confirmation" )


Bootstrap layout, with integration of [Fontawesome icons](https://fontawesome.com/).
![alt text](https://github.com/j-000/piggyborrow/blob/master/repo_images/Capture3.PNG "piggyborrow admin area" )


In this route I wanted to use a calendar view and decided to use [FullCalendar.js](https://fullcalendar.io/) plugin to accomplish that. 
![alt text](https://github.com/j-000/piggyborrow/blob/master/repo_images/Capture4.PNG "piggyborrow admin area - rate setup " )


Messages route within the profile. 
![alt text](https://github.com/j-000/piggyborrow/blob/master/repo_images/Capture5.PNG "piggyborrow send us a message from profile" )


Quote form within the user profile.
![alt text](https://github.com/j-000/piggyborrow/blob/master/repo_images/Capture6.PNG "piggyborrow quote form" )

***

## The idea behind this project

The main idea of this project is to recreate a website where customers can borrow money. The customer journey starts with a simple quote, followed by registration, email confirmation and continuing the simple quote within their profile. 

After the quote is sent, an email is sent to the customer with the details. An email is also sent everytime the quote's status changes. The customer can see within their account a calendar view of the quote stages. In this view, they can also see when their payment is due and the amount. 

Customers can make payments via their account.