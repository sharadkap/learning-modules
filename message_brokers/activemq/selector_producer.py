import stomp
import time

def start_selector_producer():
    hosts = [('localhost', 61613)]
    conn = stomp.Connection(host_and_ports=hosts)
    conn.connect('admin', 'admin', wait=True)

    # We will send messages with different 'priority' and 'region' headers
    messages = [
        ("Classic Rock Hits", {"priority": 8, "region": "US"}),
        ("Local Indie Track", {"priority": 3, "region": "EU"}),
        ("Breaking News Alert", {"priority": 10, "region": "US"}),
        ("Weather Update", {"priority": 4, "region": "US"})
    ]

    for body, headers in messages:
        # Note: ActiveMQ Selectors work on HEADERS, not the body
        conn.send(body=body, 
                  destination='/queue/filtered_music', 
                  headers=headers)
        print(f" [x] Sent '{body}' with headers {headers}")
        time.sleep(1)

    conn.disconnect()

if __name__ == "__main__":
    start_selector_producer()
