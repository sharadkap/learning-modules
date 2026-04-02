import pika

def callback(ch, method, properties, body):
    print(f" [LISTENER] Received notification: {body.decode()}")

def start_fanout_consumer():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()

    # 1. Declare the exchange
    channel.exchange_declare(exchange='music_broadcast', exchange_type='fanout')

    # 2. Create a TEMPORARY queue for this listener
    # exclusive=True means the queue will be deleted when the connection is closed
    result = channel.queue_declare(queue='', exclusive=True)
    queue_name = result.method.queue

    # 3. Bind the queue to the exchange
    channel.queue_bind(exchange='music_broadcast', queue=queue_name)

    print(' [*] Waiting for BROADCASTS. To exit press CTRL+C')

    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)

    channel.start_consuming()

if __name__ == "__main__":
    start_fanout_consumer()
