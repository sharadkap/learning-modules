import pika
import sys

def callback(ch, method, properties, body):
    print(f" [LOG] severity={method.routing_key}, message={body.decode()}")

def start_routing_consumer():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()

    channel.exchange_declare(exchange='music_logs', exchange_type='direct')

    result = channel.queue_declare(queue='', exclusive=True)
    queue_name = result.method.queue

    # User can pass severities to listen for as command line args
    # e.g., python rabbitmq_routing_consumer.py info error
    severities = sys.argv[1:]
    if not severities:
        print("Usage: python rabbitmq_routing_consumer.py [info] [error] [critical]")
        sys.exit(1)

    for severity in severities:
        channel.queue_bind(
            exchange='music_logs',
            queue=queue_name,
            routing_key=severity
        )

    print(f' [*] Waiting for logs: {severities}. To exit press CTRL+C')

    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)

    channel.start_consuming()

if __name__ == "__main__":
    start_routing_consumer()
