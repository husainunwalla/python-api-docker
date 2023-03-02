import datetime

class User:
    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.password = password
        self.last_logout_all_time = str(datetime.datetime.utcnow().timestamp())
