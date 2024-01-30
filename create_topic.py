from confluent_kafka.admin import AdminClient, NewTopic

bootstrap_servers = 'localhost:9092'

admin_client = AdminClient({'bootstrap.servers': bootstrap_servers})

topic_name = 'detection'

num_partitions = 2
replication_factor = 1

new_topic = NewTopic(topic_name, num_partitions, replication_factor)

admin_client.create_topics([new_topic])
