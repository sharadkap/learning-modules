import stomp
import time
import json
import sys

class QueueListener(stomp.ConnectionListener):
    def on_error(self, frame):
        print(f'received an error "{frame.body}"')

    def on_message(self, frame):
        data = json.loads(frame.body)
        print(f" [OK] Received Payment: {data['track']} (${data['amount']})")
        
        # Simulate processing time
        time.sleep(1)
        print(f" [DONE] Payment processed for '{data['track']}'")

def start_queue_consumer():
    hosts = [('localhost', 61613)]
    conn = stomp.Connection(host_and_ports=hosts)
    
    conn.set_listener('', QueueListener())
    conn.connect('admin', 'admin', wait=True)

    # Subscribe to the queue
    # id is a unique identifier for this subscription
    conn.subscribe(destination='/queue/music_payments', id=1, ack='auto')

    print(' [*] Waiting for Queue messages (Payments). To exit press CTRL+C')
    
    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            break

    conn.disconnect()

if __name__ == "__main__":
    start_queue_consumer()
