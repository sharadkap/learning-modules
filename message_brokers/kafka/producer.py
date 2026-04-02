from confluent_kafka import Producer
import json
import time

def delivery_report(err, msg):
    """ Called once for each message produced to indicate delivery result. """
    if err is not None:
        print(f' ❌ Message delivery failed: {err}')
    else:
        print(f' ✅ Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}')

def run_producer():
    # 1. Configuration
    conf = {
        'bootstrap.servers': 'localhost:9092',
        'client.id': 'python-producer'
    }

    # 2. Initialize Producer
    producer = Producer(conf)

    topic = 'music_streams'

    songs = [
        {"user": "Alice", "song": "Starboy", "genre": "Pop"},
        {"user": "Bob", "song": "Midnight City", "genre": "Electronic"},
        {"user": "Alice", "song": "Blinding Lights", "genre": "Pop"},
        {"user": "Charlie", "song": "Chlorine", "genre": "Indie"}
    ]

    print(f"🚀 Producing events to topic: {topic}")

    for song in songs:
        # Trigger any available delivery report callbacks from previous produce() calls
        producer.poll(0)

        # 3. Asynchronously produce a message
        # We use 'user' as the key to ensure all events for one user go to the SAME partition
        producer.produce(
            topic, 
            key=song['user'], 
            value=json.dumps(song), 
            callback=delivery_report
        )
        time.sleep(1)

    # 4. Wait for any outstanding messages to be delivered
    print("Flushing final messages...")
    producer.flush()

if __name__ == "__main__":
    run_producer()
