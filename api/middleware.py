from flask import session, jsonify
from functools import wraps


def admin_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'admin' in session['user']['roles']:
            return f(*args, **kwargs)
        else:
            return jsonify({'error': 'no authorization'}), 401

    return wrap

def beta_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'beta' in session['user']['roles']:
            return f(*args, **kwargs)
        else:
            return jsonify({'error': 'no authorization'}), 401

    return wrap
