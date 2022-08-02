from app import app, request
from app import db, Users, Posts, Notification, CommentsH, CommentsS, Messages
from flask_admin import Admin
from flask_admin.contrib.peewee import ModelView

admin = Admin(app)


