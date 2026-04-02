# Apache Pulsar: The Unified Messaging Platform

Apache Pulsar is a next-generation cloud-native distributed messaging and streaming platform. It was originally created by Yahoo and is now an Apache top-level project.

## 1. Why Pulsar? (The "Cloud Native" Advantage)

Pulsar is designed to solve the scaling bottlenecks of Kafka and the feature limitations of RabbitMQ.

| Feature | Apache Kafka | Apache Pulsar |
| :--- | :--- | :--- |
| **Architecture** | Monolithic (Compute + Storage on one node) | Decoupled (Brokers for Compute, Bookies for Storage) |
| **Scaling** | Hard (Requires rebalancing data across partitions) | Easy (Just add more storage nodes; no rebalancing needed) |
| **Multi-tenancy** | Hard (Requires shared partitions) | Native (Built-in Tenants and Namespaces) |
| **Messaging Model** | Streaming only | Unified (Queueing + Streaming) |

## 2. Key Concepts

### Architecture: Broker vs. BookKeeper
*   **Broker**: Stateless nodes that handle connections and routing.
*   **BookKeeper (Bookie)**: Stateful nodes that handle durable storage.
*   **Result**: You can scale your "Connections" independently from your "Disk Space".

### Tiered Storage
Pulsar can automatically offload older data to cheap storage like **Amazon S3** or **Google Cloud Storage** while keeping it accessible to the same consumer code.

### Subscription Types (The Unified Part)
Pulsar lets you choose how you want to consume data:
1.  **Exclusive**: One consumer (Streaming/Kafka style).
2.  **Failover**: One active consumer, others on standby.
3.  **Shared**: Multiple consumers share the work (Queueing/RabbitMQ style).
4.  **Key_Shared**: Messages with the same key go to the same consumer.

---

## 🚀 How to Run the Pulsar Lesson

### 1. Prerequisites
Ensure your virtual environment is activated.
```bash
source venv/bin/activate
cd pulsar
```

### 2. The Producer
```bash
python producer.py
```

### 3. The Consumer
```bash
python consumer.py
```

---

## 💡 Tip: Pulsar vs. Kafka
When asked why Pulsar is "better" than Kafka:
> *"Pulsar's biggest advantage is **Decoupled Storage and Compute**. In Kafka, if you run out of disk, you have to add a new broker and move existing data (rebalance), which is slow and risky. In Pulsar, you just add more BookKeeper nodes, and the system immediately starts using them without moving any old data."*
