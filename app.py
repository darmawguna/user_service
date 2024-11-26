
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from api.user.endpoints import users_endpoints
from flasgger import Swagger
import redis


# Load environment variables from the .env file
load_dotenv()

app = Flask(__name__)

CORS(app)
Swagger(app)

# Koneksi ke Redis yang berjalan di localhost (port 6379)
r = redis.StrictRedis(host='localhost', port=6379, db=0)


# register the blueprint
app.register_blueprint(users_endpoints, url_prefix='/api/v1/users')


if __name__ == '__main__':
    app.run(debug=True)
