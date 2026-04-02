# Note: This is a TEMPLATE. Running it requires the C++ core library installed.
from rocketmq.client import PushConsumer, ConsumeStatus
import time

def callback(msg):
    # This function is called for every message received
    print(f" [EVENT] Received: {msg.body.decode('utf-8')} (Tag: {msg.tags})")
    
    # Return ConsumeStatus.CONSUME_SUCCESS to acknowledge
    return ConsumeStatus.CONSUME_SUCCESS

def run_consumer():
    # 1. Initialize Consumer with Group Name
    consumer = PushConsumer('music_consumer_group')
    consumer.set_name_server_address('127.0.0.1:9876')
    
    # 2. Subscribe to Topic
    # The '*' means subscribe to all tags in this topic
    consumer.subscribe('music_topic', callback)
    
    print("📡 RocketMQ Consumer started...")
    consumer.start()

    # Keep the process alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass

    consumer.shutdown()

if __name__ == "__main__":
    run_consumer()
