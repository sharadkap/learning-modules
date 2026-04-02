import pika
import json
import uuid

class MusicRpcClient(object):
    def __init__(self):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        self.channel = self.connection.channel()

        # Create a unique callback queue for this client instance
        result = self.channel.queue_declare(queue='', exclusive=True)
        self.callback_queue = result.method.queue

        self.channel.basic_consume(
            queue=self.callback_queue,
            on_message_callback=self.on_response,
            auto_ack=True)

        self.response = None
        self.corr_id = None

    def on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = body

    def call(self, track_name):
        self.response = None
        self.corr_id = str(uuid.uuid4())
        
        # Send request to 'rpc_queue'
        self.channel.basic_publish(
            exchange='',
            routing_key='rpc_queue',
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id,
            ),
            body=track_name)
        
        # Wait for response
        while self.response is None:
            self.connection.process_data_events()
        
        return self.response.decode()

if __name__ == "__main__":
    music_rpc = MusicRpcClient()
    print(" [x] Requesting metadata for 'Starboy'...")
    response = music_rpc.call("Starboy")
    print(f" [.] Result: {response}")
