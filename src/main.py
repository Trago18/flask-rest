"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
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

@app.route('/register', methods=['POST'])
def create_user():
    body = request.get_json()

    if body is None:
        return "The request body is null", 400
    if 'username' not in body:
        return "Empty username", 400
    if 'email' not in body:
        return "Empty email", 400
    if 'password' not in body:
        return "Empty password", 400

    user = User()
    user.username = body['username']
    user.email = body['email']
    user.password = body['password']

    db.session.add(user)
    db.session.commit()

    user = User.query.filter_by(username=user.username).first()

    favorite = Favorite()
    favorite.user_id = user.id

    db.session.add(favorite)
    db.session.commit()

    response_body = {
        "msg": "Added user"
    }

    return jsonify(response_body), 200

@app.route("/login", methods=["POST"])
def login():
    username = request.json.get("username", None)
    password = request.json.get("password", None)

    if username is None and password is None:
        return jsonify({"msg": "Empty username and password"}), 400
    if username is None:
        return jsonify({"msg": "Empty username"}), 400
    if password is None:
        return jsonify({"msg": "Empty password"}), 400

    user = User.query.filter_by(username=username, password=password).first()
    if user is None:
        return jsonify({"msg": "Bad username or password"}), 401
    
    access_token = create_access_token(identity=user.id)
    return jsonify(access_token=access_token)


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
