import pulsar

def run_consumer():
    # 1. Initialize the Client
    client = pulsar.Client('pulsar://localhost:6650')

    # 2. Subscribe to the Topic
    # SubscriptionType.Shared allows multiple consumers to share the work
    consumer = client.subscribe(
        'persistent://public/default/music-streams',
        subscription_name='my-subscription',
        subscription_type=pulsar.SubscriptionType.Shared
    )

    print("📡 Pulsar Consumer waiting for events...")

    while True:
        try:
            # 3. Receive the message (timeout after 1 second)
            msg = consumer.receive(timeout_millis=1000)
            
            print(f" [EVENT] Received: {msg.data().decode('utf-8')}")

            # 4. Acknowledge processing
            consumer.acknowledge(msg)
        except Exception:
            # Timeout happened, just loop
            continue
        except KeyboardInterrupt:
            break

    # 5. Clean up
    client.close()

if __name__ == "__main__":
    run_consumer()
