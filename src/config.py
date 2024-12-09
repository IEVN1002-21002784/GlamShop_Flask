from flask_sqlalchemy import SQLAlchemy

class DevelopmentConfig:
    DEBUG = True
    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = ''
    MYSQL_DB = 'glamshop'
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:@localhost/glamshop'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

db = SQLAlchemy()  # Inicializamos la instancia de SQLAlchemy, pero sin la aplicación todavía.

config = {
    'development': DevelopmentConfig
}
