from flask import Flask, request, jsonify, session, request, make_response
from pymongo import MongoClient
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import os
import datetime
from functools import wraps
import json
from typing import List

app = Flask(__name__)

# get mongodb_url from the aws environment variables
mongodb_url = os.environ.get('MONGODB_URL')
secret_key = os.environ.get('SECRET_KEY')
app.secret_key =  secret_key
mongo_client = MongoClient(mongodb_url)

'''Local MongoDB testing client
Use this if you are testing locally and do not have an AWS account
Uncomment the line below and comment out the line above
'''
#mongo_client = MongoClient('mongodb://localhost:27017/')

db = mongo_client.my_database
users_db = db['users']
posts_db = db['posts']
recipes_collection = db['recipes']
dietplans_db = db['diet_plans']

# define error handlers
@app.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad Request', 'message': str(error)}), 400

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not Found', 'message': str(error)}), 404

@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({'error': 'Internal Server Error', 'message': str(error)}), 500

# User Model
class User:
    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.password = password
        self.last_logout_all_time = str(datetime.datetime.utcnow().timestamp())

# Post Model
class Post:
    def __init__(self, user_id, title, content):
        self.user_id = user_id
        self.title = title
        self.content = content
        self.creation_time = str(datetime.datetime.utcnow().timestamp())

class Meal:
    def __init__(self, name, description, ingredients, instructions):
        self.name = name
        self.description = description
        # self.ingredients = ingredients
        # self.instructions = instructions

    def to_dict(self):
        return {
            'name': self.name,
            'description': self.description,
            'ingredients': self.ingredients,
            'instructions': self.instructions,
        }
    
class DietPlanDay:
    def __init__(self, meals):
        self.meals = meals

    def to_dict(self):
        return {
            'meals': self.meals,
        }
    
class DietPlan:
    def __init__(self, name, description, image_url, user_id,daydietplans: List[DietPlanDay]):
        self.name = name
        self.description = description
        self.image_url = image_url
        self.user_id = user_id
        self.daydietplans = daydietplans
        self.creation_time = str(datetime.datetime.utcnow().timestamp())

    def to_dict(self):
        return {
            'name': self.name,
            'description': self.description,
            'image_url': self.image_url,
            'user_id': self.user_id,
            'daydietplans':self.daydietplans,
        }


# Decorator to check for token
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # variable of token
        token = None

        # checks if token is in header
        if 'Authorization' in request.headers:
            # checks if token is in header
            token = request.headers['Authorization'].split()[1]

        # if no token, return error
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            # decode data from token
            data = jwt.decode(token, secret_key, algorithms=["HS256"])
            # get last_logout_all_time of user from mongodb
            last_logout_all_time = db.users.find_one({'_id': ObjectId(data['id'])})["last_logout_all_time"]
            last_logout_all_time = float(last_logout_all_time)
            # get creation time of decoded token
            token_creation_time = float(data['token_creation_time'])
            # if the token was created logout all command, then token is expired
            if token_creation_time < last_logout_all_time:
                return jsonify({
                    'message': 'Token has expired!',}), 401
        except:
            return jsonify({'message': 'Token is invalid!'}), 401
        
        # get user data from id
        current_user = db.users.find_one({'_id': ObjectId(data['id'])})
        # return jsonify({'test': str(current_user)})
        return f(current_user, *args, **kwargs)

    return decorated

# sign up user
@app.route('/signup', methods=['POST'])
def signup():
    # get username, email, and password from json
    username = request.json.get('username')
    password = request.json.get('password')
    email = request.json['email']    

    # if none of these are in the json, return error
    if not (email and username and password):
        return jsonify({'message': 'Missing username, email, or password'}), 400

    # Check if the email already exists
    if users_db.find_one({'email': email}):
        return jsonify({'message': 'Email already exists'}), 400

    # Check if the username already exists
    if users_db.find_one({'username': username}):
        return jsonify({'message': 'Username already exists'}), 400
    
    # Hash the password and insert the new user in the database
    hashed_password = generate_password_hash(password)
    new_user = User(username, email, hashed_password)
    user_id = users_db.insert_one(new_user.__dict__).inserted_id

    # Return a success message and the user ID
    return jsonify({'message': 'User created','user_id': str(user_id)})

