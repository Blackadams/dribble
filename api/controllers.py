'''
    controllers.py
    github.com/doge

    endpoints:
        authentication
            POST /api/auth/loader
                :parameter username_login
                :parameter password_login
                :parameter hwid
                :return on 200, return success message, hwid, roles and subscription date

            POST /api/auth/login
                :parameter username_login
                :parameter password_login
                :return on 200, set user object to session cookie

            POST /api/auth/logout
                :return on 200, pops session cookie deauthenticating the user and redirects
                them to the login page

        user functions
            POST /api/users/get
                :return on 200, return username, email and role for each user.
                ( only to be accessed by users with 'admin' role )

            POST /api/users/create
                :parameter username_register
                :parameter password_register
                :parameter email_register
                :parameter first_name_register
                :parameter last_name_register
                :return on 200, return success message and insert new user into
                the database.

            # todo
            POST /api/users/roles/get
                :parameter username
                :return roles array for a specific user

            # todo
            POST /api/users/roles/create
                :parameter title
                :parameter authorization level
                :return success message and insert role into the database
'''


from flask import Blueprint, session, jsonify, request, redirect, url_for
from auth.middleware import login_required
from .middleware import admin_required
from utils.database import Database
from config import Config
from auth.forms import LoginForm, RegisterForm
import hashlib
from datetime import datetime, timedelta
from bson.objectid import ObjectId

api = Blueprint("api", __name__, template_folder='templates')

user_database = Database(Config.credentials, "users")
ticket_database = Database(Config.credentials, "tickets")
payment_database = Database(Config.credentials, "payments")
logs_database = Database(Config.credentials, "logs")


def log(data):
    try:
        logs_database.insert({
            'author': data['username'],
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'ip': data['ip'],
            'message': data['message']
        })
        return jsonify({
            'status': 'success'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': e
        })


# this method returns information about a user given a username and password
# can be used for authentication for desktop applications
@api.route("/api/auth/loader", methods=["POST"])
def loader():
    # takes in username_
    content = request.json
    hashed_password = hashlib.sha256(content['password_login'].encode('utf-8')).hexdigest()
    user = user_database.find_one({
        'username': content['username_login'],
        'password': hashed_password
    })

    if user:
        if user['hwid'] is None:
            user_database.update({
                'username': content['username_login']
            }, {
                '$set': {
                    'hwid': content['hwid']
                }
            })
            log({
                'username': content['username_login'],
                'ip': request.remote_addr,
                'message': "Hardware identifier set."
            })

        elif user['hwid'] != content['hwid']:
            log({
                'username': content['username_login'],
                'ip': request.remote_addr,
                'message': "Hardware identifier mismatch."
            })
            return jsonify({
                'status': 'error',
                'message': 'Hardware identifier mismatch.'
            }), 401

        log({
            'username': content['username_login'],
            'ip': request.remote_addr,
            'message': "Loader login."
        })
        return jsonify({
            'status': 'success',
            'roles': user['roles'],
            'subscribed_until': user['subscribed_until']
        })
    else:
        return jsonify({
            'status': 'error',
            'message': 'Invalid credentials.'
        }), 401

# authentication
@api.route("/api/auth/login", methods=['POST'])
def login():
    # take in username/password and do db comparison
    # return the result

    content = request.form
    login_form = LoginForm(content)

    if login_form.validate():
        hashed_password = hashlib.sha256(content['password_login'].encode('utf-8')).hexdigest()
        user = user_database.find_one({
            'username': content['username_login'],
            'password': hashed_password
        })
        if user:
            user['_id'] = str(user['_id'])
            session['user'] = user
            print(request.remote_addr)

            log({
                'username': user['username'],
                'ip': request.remote_addr,
                'message': 'Login at ' + request.remote_addr
            })

            return jsonify({
                'status': 'success',
                'hwid': user['hwid'],
                'subscribed_until': user['subscribed_until'],
                'message': 'Login successful.'
            })
        return jsonify({
            'status': 'error',
            'message': 'Invalid credentials.'
        })
    return jsonify({
        'status': 'error',
        'message': 'Please fill out the form.'
    })

@api.route("/api/auth/logout", methods=["POST", "GET"])
@login_required
def logout():
    session.pop('user')
    #return jsonify({'status': 'success'})
    return redirect(url_for('auth.login'))

# user functions
@api.route("/api/users/get", methods=['POST', 'GET'])
@login_required
@admin_required
def get_users():
    # return all users in a database given
    users = user_database.find()
    for user in users:
        user['_id'] = str(user['_id'])

    return jsonify({
        'status': 'success',
        'users': {
            'username': user['username'],
            'email': user['email'],
            'roles': user['roles']
        }
    })


