from confluent_kafka import Consumer, KafkaError
import json

def run_consumer():
    # 1. Configuration
    conf = {
        'bootstrap.servers': 'localhost:9092',
        'group.id': 'music-analytics-group',
        'auto.offset.reset': 'earliest' # Start from the beginning if no offset exists
    }

    # 2. Initialize Consumer
    consumer = Consumer(conf)

    # 3. Subscribe to the Topic
    consumer.subscribe(['music_streams'])

    print("📡 Consumer started. Waiting for events...")
    print(" (Offset is set to 'earliest' - you will see ALL history)")

    try:
        while True:
            # Poll for messages
            msg = consumer.poll(1.0) # 1 second timeout

            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    # End of partition event
                    continue
                else:
                    print(f"Error: {msg.error()}")
                    break

            # 4. Process the message
            data = json.loads(msg.value().decode('utf-8'))
            print(f" [EVENT] User {data['user']} played {data['song']} ({data['genre']}) | Partition: {msg.partition()} | Offset: {msg.offset()}")

    except KeyboardInterrupt:
        pass
    finally:
        # 5. Close down consumer to commit final offsets
        consumer.close()

if __name__ == "__main__":
    run_consumer()
