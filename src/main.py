"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
import re
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, Favorite, Character, Planet

from flask_jwt_extended import create_access_token
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import jwt_required
from flask_jwt_extended import JWTManager

app = Flask(__name__)
app.url_map.strict_slashes = False
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DB_CONNECTION_STRING')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config["JWT_SECRET_KEY"] = "super-secret"  # Change this!
jwt = JWTManager(app)
MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    return generate_sitemap(app)

@app.route('/signup', methods=['POST'])
def create_user():

    request_body = request.get_json()
    error_messages=[]

    if 'username' not in request_body:
        error_messages.append({"msg":"Username required"})
    if 'email' not in request_body:
        error_messages.append({"msg":"Email required"})
    if 'password' not in request_body:
        error_messages.append({"msg":"Password required"})
    if len(error_messages) > 0:
        return jsonify(error_messages), 400       

    if not re.match('^(\w|\.|\_|\-)+[@](\w|\_|\-|\.)+[.]\w{2,8}$', request_body['email']):
        error_messages.append({'msg':'Enter a valid email format'})
    if not re.match('^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[\W])[^\n\t]{8,20}$', request_body['password']):
        error_messages.append({'msg':'Password must contain the following: a lowercase letter, a capital letter, a number, one special character and minimum 8 characters'})
    if len(error_messages) > 0:
        return jsonify(error_messages), 400

    username = User.query.filter_by(username=request_body['username']).first()
    email = User.query.filter_by(email=request_body['email']).first()

    if username:
        error_messages.append({'msg': 'This username already exists. Check your username'})
    if email:
        error_messages.append({'msg': 'This email already exists. Check your email'})
    if len(error_messages) > 0:
        return jsonify(error_messages), 400

    user = User()
    user.username = request_body['username']
    user.email = request_body['email']
    user.password = request_body['password']
    user.is_active=True

    db.session.add(user)
    db.session.commit()

    # user = User.query.filter_by(username=user.username).first()

    # favorite = Favorite()
    # favorite.user_id = user.id

    # db.session.add(favorite)
    # db.session.commit()

    response_body = {
        "msg": "The user was successfully created."
    }

    return jsonify(response_body), 200


@app.route("/login", methods=["POST"])
def login():
    username = request.json.get("username", None)
    password = request.json.get("password", None)
    error_messages=[]
    
    if username is None:
        error_messages.append({"msg": "Username is required"})
    if password is None:
        error_messages.append({"msg": "Password is required"})
    if len(error_messages) > 0:
        return jsonify(error_messages), 400

    user = User.query.filter_by(username=username).first()
    if user is None:
        return jsonify({"msg": "Bad username or password"}), 401
    
    expiration = datetime.timedelta(days=1)
    access_token = create_access_token(identity=user.id, expires_delta=expiration)
    return jsonify('The login has been successful.', {'token':access_token, 'user_id':user.id}), 200


# Protect a route with jwt_required, which will kick out requests
# without a valid JWT present.
@app.route("/favorite/<username>", methods=["GET"])
@jwt_required()
def protected(username):
    current_user = get_jwt_identity()

    user = User.query.filter_by(username=username).first()
    if user.id != current_user:
        return jsonify({"msg": "Invalid token"}), 401
    favorite = Favorite.query.filter_by(id=user.id).first()

    return jsonify(characters=favorite.character, planets=favorite.planet), 200


### Agregar PUT de favoritos ###


@app.route("/character/<int:id>", methods=["GET"])
def get_character(id):

    character = Character.query.filter_by(id=id).all()
    character = list(map(lambda x: x.serialize(), character))

    return jsonify(character), 200


@app.route("/planet/<int:id>", methods=["GET"])
def get_planet(id):

    planet = Planet.query.filter_by(id=id).all()
    planet = list(map(lambda x: x.serialize(), planet))

    return jsonify(planet), 200


# this only runs if `$ python src/main.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
