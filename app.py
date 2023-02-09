from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    conn = sqlite3.connect('login.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (username text, password text)
    ''')
    c.execute('''
        INSERT INTO users (username, password)
        VALUES (?, ?)
    ''', (username, password))
    conn.commit()
    conn.close()

    return jsonify({'message': 'Login information saved successfully to sql'})

if __name__ == '__main__':
    app.run(debug=True)
