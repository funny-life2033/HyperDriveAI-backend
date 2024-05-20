# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from datetime import datetime, timezone, timedelta

from functools import wraps

from flask import request
from flask_restx import Api, Resource, fields

import jwt

from .models import db, Users, JWTTokenBlocklist, LLModel, Bot, ChatHistory, ChatRoom
from .config import BaseConfig

from llm.llm import generate_answer

import os
from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import GoogleDriveLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

embeddings = OpenAIEmbeddings()
rest_api = Api(version="1.0", title="Users API")


"""
    Flask-Restx models for api request and response data
"""

signup_model = rest_api.model(
    "SignUpModel",
    {
        "username": fields.String(required=True, min_length=2, max_length=32),
        "email": fields.String(required=True, min_length=4, max_length=64),
        "password": fields.String(required=True, min_length=4, max_length=16),
    },
)

login_model = rest_api.model(
    "LoginModel",
    {
        "email": fields.String(required=True, min_length=4, max_length=64),
        "password": fields.String(required=True, min_length=4, max_length=16),
    },
)

user_edit_model = rest_api.model(
    "UserEditModel",
    {
        "userID": fields.String(required=True, min_length=1, max_length=32),
        "username": fields.String(required=True, min_length=2, max_length=32),
        "email": fields.String(required=True, min_length=4, max_length=64),
    },
)

llmodel_create_model = rest_api.model(
    "LLModelCreateModel",
    {
        "name": fields.String(max_length=32, required=True),
        "icon": fields.String(),
        "model": fields.String(),
        "url": fields.String(),
        "popular": fields.Boolean(),
        "offical": fields.Boolean(),
        "limited": fields.Boolean(),
    },
)

"""
   Helper function for JWT token required
"""


def token_required(f):

    @wraps(f)
    def decorator(*args, **kwargs):

        token = None

        if "authorization" in request.headers:
            token = request.headers["authorization"]
            # print("token: ", token)

        if not token:
            print("Valid JWT token is missing")
            return {"success": False, "msg": "Valid JWT token is missing"}, 400

        try:
            data = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=["HS256"])
            current_user = Users.get_by_email(data["email"])

            if not current_user:
                return {
                    "success": False,
                    "msg": "Sorry. Wrong auth token. This user does not exist.",
                }, 400

            token_expired = JWTTokenBlocklist.get_by_jwt_token(token)

            if token_expired is not None:
                print("Token revoked.")
                return {"success": False, "msg": "Token revoked."}, 400

            if not current_user.check_jwt_auth_active():
                print("Token expired.")
                return {"success": False, "msg": "Token expired."}, 400

        except:
            print("Token is invalid")
            return {"success": False, "msg": "Token is invalid"}, 400

        return f(current_user, *args, **kwargs)

    return decorator


"""
    Flask-Restx routes
"""


@rest_api.route("/api/users/register")
class Register(Resource):
    """
    Creates a new user by taking 'signup_model' input
    """

    @rest_api.expect(signup_model, validate=True)
    def post(self):

        req_data = request.get_json()

        _username = req_data.get("username")
        _email = req_data.get("email")
        _password = req_data.get("password")

        user_exists = Users.get_by_email(_email)
        if user_exists:
            return {"success": False, "msg": "Email already taken"}, 400

        new_user = Users(username=_username, email=_email)

        new_user.set_password(_password)
        new_user.save()

        return {
            "success": True,
            "userID": str(new_user.id),
            "msg": "The user was successfully registered",
        }, 200


@rest_api.route("/api/users/login")
class Login(Resource):
    """
    Login user by taking 'login_model' input and return JWT token
    """

    @rest_api.expect(login_model, validate=True)
    def post(self):

        req_data = request.get_json()

        _email = req_data.get("email")
        _password = req_data.get("password")

        print(_email, _password)

        user_exists = Users.get_by_email(_email)

        if not user_exists:
            return {"success": False, "msg": "This email does not exist."}, 400

        if not user_exists.check_password(_password):
            return {"success": False, "msg": "Wrong credentials."}, 400

        # create access token uwing JWT
        token = jwt.encode(
            {"email": _email, "exp": datetime.utcnow() + timedelta(days=1)},
            BaseConfig.SECRET_KEY,
        )

        user_exists.set_jwt_auth_active(True)
        user_exists.save()

        return {"success": True, "token": token, "user": user_exists.toJSON()}, 200


