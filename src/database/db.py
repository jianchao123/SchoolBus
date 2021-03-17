# coding:utf-8
from flask_sqlalchemy import SQLAlchemy

session_options = {
    'autocommit': True
}
db = SQLAlchemy(session_options=session_options)

