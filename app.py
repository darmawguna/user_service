from flask import Flask
import time
from flask_cors import CORS
from dotenv import load_dotenv
from api.user.endpoints import users_endpoints
from flasgger import Swagger
from helper.user_summary_handler import save_data_to_db
from confluent_kafka import Consumer, KafkaException, KafkaError
import threading
import msgpack
import logging

logging.basicConfig(level=logging.INFO)

# Load environment variables from the .env file
load_dotenv()

app = Flask(__name__)

# Kafka consumer configuration
conf = {
    'bootstrap.servers': 'localhost:9092',  # Replace with your Kafka broker address
    'group.id': 'flask-consumer-group',
    'auto.offset.reset': 'earliest',  # Start consuming from the earliest message
}
topic = 'user_summary'  # Replace with your Kafka topic name

import signal

stop_event = threading.Event()  # Global event untuk menghentikan loop Kafka

def consume_kafka():
    consumer = None
    while not stop_event.is_set():
        try:
            if not consumer:
                consumer = Consumer(conf)
                consumer.subscribe([topic])
                logging.info(f"Subscribed to Kafka topic: {topic}")

            msg = consumer.poll(timeout=1.0)
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


# def handle_shutdown(signal, frame):
#     print("Shutting down gracefully...")
#     stop_event.set()  # Set the stop_event untuk menghentikan Kafka consumer

# signal.signal(signal.SIGINT, handle_shutdown)
# signal.signal(signal.SIGTERM, handle_shutdown)


CORS(app)
Swagger(app)

# Register the blueprint
app.register_blueprint(users_endpoints, url_prefix='/api/users')

# Start Kafka consumer in a separate thread
def start_kafka_consumer():
    kafka_thread = threading.Thread(target=consume_kafka, daemon=True)
    kafka_thread.start()

if __name__ == '__main__':
    # start_kafka_consumer()  # Start Kafka subscriber
    app.run(debug=False, port=5001)
