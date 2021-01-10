import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you_will_never_guess'

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True

    APP_OAUTH_ID = os.environ.get('APP_OAUTH_ID')
    APP_OAUTH_SECRET = os.environ.get('APP_OAUTH_SECRET')
    APP_OAUTH_TENANT = os.environ.get('APP_AAD_TENANT')

    BASE_GRAPH_API_URL = 'https://graph.microsoft.com/v1.0/'

    GOOGLE_CREDENTIALS = os.path.join(basedir, 'credentials.json')
    SPREADSHEET_ID = os.environ.get('SPREADSHEET_ID')

    ICTIS_API_URL = os.environ.get('ICTIS_API_URL')
    ICTIS_API_LOGIN = os.environ.get('ICTIS_API_LOGIN')
    ICTIS_API_PASSWORD = os.environ.get('ICTIS_API_PASSWORD')

    MONGO_URI = os.environ.get('MONGO_URI') or os.environ.get('DATABASE_URI')
    MONGO_DBNAME = os.environ.get('MONGO_DBNAME')

    STUDENT_GRADE_CHECK_ENABLED = os.environ.get('STUDENT_GRADE_CHECK_ENABLED') or False
    STUDENT_GRADE_MAX = os.environ.get('STUDENT_GRADE_MAX') or 1



    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    SSL_REDIRECT = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'data-dev.sqlite')


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        'sqlite://'
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'data.sqlite')

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)


class HerokuConfig(ProductionConfig):
    SSL_REDIRECT = True if os.environ.get('DYNO') else False

    @classmethod
    def init_app(cls, app):
        ProductionConfig.init_app(app)

        # handle reverse proxy server headers
        from werkzeug.middleware.proxy_fix import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app)

        # log to stderr
        import logging
        from logging import StreamHandler
        file_handler = StreamHandler()
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'heroku': HerokuConfig,

    'default': DevelopmentConfig
}
