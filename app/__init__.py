import logging
from logging.handlers import SMTPHandler
from flask import Flask
from flask_bootstrap import Bootstrap
from flask_oauthlib.client import OAuth, OAuthException
from flask_fontawesome import FontAwesome
from flask_pymongo import PyMongo
from flask_caching import Cache
from config import config
import os

bootstrap = Bootstrap()
oauth = OAuth()
mongo = PyMongo()
cache = Cache()
tenant_name = os.getenv('APP_AAD_TENANT')
microsoft = oauth.remote_app(
    'microsoft',
    consumer_key=os.getenv('APP_OAUTH_ID'),
    consumer_secret=os.getenv('APP_OAUTH_SECRET'),
    request_token_params={'scope': 'offline_access email profile openid User.Read'},
    base_url='https://graph.microsoft.com/v1.0/',
    request_token_url=None,
    access_token_method='POST',
    access_token_url=f'https://login.microsoftonline.com/{tenant_name}/oauth2/v2.0/token',
    authorize_url=f'https://login.microsoftonline.com/{tenant_name}/oauth2/v2.0/authorize'
)


def create_app(config_name: str) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    bootstrap.init_app(app)
    oauth.init_app(app)
    mongo.init_app(app)
    FontAwesome(app)

    cache.init_app(app, config={
        'CACHE_TYPE': app.config['CACHE_TYPE'],
        'CACHE_REDIS_URL': app.config['CACHE_REDIS_URL'],
        'CACHE_DEFAULT_TIMEOUT': app.config['CACHE_DEFAULT_TIMEOUT']
    })

    if app.config['SSL_REDIRECT']:
        from flask_sslify import SSLify
        sslify = SSLify(app)

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .api import api as api_blueprint
    app.register_blueprint(api_blueprint)

    return app
