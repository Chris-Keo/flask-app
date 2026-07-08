from flask_mail import Message
from app import mail
from flask import render_template
from app import app
from threading import Thread

def send_async_email(app, msg):
    """
    Runs in the background thread invoked via Thread class
    This thread will clean itself up
    """
    with app.app_context():
        """Note: app.app_context() will have access to the application instance and 
        The application context is essential for extensions that need access to the Flask application instance.
        It allows them to find the application without explicitly passing it as an argument.
        Extensions often store their configuration in the app.config object, which contains settings specific to the application. """
        mail.send(msg)

def send_email(subject, sender, recipients, text_body, html_body):
    """
    Make sure you’ve configured Flask-Mail with the appropriate SMTP settings (e.g., mail server, port, credentials) before calling this function
    """
    msg = Message(subject, sender=sender, recipients=recipients) # The Message object is initialized with the subject and sender (the email address from which the email will be sent)
    msg.body = text_body # contains the plain text version of the email.
    msg.html = html_body # contains the HTML version of the email (useful for formatting and styling)
    # mail.send(msg)
    Thread(target=send_async_email, args=(app, msg)).start()

# def send_email(subject, sender, recipients, text_body, html_body):
#     """
#     Make sure you’ve configured Flask-Mail with the appropriate SMTP settings (e.g., mail server, port, credentials) before calling this function
#     """
#     msg = Message(subject, sender=sender, recipients=recipients) # The Message object is initialized with the subject and sender (the email address from which the email will be sent)
#     msg.body = text_body # contains the plain text version of the email.
#     msg.html = html_body # contains the HTML version of the email (useful for formatting and styling)
#     mail.send(msg)

def send_password_reset_email(user):
    """
    Relies on send_email()
    text and HTML content is generated using render_template and user and token is passed as arguments
    """
    token = user.get_reset_password_token()
    send_email('[Microblog] Reset Password',
               sender=app.config['ADMINS'][0],
               recipients=[user.email],
               text_body=render_template('email/reset_password.txt',
                                        user=user, token=token),
                html_body=render_template('email/reset_password.html', user=user, token=token)
               )