# user login and returns token
@app.route('/login', methods=['POST'])
def login():
    # get email and password from json
    email = request.json.get('email')
    password = request.json.get('password')

    # if none of these are in the json, return error
    if not (email and password):
        return jsonify({'message': 'Missing email or password'}), 400

    # retrieve user from collection
    user = db.users.find_one({'email': email})

    # if no email, return error
    if not user:
        return jsonify({'message': 'Invalid email'}), 401    

    # Check if the password is correct
    if check_password_hash(user['password'], password):
        # Store the user ID in the session
        session['user_id'] = str(user['_id'])
        # encode to create token
        token = jwt.encode({'id': str(user['_id']), 'token_creation_time': str(datetime.datetime.utcnow().timestamp())}, secret_key, algorithm="HS256")
        return jsonify({'message': 'Login successful!','token': str(token)})
    else:
        return jsonify({'message': 'Invalid password'}), 401

# user logout and expires previous tokens
@app.route('/logout-all', methods=['POST'])
@token_required
def logout_all(current_user):
    # updates last_logout_all time to now
    # therefore, all tokens will expire
    db.users.update_one({'_id': ObjectId(current_user['_id'])}, {'$set': {'last_logout_all_time': str(datetime.datetime.utcnow().timestamp())}})
    return jsonify({'message': 'Logged out from all devices!'})

# # protected API Endpoint
# @app.route('/protected', methods=['GET'])
# @token_required
# def protected(current_user):
#     return jsonify({'message': 'This is a protected API endpoint.', 'current_user': current_user})

# CRUD functions for posts
# get all posts
@app.route('/posts/all', methods=['GET'])
def get_posts():
    # create post array
    posts = []
    # append each post from db to array
    for post in posts_db.find():
        post['_id'] = str(post['_id'])
        posts.append(post)    
    return jsonify({'posts': posts})

# get all posts from user
@app.route('/posts/user', methods=['GET'])
def get_posts_user():
    # get argument from query
    args = request.args
    user_id = args.get('user_id')
    # create post array
    posts = []
    # append each post from db to array
    for post in posts_db.find({'user_id':user_id}):
        post['_id'] = str(post['_id'])
        posts.append(post)    
    return jsonify({'posts': posts})

# get post based on id
@app.route('/posts', methods=['GET'])
def get_post():
    # get argument from query
    args = request.args
    post_id = args.get('post_id')

    # check if id is retrieved
    if post_id == None or post_id == "":
        raise ValueError('post_id is missing')

    # retrieve post
    post = posts_db.find_one({'_id': ObjectId(post_id)})
    # check if post was retrieved
    if post:
        # convert ObjectId to string
        post["_id"] = str(post["_id"])
        # return post
        return jsonify(post)
    else:
        raise ValueError('Post not found')

# create post
@app.route('/posts', methods=['POST'])
@token_required
def create_post(current_user):
    # ensure that all values are received
    if 'title' not in request.json or 'content' not in request.json:
        raise ValueError('Title or Content are missing')
    
    # get values
    post = request.get_json()
    # convert object id to string as well
    user_id = str(current_user['_id'])

    # create post object
    new_post = Post(user_id, post['title'], post['content'])
    # create post object and get new id
    post_id = posts_db.insert_one(new_post.__dict__).inserted_id
        
    # retrieve post
    new_post = posts_db.find_one({'_id': post_id})

    # convert ObjectId to string
    new_post["_id"] = str(new_post["_id"])

    # return post
    return jsonify(new_post)

# update post
@app.route('/posts', methods=['PUT'])
@token_required
def update_post(current_user):
    # get argument from query
    args = request.args
    post_id = args.get('post_id')
    # check if id is retrieved
    if post_id == None or post_id == "":
        raise ValueError('post_id is missing')

    # ensure that all values are received
    if 'title' not in request.json or 'content' not in request.json:
        raise ValueError('Title or Content are missing')
    
    # convert object id to string as well
    user_id = str(current_user['_id'])

    # get values
    post = request.json

    # get values to update
    title = post.get('title')
    content = post.get('content')

    # get result from updating post
    result = posts_db.update_one(
        {'_id': ObjectId(post_id),'user_id':user_id}, 
        {'$set': {'title': title, 'content': content, 'creation_time': datetime.datetime.utcnow().timestamp()}}
    )
    if result.modified_count == 1:
        return jsonify({'message': 'Post updated successfully!'})
    else:
        raise ValueError('Post not found')

