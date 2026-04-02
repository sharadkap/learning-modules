import pulsar

def run_producer():
    # 1. Initialize the Client
    client = pulsar.Client('pulsar://localhost:6650')

    # 2. Create the Producer
    # Topic format: persistent://tenant/namespace/topic
    # 'public/default' is the default tenant/namespace
    producer = client.create_producer('persistent://public/default/music-streams')

    tracks = ["Levitating", "Heat Waves", "Save Your Tears", "Stay"]

    print("🚀 Pulsar Producer sending tracks...")

    for track in tracks:
        producer.send(track.encode('utf-8'))
        print(f" [x] Sent: {track}")

    # 3. Clean up
    client.close()

if __name__ == "__main__":
    run_producer()
