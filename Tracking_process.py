from io import BytesIO
from confluent_kafka import Consumer, KafkaError, Producer, TopicPartition
from ultralytics import YOLO
# from ultralytics.utils.plotting import Annotator

import numpy as np
import cv2
import json
import time

from pathlib import Path

from boxmot import  OCSORT


class KafkaHumanDetection:
    def __init__(self, bootstrap_servers='localhost:9092', detection_topic='Frames', result_topic='Bboxes', group_id='detection') -> None:
        self.bootstrap_servers = bootstrap_servers
        self.detection_topic = detection_topic
        self.result_topic = result_topic
        self.group_id = group_id
        self.received_frames = []  # store all received frame
        self.model = YOLO('yolov8n.pt')

        # self.tracker = DeepOCSORT(
        #     # which ReID model to use
        #     model_weights=Path('osnet_x0_25_msmt17.pt'),
        #     device='cuda:0',
        #     fp16=False,
        # )
        self.tracker = OCSORT()

        # ======== CONSUMER ===========

        self.consumer_config = {
            'bootstrap.servers': self.bootstrap_servers,
            'group.id': self.group_id,
            'auto.offset.reset': 'earliest'
        }

        self.consumer = Consumer(self.consumer_config)
        self.consumer.subscribe([self.detection_topic])
        self.latest_offset = 0

        # ======== PRODUCER =============
        # write sth here
        self.producer_config = {
            'bootstrap.servers': self.bootstrap_servers
        }
        self.producer = Producer(self.producer_config)

    def delivery_report(self, err, msg):
        if err is not None:
            print('Message delivery failed: {}'.format(err))
        else:
            print("Result delivered to topic: {}, partition: {}, offset: {}".format(
                msg.topic(), msg.partition(), msg.offset()))

    def process_frame(self, frame_data, offset):

        results = self.model(frame_data, classes=0)

        # prepare data to send

        detection_data = {
            'offset': offset,
        }
        bboxes = []
        for r in results:
            boxes = r.boxes
            for box in boxes:
                # get box coordinates (l, t, r, b, cf, cls)
                b = box.data[0].cpu().numpy()

                bboxes.append(b)
        # ! Check if bboxes is empty or not
        if not (not bboxes):
            bboxes = np.stack(bboxes, axis=0)

        detection_data['detection_results'] = bboxes

        # print(bboxes)
        # print(np.array(bboxes))
        tracks = self.tracker.update(np.array(bboxes), frame_data)
        print('this is tracks')
        # print(tracks)

        inds = tracks[:, 7].astype('int')

        print(inds)

        detection_data['inds'] = inds

        self.producer.produce(self.result_topic, value=json.dumps(
            detection_data, default=lambda x: x.tolist()).encode('utf-8'), callback=self.delivery_report)
        self.producer.poll(1)

    def receive_and_process_frames(self):
        try:
            while True:
                message = self.consumer.poll(0)
                time.sleep(0.6)
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

                    frame_data = cv2.imdecode(np.frombuffer(
                        message.value(), 'u1'), cv2.IMREAD_UNCHANGED)

                    self.latest_offset = message.offset()  # Get the offset of receive frame
                    
                    self.process_frame(frame_data=frame_data,
                                       offset=self.latest_offset)
                    print(f'============={self.latest_offset}===========')

                    
        except KeyboardInterrupt:
            pass
        finally:
            self.consumer.close()


if __name__ == '__main__':

    kafka_detection = KafkaHumanDetection()
    kafka_detection.receive_and_process_frames()
