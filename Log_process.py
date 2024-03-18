from io import BytesIO
from confluent_kafka import Consumer, KafkaError, Producer, TopicPartition

import json
import os
# import numpy as np




class KafkaLogging:
    def __init__(self, bootstrap_servers='localhost:9092', logs_topic='Logs', group_id='saving') -> None:
        self.bootstrap_servers = bootstrap_servers
        self.log_topic = logs_topic
        self.group_id = group_id

        self.save_log_path = os.getcwd()

        self.comsumer_config = {
            'bootstrap.servers': self.bootstrap_servers,
            'group.id': self.group_id,
            'auto.offset.reset': 'earliest'
        }

        self.consumer = Consumer(self.comsumer_config)
        self.consumer.subscribe([self.log_topic])
        self.latest_offset = 0

    def receive_json(self):
        try:
            while True:
                message = self.consumer.poll(0.0015)
                if message is None:
                    print('Waiting...')
                    # continue
                elif message.error():
                    if message.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    else:
                        print(message.error())
                        break
                else:
                    log_data = json.loads(
                        message.value().decode('utf-8')
                    )
                    print("Logging ...")

                    with open(self.save_log_path + '/log.json', 'a') as json_file:
                        json.dump(log_data, json_file)
                        json_file.write('\n')
        except KeyboardInterrupt:
            pass
        finally:
            self.consumer.close()

if __name__ == "__main__":
    Log = KafkaLogging()
    Log.receive_json()