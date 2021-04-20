from wtforms import Form, SubmitField, StringField, BooleanField, PasswordField, validators
from wtforms.fields.html5 import EmailField
from markupsafe import Markup

class LoginForm(Form):
    username_login = StringField('username', [
        validators.Length(min=4, max=25),
        validators.DataRequired()
    ])
    password_login = PasswordField('password', [
        validators.DataRequired()
    ])
    button_login = SubmitField('Login')


class RegisterForm(Form):
    first_name_register = StringField('first-name', [
        validators.DataRequired()
    ])
    last_name_register = StringField('last-name', [
        validators.DataRequired()
    ])
    username_register = StringField('username', [
        validators.Length(min=4, max=25),
        validators.DataRequired()
    ])
    email_register = EmailField('email', [
        validators.DataRequired(),
        validators.Email()
    ])
    password_register = PasswordField('password', [
        validators.DataRequired(),
        validators.EqualTo('confirm_password_register', message='Passwords must match.')
    ])
    confirm_password_register = PasswordField('confirm-password')
    invite_code = StringField('invite-code', [
        validators.Length(min=0, max=32)
    ])
    tos_agreement = BooleanField('tos-agreement', [
        validators.DataRequired()
    ])

class PasswordReset(Form):
    current_password = PasswordField('current-password', [
        validators.DataRequired()
    ])
    new_password = PasswordField('new-password', [
        validators.DataRequired(),
        validators.EqualTo('new_password_confirm', message='Passwords must match.')
    ])
    new_password_confirm = PasswordField('new-password-confirm', [
        validators.DataRequired()
    ])
    button_submit = SubmitField('Submit')