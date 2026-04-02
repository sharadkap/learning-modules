import stomp
import time

def start_delayed_producer():
    hosts = [('localhost', 61613)]
    conn = stomp.Connection(host_and_ports=hosts)
    conn.connect('admin', 'admin', wait=True)

    # ActiveMQ Scheduled Delivery: 
    # Use 'AMQ_SCHEDULED_DELAY' header (in milliseconds)
    delay_ms = 5000 # 5 seconds
    
    message = f"This message was sent at {time.strftime('%H:%M:%S')} with a 5s delay."
    
    conn.send(body=message, 
              destination='/queue/delayed_tasks', 
              headers={'AMQ_SCHEDULED_DELAY': delay_ms})
    
    print(f" [x] Sent message with 5s delay. Expect it to arrive in console shortly.")
    conn.disconnect()

if __name__ == "__main__":
    start_delayed_producer()
