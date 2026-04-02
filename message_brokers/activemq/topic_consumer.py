import stomp
import time

class TopicListener(stomp.ConnectionListener):
    def on_message(self, frame):
        print(f" [ALERT] Received broadcast: {frame.body}")

def start_topic_consumer():
    hosts = [('localhost', 61613)]
    conn = stomp.Connection(host_and_ports=hosts)
    
    conn.set_listener('', TopicListener())
    conn.connect('admin', 'admin', wait=True)

    # Subscribing to a topic
    conn.subscribe(destination='/topic/system_alerts', id=2, ack='auto')

    print(' [*] Waiting for Topic broadcasts (Alerts). To exit press CTRL+C')
    
    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            break

    conn.disconnect()

if __name__ == "__main__":
    start_topic_consumer()
