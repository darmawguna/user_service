import msgpack
from confluent_kafka import Consumer, KafkaException, KafkaError
import redis
import json


r = redis.StrictRedis(host='localhost', port=6379, db=0)


conf = {
    'bootstrap.servers': 'localhost:9092', 
    'group.id': 'transaction-consumer-group',
    'auto.offset.reset': 'earliest',
}

consumer = Consumer(conf)
topic = 'user_summary'  

def consume_message():
    try:
        consumer.subscribe([topic])  

        while True:
            msg = consumer.poll(timeout=1.0)  
            if msg is None:
                continue
            elif msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    print(f"End of partition reached {msg.partition()}")
                else:
                    raise KafkaException(msg.error())
            else:
                try:
                    
                    message_data = msgpack.unpackb(msg.value(), raw=False)  
                    print(f"Received message: {message_data}")

                  
                    if isinstance(message_data, dict):
                        
                        message_data_json = json.dumps(message_data)
                        
                        # Simpan data ke Redis
                        r.set('latest_message', message_data_json)
                        print("Data sent to Redis:", message_data_json)
                    else:
                        print("Error: Received data is not a dictionary. Skipping.")

                except Exception as e:
                    print(f"Error processing message: {e}")

    except KeyboardInterrupt:
        print("Consumer interrupted by user")

    finally:
        consumer.close()

# Menjalankan consumer
if __name__ == '__main__':
    consume_message()
