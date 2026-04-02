import pika
import sys

def start_routing_producer():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()

    # 'direct' exchange routes messages based on a routing key
    channel.exchange_declare(exchange='music_logs', exchange_type='direct')

    # Example logs
    logs = [
        ('info', 'Track Starboy started playing'),
        ('error', 'Failed to load album art for Midnight City'),
        ('info', 'User logged in'),
        ('critical', 'DATABASE CONNECTION LOST!')
    ]

    for severity, message in logs:
        channel.basic_publish(
            exchange='music_logs',
            routing_key=severity,
            body=message
        )
        print(f" [x] Sent [{severity}]: {message}")

    connection.close()

if __name__ == "__main__":
    start_routing_producer()
