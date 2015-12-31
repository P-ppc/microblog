import os

basedir = os.path.abspath(os.path.dirname(__file__))

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_respository')
SQLALCHEMY_TRACK_MODIFICATIONS = False

CSRF_ENABLED = True
SECRET_KEY = 'you-will-never-guess'

# pagination
POSTS_PER_PAGE = 3

MAX_SEARCH_RESULTS = 50

UPLOAD_FOLDER = os.path.join(basedir, 'app/static/upload')
UPLOAD_LOCAL_FOLDER = 'static/upload'
HEAD_FOLDER = 'app/static/head'
HEAD_LOCAL_FOLDER = '/static/head'