# delete post
@app.route('/posts', methods=['DELETE'])
@token_required
def delete_post(current_user):
    # get argument from query
    args = request.args
    post_id = args.get('post_id')
    # check if id is retrieved
    if post_id == None or post_id == "":
        raise ValueError('post_id is missing') 
    # convert object id to string as well
    user_id = str(current_user['_id'])   
    # delete a post
    result = posts_db.delete_one({'_id': ObjectId(post_id), 'user_id':user_id})
    # get result from deleting post
    if result.deleted_count == 1:
        return jsonify({'message': 'Post deleted successfully!'})
    else:
        raise ValueError('Post not found')

# create diet plan
@app.route('/dietplans', methods=['POST'])
@token_required
def create_dietplan(current_user):
    # parameters of string
    parameters = ['name','description','image_url','daydietplans']
    # ensure each value is in json
    for p in parameters:
        if not p in request.json:
            raise ValueError('{} parameter is missing'.format(p))
    
    # get the values
    name = request.json['name']
    description = request.json['description']
    image_url = request.json['image_url']
    user_id = str(current_user['_id'])    
    daydietplans = request.json['daydietplans']
    # create diet plan value
    new_dietplan = DietPlan(name, description, image_url, user_id,daydietplans)
    # create diet plan
    dietplan_id = dietplans_db.insert_one(new_dietplan.__dict__).inserted_id
    # retrieve diet plan
    new_dietplan = dietplans_db.find_one({'_id': dietplan_id})
    # convert ObjectId to string
    new_dietplan["_id"] = str(new_dietplan["_id"])    
    
    return jsonify(new_dietplan)

# update diet plan
@app.route('/dietplans', methods=['GET'])
def get_dietplan():
    # get argument from query
    args = request.args
    dietplan_id = args.get('dietplan_id')

    # check if id is retrieved
    if dietplan_id == None or dietplan_id == "":
        raise ValueError('dietplan_id is missing')

    # retrieve diet plan
    dietplan = dietplans_db.find_one({'_id': ObjectId(dietplan_id)})

    # check if post was retrieved
    if dietplan:
        # convert ObjectId to string
        dietplan["_id"] = str(dietplan["_id"])
        # return post
        return jsonify(dietplan)
    else:
        raise ValueError('Post not found')

# update dietplan
@app.route('/dietplans', methods=['PUT'])
@token_required
def update_dietplan(current_user):
    # get argument from query
    args = request.args
    dietplan_id = args.get('dietplan_id')
    # check if id is retrieved
    if dietplan_id == None or dietplan_id == "":
        raise ValueError('dietplan_id is missing')

    # parameters of string
    parameters = ['name','description','image_url','daydietplans']
    # ensure each value is in json
    for p in parameters:
        if not p in request.json:
            raise ValueError('{} parameter is missing'.format(p))

    name = request.json['name']
    description = request.json['description']
    image_url = request.json['image_url']
    user_id = str(current_user['_id'])    
    daydietplans = request.json['daydietplans']

    result = dietplans_db.update_one({'_id': ObjectId(dietplan_id),'user_id':user_id}, {'$set': {
        'name': name,
        'description': description,
        'image_url':image_url,
        'daydietplans': daydietplans,        
        'creation_time': datetime.datetime.utcnow().timestamp()
    }})

    if result.modified_count == 1:
        return jsonify({'message': 'Diet plan updated successfully!'})
    else:
        raise ValueError('Post not found')

# delete dietplan
@app.route('/dietplans', methods=['DELETE'])
@token_required
def delete_dietplan(current_user):
    # get argument from query
    args = request.args
    dietplan_id = args.get('dietplan_id')
    # check if id is retrieved
    if dietplan_id == None or dietplan_id == "":
        raise ValueError('dietplan_id is missing') 
    # convert object id to string as well
    user_id = str(current_user['_id'])  
    # delete a post 
    result = dietplans_db.delete_one({'_id': ObjectId(dietplan_id), 'user_id':user_id})
    # get result from deleting post
    if result.deleted_count == 1:
        return jsonify({'message': 'Diet plan deleted successfully!'})
    else:
        raise ValueError('Diet plan not found')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')

    #app.run for local testing
    # app.run(debug=True)