import pika
import time

# Mock database
MUSIC_DB = {
    "Starboy": {"artist": "The Weeknd", "album": "Starboy", "year": 2016},
    "Chlorine": {"artist": "Twenty One Pilots", "album": "Trench", "year": 2018},
    "Midnight City": {"artist": "M83", "album": "Hurry Up, We're Dreaming", "year": 2011}
}

def on_request(ch, method, props, body):
    track_name = body.decode()
    print(f" [.] Looking up metadata for: {track_name}")
    
    # Simulate DB lookup
    time.sleep(1)
    
    response = MUSIC_DB.get(track_name, "Track Not Found")
    
    # Send response back to the 'reply_to' queue
    ch.basic_publish(exchange='',
                     routing_key=props.reply_to,
                     properties=pika.BasicProperties(correlation_id=props.correlation_id),
                     body=str(response))
    
    # Ack the request
    ch.basic_ack(delivery_tag=method.delivery_tag)

def start_rpc_server():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()

    channel.queue_declare(queue='rpc_queue')

    # Load balance: Don't give a worker more than one message at a time
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='rpc_queue', on_message_callback=on_request)

    print(" [x] Awaiting RPC requests...")
    channel.start_consuming()

if __name__ == "__main__":
    start_rpc_server()
