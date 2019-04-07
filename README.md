## piggyborrow - a flask application


Main features:
+ Recover Password
+ Reset Password 
+ Confirm account through email - uses jwt tokens.
+ Cookie setup if user is annonymous / has no account and performs a simple quote on main page. This cookie then assists in continuing that same quote after registration and email confirmation. 
+ Admin area to manage Users, Quotes, Rates, Messages
+ Stripe integration for payments (test mode only)

More details in the [requirements.txt file](https://github.com/j-000/piggyborrow/blob/master/requirements.txt). 


![alt text](https://github.com/j-000/piggyborrow/blob/master/repo_images/Capture.PNG "piggyborrow main page")

piggyborrow main page. It uses [Bootstrap](https://getbootstrap.com/) for the layout and styling. The spinner is plain javascript and css. 

![alt text](https://github.com/j-000/piggyborrow/blob/master/repo_images/Capture2.PNG "piggyborrow quote email confirmation")

The server side email sending is done via an asynchromnous thread using Google's smtp and [Flask-Mail](https://pythonhosted.org/Flask-Mail/).

![alt text](https://github.com/j-000/piggyborrow/blob/master/repo_images/Capture3.PNG "piggyborrow admin area")

Bootstrap layout, with integration of [Fontawesome icons](https://fontawesome.com/).

![alt text](https://github.com/j-000/piggyborrow/blob/master/repo_images/Capture4.PNG "piggyborrow admin area - rate setup ")

In this route I wanted to use a calendar view and decided to use [FullCalendar.js](https://fullcalendar.io/) plugin to accomplish that. 

![alt text](https://github.com/j-000/piggyborrow/blob/master/repo_images/Capture5.PNG "piggyborrow send us a message from profile")

Messages route within the profile. 

![alt text](https://github.com/j-000/piggyborrow/blob/master/repo_images/Capture6.PNG "piggyborrow quote form")

Quote form within the user profile.