@api.route("/api/users/create", methods=['POST'])
def register():
    content = request.form
    register_form = RegisterForm(content)

    if register_form.validate():
        existing_user = user_database.find_one({'username': content['username_register']})
        if not existing_user:
            hashed_password = hashlib.sha256(content['password_register'].encode('utf-8')).hexdigest()
            user_database.insert({
                'username': content['username_register'],
                'password': hashed_password,
                'email': content['email_register'],
                'first_name': content['first_name_register'],
                'last_name': content['last_name_register'],
                'roles': ['user'],
                'signup-date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'hwid': None,
                'subscribed_until': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
            return jsonify({'status': 'success', 'message': 'Your account has been created.'})
        return jsonify({
            'status': 'error',
            'message': 'Username already exists.'
        })

    try:
        return jsonify({
            'status': 'error',
            'message': dict(register_form.errors.items())['password_register']
        })
    except:
        return jsonify({
            'status': 'error',
            'message': 'Please fill out the form.'
        })


@api.route("/api/users/roles/get", methods=['POST', 'GET'])
@login_required
def get_roles():
    content = request.json
    user = user_database.find_one({'username': content['username']})
    return jsonify({'roles': user['roles']})

@api.route("/api/users/roles/create", methods=['POST'])
@login_required
def create_role():
    # todo
    # create a role but only if the user is an administrator
    pass

# tickets
@api.route("/api/tickets/get", methods=['GET'])
@login_required
def get_tickets():
    # return tickets that apply to a certain user
    if 'admin' in session['user']['roles']:
        tickets = ticket_database.find()
    else:
        tickets = ticket_database.find({'author': session['user']['username']})
    for ticket in tickets:
        ticket['_id'] = str(ticket['_id'])
        ticket['creation_date'] = str(ticket['creation_date'])
        for item in ticket['discussion']:
            item['timestamp'] = str(item['timestamp'])

    return jsonify(tickets)

# tickets
@api.route("/api/tickets/get_one", methods=['POST'])
@login_required
def get_one_ticket():
    # return tickets that apply to a certain user
    content = request.json
    ticket = ticket_database.find_one({'_id': ObjectId(content['id'])})
    
    ticket['_id'] = str(ticket['_id'])
    ticket['creation_date'] = str(ticket['creation_date'])
    for item in ticket['discussion']:
        item['timestamp'] = str(item['timestamp'])

    return ticket


@api.route("/api/tickets/create", methods=['POST'])
@login_required
def create_ticket():
    content = request.json
    user = session['user']
    current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        ticket_database.insert({
            'author': user['username'],
            'subject': content['subject'],
            'resolved': False,
            'creation_date': current_date,
            'discussion': [
                {
                    'author': user['username'],
                    'timestamp': current_date,
                    'body': content['body']
                }
            ]
        })
        return jsonify({
            'status': 'success',
            'message': 'Ticket was successfully created.'
        })
    except:
        return jsonify({
            'status': 'error',
            'message': 'Ticket could not be created.'
        }), 400


@api.route("/api/tickets/reply", methods=['POST'])
@login_required
def reply_ticket():
    content = request.json
    user = session['user']
    ticket = ticket_database.find_one({'_id': ObjectId(content['id'])})
    if len(content['body']) == 0:
        return jsonify({
            'status': 'error',
            'message': 'Text area cannot be empty.'
        }), 400

    if ticket['resolved']:
        return jsonify({
            'status': 'error',
            'message': 'You cannot reply to a resolved ticket.'
        }), 400
    
    if ticket['author'] == user['username'] or "admin" in user['roles']:
        # add a reply
        try:
            ticket_database.update({'_id': ObjectId(content['id'])}, {
                '$push': {
                    'discussion': {
                        'author': user['username'],
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'body': content['body']
                    }
                }
            })
            return jsonify({'status': 'success'})
        except:
            return jsonify({'status': 'error'}), 400
    return jsonify({'status': 'error'}), 400


@api.route("/api/tickets/update_status", methods=['POST'])
def update_status():
    content = request.json
    user = session['user']
    ticket = ticket_database.find_one({'_id': ObjectId(content['id'])})
    if ticket['author'] == user['username'] or "admin" in user['roles']:

        ticket_database.update({
            '_id': ObjectId(content['id'])
        }, {
            '$set': {
                'resolved': True
            }
        })
        return jsonify({'status': 'success'})

# payment api
def refresh_user_data():
    # used to refresh the user session variable
    user_data = user_database.find_one({'username': session['user']['username']})
    user_data['_id'] = str(user_data['_id'])
    session.pop('user')
    session['user'] = user_data

def add_days_to_subscription(user, days):
    # adds 'days' amount of days to a users 'subscribed_until' variable
    current_subscription_date = datetime.strptime(session['user']['subscribed_until'], '%Y-%m-%d %H:%M:%S')
    if current_subscription_date < datetime.now():
        to_add = (datetime.now() + timedelta(days)).strftime('%Y-%m-%d %H:%M:%S')
    else:
        to_add = (current_subscription_date + timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')

    try:
        user_database.update({
                'username': user['username']
            }, {
            '$set': {
                 'subscribed_until': to_add
            }
        })
        refresh_user_data()

        return jsonify({
             'status': 'success'
        })
    except:
        return jsonify({
             'status': 'error',
             'message': 'unable to add days'
        })

@api.route("/api/payments/stripe", methods=['POST', 'GET'])
@login_required
def payment():
    # todo
    # implement stripe api
    log({
        'username': session['user']['username'],
        'ip': request.remote_addr,
        'message': "Subscription purchased."
    })
    return add_days_to_subscription(session['user'], 30)


@api.route("/api/logs/get", methods=['GET'])
def get_logs():
    logs = logs_database.find({'author': 'admin'})
    return jsonify(logs)