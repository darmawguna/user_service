from flask import Flask
import time
from flask_cors import CORS
from dotenv import load_dotenv
from api.user.endpoints import users_endpoints
from flasgger import Swagger
from helper.user_summary_handler import save_data_to_db
from confluent_kafka import Consumer, KafkaException, KafkaError
from multiprocessing import Process, Event
import msgpack
import logging

logging.basicConfig(level=logging.INFO)

# Load environment variables from the .env file
load_dotenv()

app = Flask(__name__)

# Kafka consumer configuration
conf = {
    'bootstrap.servers': '192.168.18.12:9092',  # Replace with your Kafka broker address
    'group.id': 'flask-consumer-group',
    'auto.offset.reset': 'earliest',  # Start consuming from the earliest message
}
topic = 'user_summary'  # Replace with your Kafka topic name

# Event to manage process shutdown
stop_event = Event()

def consume_kafka(stop_event):
    """Fungsi untuk mendengarkan Kafka dan mengonsumsi pesan di latar belakang."""
    consumer = None
    while not stop_event.is_set():
        try:
            if not consumer:
                consumer = Consumer(conf)
                consumer.subscribe([topic])
                # logging.info(f"Subscribed to Kafka topic: {topic}") 
                print("Subscribed to Kafka topic:", topic)

            msg = consumer.poll(timeout=5.0)
            if msg is None:
                continue
            elif msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    logging.info(f"End of partition reached for {msg.partition()}")
                else:
                    logging.error(f"Kafka error: {msg.error()}")
                    continue

            message_data = msgpack.unpackb(msg.value(), raw=False)
            save_data_to_db(message_data)
        except Exception as e:
            logging.error(f"Error in Kafka consumer: {e}")
            time.sleep(5)  # Retry delay
        finally:
            if consumer:
                consumer.close()
                consumer = None

# Fungsi untuk memulai konsumer Kafka di proses terpisah
def start_kafka_consumer():
    consumer_process = Process(target=consume_kafka, args=(stop_event,))
    consumer_process.start()
    return consumer_process

CORS(app)
Swagger(app)

# Register the blueprint
app.register_blueprint(users_endpoints, url_prefix='/api/users')

if __name__ == '__main__':
    # Start Kafka consumer in a separate process
    kafka_process = start_kafka_consumer()
    
    try:
        app.run(debug=False, port=5001, host='0.0.0.0')  # Jalankan aplikasi Flask
    finally:
        stop_event.set()  # Hentikan konsumsi Kafka saat Flask dihentikan
        kafka_process.join()  # Tunggu sampai proses Kafka selesai
