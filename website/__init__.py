from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager
from flask_simplemde import SimpleMDE
from flaskext.markdown import Markdown
from pyngrok import ngrok

db = SQLAlchemy()
DB_NAME = "database.db"


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = b'\xdeZd\xc3\x12\x07\xa5tN\x1efm\xe1\x19\x7f@'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    app.config["SIMPLEMDE_JS_IIFE"] = True
    app.config["SIMPLEMDE_USE_CDN"] = True
    app.config["SESSION_COOKIE_SECURE"] = True
    app.config["REMEMBER_COOKIE_SECURE"] = True
    app.config["REMEMBER_COOKIE_HTTPONLY"] = True
    db.init_app(app)
    SimpleMDE(app)
    Markdown(app, extensions=["nl2br", "fenced_code"])
    #https_tunnel = ngrok.connect(5000, bind_tls=True)
    #print(https_tunnel)

    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    from .models import User, Note

    create_database(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    return app


def create_database(app):
    if not path.exists('website/' + DB_NAME):
        db.create_all(app=app)
        print('Created Database!')
