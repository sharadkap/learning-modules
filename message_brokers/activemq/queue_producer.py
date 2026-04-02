import stomp
import json
import time

def send_to_queue():
    # ActiveMQ STOMP configuration
    hosts = [('localhost', 61613)]
    conn = stomp.Connection(host_and_ports=hosts)
    
    # Connecting with default ActiveMQ credentials
    conn.connect('admin', 'admin', wait=True)

    tracks = ["Starboy", "Midnight City", "Blinding Lights", "Chlorine"]

    for track in tracks:
        message = {
            "action": "PROCESS_PAYMENT",
            "track": track,
            "amount": 0.99,
            "currency": "USD"
        }
        
        # /queue/ prefix is a convention in ActiveMQ for Queues
        conn.send(body=json.dumps(message), destination='/queue/music_payments')
        print(f" [x] Sent payment task for '{track}' to Queue")
        time.sleep(1)

    conn.disconnect()

if __name__ == "__main__":
    send_to_queue()
