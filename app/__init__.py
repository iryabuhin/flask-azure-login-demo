from flask import Flask
from flask_bootstrap import Bootstrap
from flask_oauthlib.client import OAuth, OAuthException
from config import config
import os

bootstrap = Bootstrap()
oauth = OAuth()

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

def create_app(config_name: str):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    bootstrap.init_app(app)
    oauth.init_app(app)

    if app.config['SSL_REDIRECT']:
        from flask_sslify import SSLify
        sslify = SSLify(app)

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint, url_prefix='')

    return app
