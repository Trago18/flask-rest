"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
import re
import requests
from datetime import timedelta
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, Favorite, Character, Planet
from flask_jwt_extended import create_access_token, current_user, get_jwt_identity, jwt_required, JWTManager

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

@jwt.user_identity_loader
def user_identity_lookup(user):
    return user.id

@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    identity = jwt_data["sub"]
    return User.query.filter_by(id=identity).one_or_none()

@app.before_first_request
def characters_load():
    characters = Character.query.all()
    if not characters:
        response_characters = requests.get("https://swapi.dev/api/people/")
        json_response = response_characters.json()
        for character in json_response['results']:
            character_info=Character(name=character['name'], birth_day=character['birth_year'], gender = character['gender'], height = character['height'], skin_color = character['skin_color'], hair_color = character['hair_color'], eye_color = character['eye_color'])
            db.session.add(character_info)
        db.session.commit()

@app.before_first_request
def planets_load():
    planets = Planet.query.all()
    if not planets:
        response_planets = requests.get("https://swapi.dev/api/planets")
        json_response = response_planets.json()
        for planet in json_response['results']:
            planet_info=Planet(name=planet['name'], climate=planet['climate'], population = planet['population'], terrain = planet['terrain'], rotation_period = planet['rotation_period'], orbital_period = planet['orbital_period'], diameter = planet['diameter'])
            db.session.add(planet_info)
        db.session.commit()

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

    #user = User.query.filter_by(username=user.username).first()

    #favorite = Favorite()
    #favorite.user_id = user.id

    #db.session.add(favorite)
    #db.session.commit()

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

    user = User.query.filter_by(username=username).one_or_none()

    if not user:
        return jsonify({"msg": "Username doesn't exist"}), 400
    if not user.check_password(password):
        return jsonify({"msg": "Invalid password"}), 401
    
    expiration = timedelta(days=1)
    access_token = create_access_token(identity=user, expires_delta=expiration)
    return jsonify('The login has been successful.', {'token':access_token}), 200


# Protect a route with jwt_required, which will kick out requests
# without a valid JWT present.
@app.route("/favorites", methods=["GET"])
@jwt_required()
def get_favorites():

    favorite = Favorite.query.filter_by(user_id=current_user.id).first()
    favorite_serial = favorite.serialize()
    return jsonify(favorite_serial)


@app.route("/favorites", methods=["POST"])
@jwt_required()
def add_favorite(username):
    current_user = get_jwt_identity()

    user = User.query.filter_by(username=username).first()
    if user.id != current_user:
        return jsonify({"msg": "Invalid token"}), 401
    
    favorite = request.get_json()



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
