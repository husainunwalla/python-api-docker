# API for COEN 241 Cloud Computing Project
## python-api-docker

## Docker Commands for running both Flask and MongoDB locally:
* The following commands download the official MongoDB image, create a network so that both containers can communicate, build the Flask docker image, and run both containers.
```
cd python-api
docker pull mongo
docker build -t my-flask-app .
docker network create my-network
docker run -d --name mongodb --network my-network mongo
docker run -d -p 5000:5000 --name myapp-container -e MONGODB_URL=mongodb://mongodb:27017/ -e SECRET_KEY=1234 --network my-network my-flask-app:latest
```

## Postman Setup:
1. If you plan to run the containers locally, set the "address" variable to "localhost"
### Special Instructions:
* To get a token, use the following api route: /login
* The following api routes require a token: 
    * log out of all devices
    * create, update, and delete posts, dietplans, and so on
* To include newly received token for a CRUD api:
    1. Go to the Auth tab
    2. For 'Type', select 'Bearer Token'
    3. Enter the token with out quotes

