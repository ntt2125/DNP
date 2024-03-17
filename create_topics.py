from confluent_kafka.admin import AdminClient, NewTopic


def create_topic():

    a = AdminClient({'bootstrap.servers': 'localhost:9092'})
    config = {
        'num_partitions': 1,
        'replication_factor': 1
    }

    new_topics = [NewTopic(topic, num_partitions=config['num_partitions'],
                           replication_factor=config['replication_factor']) for topic in ["Frames", "Bboxes"]]
    # Note: In a multi-cluster production scenario, it is more typical to use a replication_factor of 3 for durability.

    # Call create_topics to asynchronously create topics. A dict
    # of <topic,future> is returned.
    fs = a.create_topics(new_topics)

# Wait for each operation to finish.
    for topic, f in fs.items():
        try:
            f.result()  # The result itself is None
            print("Topic {} created".format(topic))
        except Exception as e:
            print("Failed to create topic {}: {}".format(topic, e))


def list_topics():
    # Configure Kafka Admin Client
    bootstrap_servers = "localhost:9092"  # Example bootstrap servers
    admin_client = AdminClient({"bootstrap.servers": bootstrap_servers})

    # List Topics
    topics_metadata = admin_client.list_topics().topics
    topics_list = [topic for topic in topics_metadata.keys()]

    print("List of topics:")
    for topic in topics_list:
        print(topic)


if __name__ == "__main__":
    create_topic()
    list_topics()
