# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from datetime import datetime

from werkzeug.security import generate_password_hash, check_password_hash
from flask_mongoengine import MongoEngine

db = MongoEngine() 

class Users(db.Document):
    username = db.StringField(max_length=32, required=True)
    email = db.StringField(required=True)
    password = db.StringField()
    jwt_auth_active = db.BooleanField()
    date_joined = db.DateTimeField(default=datetime.utcnow)

    def __repr__(self):
        return f"User {self.username}"

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def update_email(self, new_email):
        self.email = new_email

    def update_username(self, new_username):
        self.username = new_username

    def check_jwt_auth_active(self):
        return self.jwt_auth_active

    def set_jwt_auth_active(self, set_status):
        self.jwt_auth_active = set_status

    @classmethod
    def get_by_id(cls, id):
        return cls.query.get_or_404(id)

    @classmethod
    def get_by_email(cls, email):
        return cls.objects(email=email).first()

    def toDICT(self):

        cls_dict = {}
        cls_dict['_id'] = str(self.id)
        cls_dict['username'] = self.username
        cls_dict['email'] = self.email

        return cls_dict

    def toJSON(self):

        return self.toDICT()


class JWTTokenBlocklist(db.Document):
    jwt_token = db.StringField(required=True)
    created_at = db.DateTimeField(required=True)

    def __repr__(self):
        return f"Expired Token: {self.jwt_token}"

    @classmethod
    def get_by_jwt_token(cls, jwt_token):
        return cls.objects(jwt_token=jwt_token).first()

class LLModel(db.Document):
    name = db.StringField(max_length=32, required=True)
    model = db.StringField()
    url = db.StringField()

    def toDICT(self):
        cls_dict = {}
        cls_dict['_id'] = str(self.id)
        cls_dict['name'] = self.name
        cls_dict['model'] = self.model
        cls_dict['url'] = self.url
        return cls_dict

    def toJSON(self):
        return self.toDICT()

class Bot(db.Document):
    base = db.ReferenceField(LLModel)
    name = db.StringField()
    icon = db.StringField()
    behavior = db.StringField()
    greeting = db.StringField()

    def toDICT(self):
        cls_dict = {}
        cls_dict['_id'] = str(self.id)
        cls_dict['base'] = self.base.toJSON()
        cls_dict['name'] = self.name
        cls_dict['icon'] = self.icon
        cls_dict['behavior'] = self.behavior
        cls_dict['greeting'] = self.greeting
        return cls_dict

    def toJSON(self):
        return self.toDICT()

class ChatRoom(db.Document):
    bot = db.ReferenceField(Bot)
    user = db.ReferenceField(Users)
    created_at = db.DateTimeField(default=datetime.utcnow)
    updated_at = db.DateTimeField(default=datetime.utcnow)

    def toDICT(self):
        cls_dict = {}
        cls_dict['_id'] = str(self.id)
        cls_dict['bot'] = self.bot.toJSON()
        cls_dict['user'] = self.user.toJSON()
        history = ChatHistory.objects(room=self).order_by('-updated_at')
        if len(history) > 0:
            cls_dict['last_message'] = history.first().answer
        else:
            cls_dict['last_message'] = ''
        cls_dict['created_at'] = self.created_at.isoformat()
        cls_dict['updated_at'] = self.updated_at.isoformat()
        return cls_dict

    def toJSON(self):
        return self.toDICT()

class ChatHistory(db.Document):
    room = db.ReferenceField(ChatRoom)
    question = db.StringField()
    answer = db.StringField()
    timestamp = db.DateTimeField(default=datetime.utcnow)

    def toDICT(self):
        cls_dict = {}
        cls_dict['_id'] = str(self.id)
        cls_dict['question'] = self.question
        cls_dict['answer'] = self.answer
        cls_dict['timestamp'] = self.timestamp.isoformat()
        return cls_dict

    def toJSON(self):
        return self.toDICT()
