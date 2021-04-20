from flask import Flask, redirect, render_template, session
from auth.middleware import login_required
from auth.controllers import auth
from api.controllers import api
from config import Config
import datetime


def register_blueprints(app):
    app.register_blueprint(auth)
    app.register_blueprint(api)


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = Config.secret_key
    app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

    register_blueprints(app)

    @app.route('/')
    def index():
        return redirect('/dashboard')

    @app.route('/dashboard')
    @login_required
    def dashboard():
        return render_template('panel.html', datetime=datetime.datetime)

    return app


if __name__ == '__main__':
    create_app().run()