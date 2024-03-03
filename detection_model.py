from io import BytesIO
from confluent_kafka import Consumer, KafkaError, Producer
from ultralytics import YOLO
from ultralytics.utils.plotting import Annotator
import numpy as np
import cv2
import json

class KafkaHumanDetection:
    def __init__(self, bootstrap_servers='localhost:9092', detection_topic='detection', result_topic='bbox', group_id='detection') -> None:
        self.bootstrap_servers = bootstrap_servers
        self.detection_topic = detection_topic
        self.result_topic = result_topic
        self.frame_count = 0
        self.group_id = group_id 
        self.received_frames = [] # store all received frame
        self.model = YOLO('yolov8n.pt')
        
        #======== CONSUMER ===========
        
        self.consumer_config = {
            'bootstrap.servers' : self.bootstrap_servers,
            'group.id': self.group_id,
            'auto.offset.reset': 'earliest'
        }
        
        self.consumer = Consumer(self.consumer_config)
        self.consumer.subscribe([self.detection_topic])
        
        #======== PRODUCER =============
        # write sth here
        self.producer_config = {
            'bootstrap.servers': self.bootstrap_servers
        }
        self.producer = Producer(self.producer_config)
        
    
    def delivery_report(self, err, msg):
        if err is not None:
            print('Message delivery failed: {}'.format(err))
        else:
            print("Result delivered to topic: {}, partition: {}, offset: {}".format(msg.topic(), msg.partition(), msg.offset()))

    
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
                b = box.xyxy[0].cpu().numpy() # get box coordinates (l, t, r, b)
                
                bboxes.append(b)
        
        if not (not bboxes):
            bboxes = np.stack(bboxes, axis=0)
            
        detection_data['detection_results'] = bboxes
        
        self.producer.produce(self.result_topic, value = json.dumps(detection_data, default=lambda x: x.tolist()).encode('utf-8'), callback=self.delivery_report)
        self.producer.poll(0)
        
        
    def receive_and_process_frames(self):
        
        while True:
            message = self.consumer.poll(10)
            if message is None:
                print('Waiting...')
                continue
            if message.error():
                if message.error().code() == KafkaError._PARTITION_EOF:
                    continue
                else:
                    print(message.error())
                    break
                
            stream = BytesIO(message.value())
            frame_data = cv2.imdecode(np.frombuffer(message.value(), 'u1'), cv2.IMREAD_UNCHANGED)
            
            offset = message.offset() # Get the offset of receive frame
            
            self.frame_count += 1
            # self.process_frame(frame_data, offset)
            # results = self.model(frame_data, save=False, show=True, project="output/detect", name='inference', exist_ok=False)
            
            
            self.process_frame(frame_data=frame_data, offset=offset)
            
            stream.close()

if __name__ == '__main__':
    
    kafka_detection = KafkaHumanDetection()
    kafka_detection.receive_and_process_frames()
    
    