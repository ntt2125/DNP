#!/usr/bin/env python

import sys
from random import choice
from argparse import ArgumentParser, FileType
from configparser import ConfigParser
from confluent_kafka import Producer
import cv2
from datetime import datetime


if __name__ == '__main__':
    # Parse the command line.
    parser = ArgumentParser()
    parser.add_argument('config_file', type=FileType('r'))
    args = parser.parse_args()

    # Parse the configuration.
    # See https://github.com/edenhill/librdkafka/blob/master/CONFIGURATION.md
    config_parser = ConfigParser()
    config_parser.read_file(args.config_file)
    config = dict(config_parser['default'])

    # Create Producer instance
    producer = Producer(config)

    # Optional per-message delivery callback (triggered by poll() or flush())
    # when a message has been successfully delivered or permanently
    # failed delivery (after retries).
    def delivery_callback(err, msg):
        if err:
            print('ERROR: Message failed delivery: {}'.format(err))
        else:
            print("Produced event to topic {topic}: key = {key:12} ".format(
                topic=msg.topic(), key=msg.key().decode('utf-8'), ))

    # Produce data by selecting random values from these lists.
    topic = "dnp_1"
    user_ids = ['eabara', 'jsmith', 'sgarcia', 'jbernard', 'htanaka', 'awalther']
    products = ['book', 'alarm clock', 't-shirts', 'gift card', 'batteries']

    vidcap = cv2.VideoCapture('vid.mp4')
    success, image = vidcap.read()
    count = 0
    
    start_date = datetime.now()
    while success:
        success, image = vidcap.read()
        if success == False:
            print('fail to read video')
            break
        count += 1
        ret, buffer = cv2.imencode('.jpeg', image)
        

        # user_id = choice(user_ids)
        # product = choice(products)
        producer.produce(topic, buffer.tobytes(), str(count) , callback=delivery_callback)
        # count += 1
        # if count == 20:
        #     break

    # Block until the messages are sent.
    producer.poll(10000)
    producer.flush()