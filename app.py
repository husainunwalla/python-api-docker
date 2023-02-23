from flask import Flask, request, jsonify, session
from pymongo import MongoClient
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'my_secret_key'

client = MongoClient('mongodb://localhost:27017/')
db = client['my_database']
users_collection = db['users']

@app.route('/signup', methods=['POST'])
def signup():
    username = request.json.get('username')
    password = request.json.get('password')
    if not username or not password:
        return jsonify({'message': 'Missing username or password'}), 400

    # Check if the user already exists
    if users_collection.find_one({'username': username}):
        return jsonify({'message': 'User already exists'}), 400

    # Hash the password and insert the new user in the database
    hashed_password = generate_password_hash(password)
    user_id = users_collection.insert_one({'username': username, 'password': hashed_password}).inserted_id

    # Return a success message and the user ID
    return jsonify({'message': 'User created', 'user_id': str(user_id)}), 201

@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username')
    password = request.json.get('password')
    if not username or not password:
        return jsonify({'message': 'Missing username or password'}), 400

    # Check if the user exists and the password is correct
    user = users_collection.find_one({'username': username})
    if user and check_password_hash(user['password'], password):
        # Store the user ID in the session
        session['user_id'] = str(user['_id'])
        return jsonify({'message': 'Login successful!'})
    else:
        return jsonify({'message': 'Invalid username or password'}), 401

if __name__ == '__main__':
    app.run(debug=True)
