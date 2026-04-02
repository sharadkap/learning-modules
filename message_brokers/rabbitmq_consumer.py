import pika
import time
import json

def callback(ch, method, properties, body):
    data = json.loads(body)
    print(f" [OK] Received task: {data['task']} for '{data['track_id']}'")
    
    # Simulate work (Encoding takes time)
    time.sleep(2)
    
    print(f" [DONE] Finished processing '{data['track_id']}'")
    
    # 4. Manual Acknowledgment
    # This tells RabbitMQ: "I finished this safely, you can delete it now."
    # If the consumer crashes before this, RabbitMQ will re-queue the message.
    ch.basic_ack(delivery_tag=method.delivery_tag)

def start_consuming():
    # 1. Connection
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()

    # 2. Declare queue (same as producer, just in case)
    channel.queue_declare(queue='music_tasks', durable=True)

    # 3. Fair Dispatch
    # Don't give more than one message to a worker at a time.
    # This distributes work evenly if one worker is slower than others.
    channel.basic_qos(prefetch_count=1)

    print(' [*] Waiting for music tasks. To exit press CTRL+C')
    
    channel.basic_consume(queue='music_tasks', on_message_callback=callback)

    channel.start_consuming()

if __name__ == "__main__":
    try:
        start_consuming()
    except KeyboardInterrupt:
        print("\nStopping worker...")
