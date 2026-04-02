# Note: This is a TEMPLATE. Running it requires the C++ core library installed.
from rocketmq.client import Producer, Message

def run_producer():
    # 1. Initialize Producer with Group Name
    producer = Producer('music_producer_group')
    producer.set_name_server_address('127.0.0.1:9876')
    producer.start()

    # 2. Normal Message
    msg = Message('music_topic')
    msg.set_body('Playing: Shape of You')
    msg.set_keys('user_id_1')
    msg.set_tags('Pop')

    # 3. Delayed Message (Level 3 = 10s)
    # RocketMQ has 18 fixed levels: 1s, 5s, 10s, 30s, 1m, 2m, 3m...
    delayed_msg = Message('music_topic')
    delayed_msg.set_body('Delayed Alert: Playlist Updated')
    delayed_msg.set_delay_time_level(3)

    print("🚀 Sending RocketMQ messages...")
    ret = producer.send_sync(msg)
    print(f" [x] Sent Normal: {ret.status} {ret.msg_id}")

    ret_delayed = producer.send_sync(delayed_msg)
    print(f" [x] Sent Delayed: {ret_delayed.status}")

    producer.shutdown()

if __name__ == "__main__":
    run_producer()
