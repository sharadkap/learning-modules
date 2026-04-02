import pika
import sys

def callback(ch, method, properties, body):
    print(f" [RECV] {method.routing_key} : {body.decode()}")

def start_topic_consumer():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()

    channel.exchange_declare(exchange='music_topics', exchange_type='topic')

    result = channel.queue_declare(queue='', exclusive=True)
    queue_name = result.method.queue

    # User passes patterns like "music.rock.*" or "#" as command line args
    binding_keys = sys.argv[1:]
    if not binding_keys:
        print("Usage: python rabbitmq_topic_consumer.py [binding_key]...")
        print("Example: python rabbitmq_topic_consumer.py \"music.rock.*\"")
        print("Example: python rabbitmq_topic_consumer.py \"#\" (Matches everything)")
        sys.exit(1)

    for binding_key in binding_keys:
        channel.queue_bind(
            exchange='music_topics',
            queue=queue_name,
            routing_key=binding_key
        )

    print(f' [*] Listening for patterns: {binding_keys}. To exit press CTRL+C')

    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)

    channel.start_consuming()

if __name__ == "__main__":
    try:
        start_topic_consumer()
    except KeyboardInterrupt:
        pass
