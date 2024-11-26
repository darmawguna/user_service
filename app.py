
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from api.user.endpoints import users_endpoints
from flasgger import Swagger
import redis
import time
from helper.user_summary_handler import save_redis_data_to_db
import threading

# Load environment variables from the .env file
load_dotenv()

app = Flask(__name__)

CORS(app)
Swagger(app)

# Koneksi ke Redis yang berjalan di localhost (port 6379)
r = redis.StrictRedis(host='localhost', port=6379, db=0)

def watch_redis_key():
    """Memantau Redis untuk data terbaru dan menyimpan ke database."""
    last_processed = None
    while True:
        latest_message = r.get('latest_message')
        if latest_message != last_processed:  # Cek apakah ada data baru
            last_processed = latest_message
            result = save_redis_data_to_db(latest_message)
            print(result["message"])
        time.sleep(1)  # Tunggu sebentar sebelum polling lagi


def start_redis_watcher():
    # Menjalankan watch_redis_key() dalam thread terpisah
    thread = threading.Thread(target=watch_redis_key)
    thread.daemon = True  # Membuat thread menjadi daemon agar thread ini mati ketika aplikasi Flask berhenti
    thread.start()

# register the blueprint
app.register_blueprint(users_endpoints, url_prefix='/api/v1/users')


if __name__ == '__main__':
    start_redis_watcher()
    app.run(debug=True)
