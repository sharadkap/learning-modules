import pika
import os
import sys

def start_fanout_producer():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()

    # Create a 'fanout' exchange
    # A fanout exchange broadcasts to every queue attached to it
    channel.exchange_declare(exchange='music_broadcast', exchange_type='fanout')

    message = "New Album Released: Random Access Memories!"
    
    channel.basic_publish(exchange='music_broadcast', 
                          routing_key='', # Ignored in fanout
                          body=message)
    
    print(f" [x] Broadcasted: {message}")
    connection.close()

if __name__ == "__main__":
    start_fanout_producer()
