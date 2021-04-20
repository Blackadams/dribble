from flask import Blueprint, redirect, request, render_template, url_for
from .middleware import login_required
from .forms import RegisterForm, LoginForm

auth = Blueprint("auth", __name__, template_folder='templates')

@auth.route('/login', methods=['GET', 'POST'])
def login():
    login_form = LoginForm(request.form)
    return render_template('login.html', login_form=login_form)


@auth.route('/register', methods=['GET', 'POST'])
def register():
    register_form = RegisterForm(request.form)
    return render_template('register.html', register_form=register_form)


@auth.route('/logout')
@login_required
def logout():
    return redirect(url_for('api.logout'))