import pika
import json
import time

def send_task():
    # 1. Establish connection to RabbitMQ server
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()

    # 2. Declare a queue (It's idempotent - only created if it doesn't exist)
    # durable=True means the queue will survive a RabbitMQ server restart
    channel.queue_declare(queue='music_tasks', durable=True)

    tracks = ["Starboy", "Midnight City", "Blinding Lights", "Chlorine"]

    for track in tracks:
        message = {
            "task": "ENCODE_MP3",
            "track_id": track,
            "quality": "320kbps",
            "timestamp": time.time()
        }
        
        # 3. Publish the message
        # In RabbitMQ, messages are sent to Exchanges, not directly to queues.
        # The empty string '' is the default exchange, which routes to the queue name.
        channel.basic_publish(
            exchange='',
            routing_key='music_tasks',
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2,  # make message persistent
            )
        )
        print(f" [x] Sent '{track}' encoding task")
        time.sleep(1)

    # 4. Close connection
    connection.close()

if __name__ == "__main__":
    send_task()
