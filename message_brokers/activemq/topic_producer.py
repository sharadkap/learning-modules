import stomp
import time

def broadcast_to_topic():
    hosts = [('localhost', 61613)]
    conn = stomp.Connection(host_and_ports=hosts)
    conn.connect('admin', 'admin', wait=True)

    announcement = "🚨 SYSTEM MAINTENANCE: Servers will be down at Midnight UTC"
    
    # /topic/ prefix is mandatory for Pub/Sub in ActiveMQ
    conn.send(body=announcement, destination='/topic/system_alerts')
    
    print(f" [x] Broadcasted Alert: {announcement}")
    conn.disconnect()

if __name__ == "__main__":
    broadcast_to_topic()
