import pika
import sys

def start_topic_producer():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()

    # Declare a 'topic' exchange
    channel.exchange_declare(exchange='music_topics', exchange_type='topic')

    # Example messages with hierarchical routing keys
    messages = [
        ('music.rock.classic', 'Queen - Bohemian Rhapsody'),
        ('music.rock.alt', 'Radiohead - Creep'),
        ('music.pop.hits', 'The Weeknd - Blinding Lights'),
        ('music.jazz.mellow', 'Miles Davis - So What'),
        ('news.music.rock', 'New Rock Hall of Fame inductees announced')
    ]

    for routing_key, message in messages:
        channel.basic_publish(
            exchange='music_topics',
            routing_key=routing_key,
            body=message
        )
        print(f" [x] Sent '{routing_key}':'{message}'")

    connection.close()

if __name__ == "__main__":
    start_topic_producer()
