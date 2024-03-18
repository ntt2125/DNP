from confluent_kafka import Consumer, Producer, KafkaError
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
    def __init__(self, bootstrap_servers='localhost:9092', frame_topic='Frames', bbox_topic='Bboxes', log_topic = 'Logs', group_id='pose_estimation') -> None:
        self.bootstrap_servers = bootstrap_servers
        self.frame_topic = frame_topic
        self.bbox_topic = bbox_topic
        self.log_topic = log_topic
        self.group_id = group_id
        self.frame_data_list = []
        self.bbox_data_list = []

        self.pose_config = 'Config/Pose/Pose_config/rtmpose-m_8xb256-420e_coco-256x192.py'
        self.pose_checkpoint = 'https://download.openmmlab.com/mmpose/v1/projects/rtmposev1/rtmpose-m_simcc-aic-coco_pt-aic-coco_420e-256x192-63eb25f7_20230126.pth'
        self.device = 'cpu'
        self.draw_heatmap = False

        self.radius = 3
        self.thickness = 1
        self.alpha = 0.8
        self.skeleton_style = 'mmpose'

        self.show_interval = 0.01
        self.kpt_thr = 0.3
        self.draw_bbox = True
        self.show = True

        # * Build pose estimator
        self.pose_estimator = init_pose_estimator(
            self.pose_config,
            self.pose_checkpoint,
            device=self.device,
            cfg_options=dict(
                model=dict(test_cfg=dict(output_heatmaps=self.draw_heatmap))))

        # * Build visualize

        self.pose_estimator.cfg.visualizer.radius = self.radius
        self.pose_estimator.cfg.visualizer.alpha = self.alpha
        self.pose_estimator.cfg.visualizer.line_width = self.thickness
        self.visualizer = VISUALIZERS.build(self.pose_estimator.cfg.visualizer)

        # the dataset_meta is loaded from the checkpoint and
        # then pass to the model in init_pose_estimator
        self.visualizer.set_dataset_meta(
            self.pose_estimator.dataset_meta, skeleton_style=self.skeleton_style)

        # *====================== CONSUMER =======================

        self.consumer_config = {
            'bootstrap.servers': self.bootstrap_servers,
            'group.id': self.group_id,
            'auto.offset.reset': 'earliest'
        }

        # * Frame's Consumer
        self.consumer_frames = Consumer(self.consumer_config)
        self.consumer_frames.subscribe([self.frame_topic])

        # * Bboxes Consumer
        self.consumer_bboxes = Consumer(self.consumer_config)
        self.consumer_bboxes.subscribe([self.bbox_topic])

        # *========================== PRODUCER =====================
        # push the log to the topic - save or visualize
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

    def log_to_topic(self, track_data, pose_keypoints):
        log = {
            'bboxs': track_data['detection_results'],
            'inds': track_data['inds'],
            'keypoint': pose_keypoints
        }

        self.producer.produce(
            self.log_topic, value=json.dumps(
                log, default=lambda x: x.tolist()
            ).encode('utf-8'), callback=self.delivery_report
        )
        self.producer.poll(1)

    def handle_mgs(self, message):
        is_continue = True

        if (message is None):
            print('Waiting....')
            return is_continue
        elif message.error():
            if message.error().code() == KafkaError._PARTITION_EOF:
                print('hi')
                return is_continue
            else:
                print(message.error())
                is_continue = False
                return is_continue
        else:
            return message

    def process_frames(self, frame_data, bbox_data, offset, visual=None):

        # Perform pose estimation with the input
        frame = frame_data['image']
        # print(bbox_data['detection_results'])
        
        # error when using slice with list, convert it to np first, use slice, then to array --- works :))
        pose_results = inference_topdown(
            self.pose_estimator, frame, np.array(bbox_data['detection_results'])[:, :4].tolist())

        # print(pose_results)
        data_samples = merge_data_samples(pose_results)

        # how to get the keypoit data.

        if isinstance(frame, str):
            frame = mmcv.imread(frame, channel_order='rgb')
        elif isinstance(frame, np.ndarray):
            frame = mmcv.bgr2rgb(frame)

        if self.visualizer is not None and visual is not None:
            self.visualizer.add_datasample(
                'result',
                frame,
                data_sample=data_samples,
                draw_gt=False,
                draw_heatmap=self.draw_heatmap,
                draw_bbox=self.draw_bbox,
                show=self.show,
                wait_time=self.show_interval,
                kpt_thr=self.kpt_thr
            )

        # * Send to the topic record
        self.log_to_topic(track_data=bbox_data, pose_keypoints=data_samples.pred_instances.keypoints)
        print(f'Pose estimation for frame at offset {offset}')
        # return data_samples.pred_instances.keypoints

    def receive_and_process_frames(self):
        frame_data = None
        bbox_data = None
        count = 1

        try:
            while True:
                frame_data = None
                bbox_data = None

                message_frames = self.consumer_frames.poll(1)
                message_bboxes = self.consumer_bboxes.poll(1)

                # print(message_frames)
                message_frames = self.handle_mgs(message=message_frames)
                message_bboxes = self.handle_mgs(message=message_bboxes)

                if message_frames is True:
                    #! print('continue')
                    continue
                elif not message_frames:
                    #! print('break')
                    break
                else:
                    print('message_frames')
                    offset = message_frames.offset()

                    frame_data = cv2.imdecode(np.frombuffer(
                        message_frames.value(), 'u1'), cv2.IMREAD_UNCHANGED)
                    frame_data = {'offset': offset, 'image': frame_data}
                    self.frame_data_list.append(frame_data)

                if message_bboxes is True:
                    continue
                elif not message_bboxes:
                    break
                else:
                    decoded_data = json.loads(
                        message_bboxes.value().decode('utf-8'))
                    bbox_data = {
                        'offset': decoded_data['offset'], 'detection_results': decoded_data['detection_results'], 'inds': decoded_data['inds']}
                    self.bbox_data_list.append(bbox_data)

                    print(
                        f'len det {len(self.frame_data_list)}, bbox {len(self.bbox_data_list)}')
                    if (len(self.bbox_data_list) >= 1) and (len(self.frame_data_list) >= 1):

                        idx = min(count, len(self.bbox_data_list),
                                  len(self.frame_data_list))
                        idx = idx - 1

                        self.process_frames(
                            self.frame_data_list[idx], self.bbox_data_list[idx], idx)
                        count += 1

                        # Remove processed detection data
                        # self.frame_data_list = [d for d in self.frame_data_list if d['offset'] != bbox_data['offset']]

                """ if (message_frames is None) or (message_bboxes is None) :
                    print('Waiting....')
                    # continue
                #* Check errors of msg_frames
                elif message_frames.error():
                    if message_frames.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    else:
                        print(message_frames.error())
                        break
                #* Check errors of msg_bboxes
                elif message_bboxes.error():
                    if message_bboxes.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    else:
                        print(message_bboxes.error())
                        break
                
                else: 
                    # stream = BytesIO(message_frames.value())
                    offset = message_frames.offset()
                    
                    frame_data = cv2.imdecode(np.frombuffer(message_frames.value(), 'u1'), cv2.IMREAD_UNCHANGED)
                    frame_data = {'offset': offset, 'image': frame_data}
                    self.frame_data_list.append(frame_data)
                        
                    decoded_data = json.loads(message_bboxes.value().decode('utf-8'))
                    bbox_data = {'offset': decoded_data['offset'], 'detection_results': decoded_data['detection_results']}
                    self.bbox_data_list.append(bbox_data)
                        
                    
                    print(f'len det {len(self.frame_data_list)}, bbox {len(self.bbox_data_list)}')
                    if (len(self.bbox_data_list) >= 1 ) and (len(self.frame_data_list) >= 1):
                        
                        idx = min(count, len(self.bbox_data_list), len(self.frame_data_list)) 
                        idx = idx -1
                        
                        self.process_frames(self.frame_data_list[idx], self.bbox_data_list[idx], idx)
                        count += 1

                        print(count)
                        # Remove processed detection data
                        # self.frame_data_list = [d for d in self.frame_data_list if d['offset'] != bbox_data['offset']]
                    # stream.close() """
        except KeyboardInterrupt:
            pass
        finally:
            self.consumer_frames.close()


if __name__ == "__main__":
    kafka_pose_estimation = KafkaPoseEstimation()
    kafka_pose_estimation.receive_and_process_frames()