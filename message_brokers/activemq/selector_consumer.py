import stomp
import time

class SelectorListener(stomp.ConnectionListener):
    def on_message(self, frame):
        print(f" [OK] Received High-Priority US Message: {frame.body}")

def start_selector_consumer():
    hosts = [('localhost', 61613)]
    conn = stomp.Connection(host_and_ports=hosts)
    
    conn.set_listener('', SelectorListener())
    conn.connect('admin', 'admin', wait=True)

    # THE MAGIC: We use the 'selector' header during subscription
    # This tells ActiveMQ to only send messages matching this SQL criteria
    selector_query = "priority > 5 AND region = 'US'"
    
    conn.subscribe(destination='/queue/filtered_music', 
                   id=3, 
                   selector=selector_query, 
                   ack='auto')

    print(f' [*] Waiting for messages matching: {selector_query}')
    print(' [*] (Messages with low priority or from EU will be ignored/left in queue)')
    
    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            break

    conn.disconnect()

if __name__ == "__main__":
    start_selector_consumer()
