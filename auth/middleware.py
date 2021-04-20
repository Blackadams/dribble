from flask import session, redirect, url_for, jsonify
from functools import wraps


def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'user' in session:
            return f(*args, **kwargs)
        else:
            #return jsonify({'error': 'no logon'})
            return redirect(url_for('auth.login'))

    return wrap
