from confluent_kafka import Consumer, KafkaError
from io import BytesIO
import json
import cv2
import numpy as np

import logging
import mimetypes
import os
import time
from argparse import ArgumentParser

import json_tricks as json
import mmcv
import mmengine
import numpy as np
from mmengine.logging import print_log

from mmpose.apis import inference_topdown
from mmpose.apis import init_model as init_pose_estimator
from mmpose.evaluation.functional import nms
from mmpose.registry import VISUALIZERS
from mmpose.structures import merge_data_samples, split_instances
from mmpose.utils import adapt_mmdet_pipeline


class KafkaPoseEstimation:
    def __init__(self, bootstrap_servers='localhost:9092', detection_topic='Frames', bbox_topic = 'Bboxes', group_id = 'pose_estimation') -> None:
        self.bootstrap_servers = bootstrap_servers
        self.detection_topic = detection_topic
        self.bbox_topic = bbox_topic
        self.group_id = group_id
        self.detection_data_list = []
        self.bbox_data_list = []
        
        self.pose_config = 'Config/Pose/Pose_config/rtmpose-m_8xb256-420e_coco-256x192.py'
        self.pose_checkpoint = 'https://download.openmmlab.com/mmpose/v1/projects/rtmposev1/rtmpose-m_simcc-aic-coco_pt-aic-coco_420e-256x192-63eb25f7_20230126.pth'
        self.device = 'cuda'
        self.draw_heatmap = False
        
        self.radius = 3
        self.thickness = 1
        self.alpha = 0.8
        self.skeleton_style='mmpose'
        
        self.show_interval = 0.01
        self.kpt_thr = 0.3
        self.draw_bbox = True
        self.show=True
        
        #* Build pose estimator
        self.pose_estimator = init_pose_estimator(
            self.pose_config,
            self.pose_checkpoint,
            device=self.device,
            cfg_options=dict(
            model=dict(test_cfg=dict(output_heatmaps=self.draw_heatmap))))
        
        #* Build visualize
        
        self.pose_estimator.cfg.visualizer.radius = self.radius
        self.pose_estimator.cfg.visualizer.alpha = self.alpha
        self.pose_estimator.cfg.visualizer.line_width = self.thickness
        self.visualizer = VISUALIZERS.build(self.pose_estimator.cfg.visualizer)
        # the dataset_meta is loaded from the checkpoint and
        # then pass to the model in init_pose_estimator
        self.visualizer.set_dataset_meta(
            self.pose_estimator.dataset_meta, skeleton_style=self.skeleton_style)
    
        
        
        #====== CONSUMER =======
        
        self.consumer_config = {
            'bootstrap.servers': self.bootstrap_servers,
            'group.id': self.group_id,
            'auto.offset.reset': 'earliest'
        }
        
        self.consumer = Consumer(self.consumer_config)
        self.consumer.subscribe([self.bbox_topic, self.detection_topic])
        
        # 
    
    def process_frames(self, detection_data, bbox_data, offset):
        
            # Perform pose estimation with the input
        frame  = detection_data['image']
        pose_results = inference_topdown(self.pose_estimator, frame, bbox_data['detection_results'])
        data_samples = merge_data_samples(pose_results)
            
        if isinstance(frame, str):
            frame = mmcv.imread(frame, channel_order='rgb')
        elif isinstance(frame, np.ndarray):
            frame = mmcv.bgr2rgb(frame)
                
        if self.visualizer is not None:
            self.visualizer.add_datasample(
                    'result',
                    frame,
                    data_sample = data_samples,
                    draw_gt=False,
                    draw_heatmap=self.draw_heatmap,
                    draw_bbox=self.draw_bbox,
                    show = self.show,
                    wait_time=self.show_interval,
                    kpt_thr=self.kpt_thr
                )
            
        print(f'Pose estimation for frame at offset {offset}')
        
    def receive_and_process_frames(self):
        detection_data = None
        bbox_data = None
        count = 1
        
        try: 
            while True:
                message = self.consumer.poll(1)
                # print(message)
                
                if message is None:
                    print('Waiting....')
                    # continue
                
                elif message.error():
                    if message.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    else:
                        print(message.error())
                        break
                else: 
                    # stream = BytesIO(message.value())
                    offset = message.offset()
                    
                    # Check the topic and process accordingly
                    if message.topic() == self.detection_topic:
                        frame_data = cv2.imdecode(np.frombuffer(message.value(), 'u1'), cv2.IMREAD_UNCHANGED)
                        detection_data = {'offset': offset, 'image': frame_data}
                        self.detection_data_list.append(detection_data)
                        
                    elif message.topic() == self.bbox_topic:
                        decoded_data = json.loads(message.value().decode('utf-8'))
                        bbox_data = {'offset': decoded_data['offset'], 'detection_results': decoded_data['detection_results']}
                        self.bbox_data_list.append(bbox_data)
                        
                    
                    print(f'len det {len(self.detection_data_list)}, bbox {len(self.bbox_data_list)}')
                    if (len(self.bbox_data_list) >= 1 ) and (len(self.detection_data_list) >= 1):
                        
                        idx = min(count, len(self.bbox_data_list), len(self.detection_data_list)) 
                        idx = idx -1
                        
                        self.process_frames(self.detection_data_list[idx], self.bbox_data_list[idx], idx)
                        count += 1

                        print(count)
                        # Remove processed detection data
                        # self.detection_data_list = [d for d in self.detection_data_list if d['offset'] != bbox_data['offset']]
                    # stream.close()
        except KeyboardInterrupt:
            pass
        finally:
            self.consumer.close()
            
            
if __name__ =="__main__":
    kafka_pose_estimation = KafkaPoseEstimation()
    kafka_pose_estimation.receive_and_process_frames()