@rest_api.route("/api/users/edit")
class EditUser(Resource):
    """
    Edits User's username or password or both using 'user_edit_model' input
    """

    @rest_api.expect(user_edit_model)
    @token_required
    def post(self, current_user):

        req_data = request.get_json()

        _new_username = req_data.get("username")
        _new_email = req_data.get("email")

        if _new_username:
            self.update_username(_new_username)

        if _new_email:
            self.update_email(_new_email)

        self.save()

        return {"success": True}, 200


@rest_api.route("/api/users/checkSession")
class checkSession(Resource):
    """
    Checks an existing JWT Token for validity
    """

    @token_required
    def post(self, current_user):

        if self:
            return {"success": True, "msg": "User is logged on with valid token"}, 200
        else:
            return {"success": False, "msg": "User is not logged on"}, 400


@rest_api.route("/api/users/logout")
class LogoutUser(Resource):
    """
    Logs out User using 'logout_model' input
    """

    @token_required
    def post(self, current_user):

        _jwt_token = request.headers["authorization"]

        jwt_block = JWTTokenBlocklist(
            jwt_token=_jwt_token, created_at=datetime.now(timezone.utc)
        )
        jwt_block.save()

        self.set_jwt_auth_active(False)
        self.save()

        return {"success": True}, 200


# Models
@rest_api.route("/api/models")
class ListModels(Resource):
    @token_required
    def get(self, current_user):
        models = LLModel.objects
        return [model.toJSON() for model in models], 200

    @rest_api.expect(llmodel_create_model, validate=True)
    @token_required
    def post(self, current_user):
        req_data = request.get_json()

        _name = req_data.get("name")
        _model = req_data.get("model")
        _url = req_data.get("url")

        new_model = LLModel(name=_name, model=_model, url=_url)
        new_model.save()
        return {"success": True}, 200


# Bots
@rest_api.route("/api/bots")
class Bots(Resource):
    @token_required
    def get(self, current_user):
        print(current_user)
        bots = Bot.objects
        return [bot.toJSON() for bot in bots], 200

    @token_required
    def post(self, current_user):
        req_data = request.get_json()

        _base = req_data.get("model")
        _name = req_data.get("name")
        _icon = req_data.get("icon")
        _behavior = req_data.get("behavior")
        _greeting = req_data.get("greeting")
        _files = req_data.get("files")

        model = LLModel.objects(id=_base).first()

        new_bot = Bot(
            base=model, name=_name, icon=_icon, behavior=_behavior, greeting=_greeting
        )

        new_bot.save()

        loader = GoogleDriveLoader(
            file_ids=[file["id"] for file in _files],
            # file_loader_cls=UnstructuredFileIOLoader,
        )
        data = loader.load()

        text_splitter = RecursiveCharacterTextSplitter()
        docs = text_splitter.split_documents(data)

        # pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        # pc.create_index(
        #     name=f"{new_bot.id}",
        #     dimension=1536,
        #     metric="cosine",
        #     spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        # )

        PineconeVectorStore.from_documents(
            documents=docs, index_name="bot", embedding=embeddings
        )

        return new_bot.toJSON(), 200


# Rooms
@rest_api.route("/api/rooms/")
class Chats(Resource):
    @token_required
    def get(current_user, self):
        rooms = ChatRoom.objects(user=current_user)
        return [room.toJSON() for room in rooms], 200

    @token_required
    def post(current_user, self):
        req_data = request.get_json()
        bot_id = req_data.get("bot_id")
        bot = Bot.objects(id=bot_id).first()
        new_room = ChatRoom(bot=bot, user=current_user)
        new_room.save()
        return new_room.toJSON(), 200


# Chats
@rest_api.route("/api/chats/<room_id>")
class Chats(Resource):
    @token_required
    def get(current_user, self, room_id):
        room = ChatRoom.objects(id=room_id).first()
        history = ChatHistory.objects(room=room)
        return [room.toJSON() for room in history], 200

    @token_required
    def post(current_user, self, room_id):
        req_data = request.get_json()

        room = ChatRoom.objects(id=room_id).first()
        question = req_data.get("question")
        answer = generate_answer(room, question)
        new_chat = ChatHistory(room=room, question=question, answer=answer)
        new_chat.save()
        return new_chat.toJSON()
