from confluent_kafka import Consumer, Producer, KafkaError
from io import BytesIO
from rtmlib import draw_skeleton, draw_bbox
import cv2
import numpy as np
import json


class KafkaSaveVideo:
    def __init__(self, bootstrap_servers='localhost:9092', frame_topic='Frames', log_topic='Logs', group_id='save_vid') -> None:
        self.bootstrap_servers = bootstrap_servers
        self.frame_topic = frame_topic
        self.log_topic = log_topic
        self.group_id = group_id

        self.frame_data_list = []
        self.log_data_list = []

        self.output_video = 'output_video.avi'
        self.fourcc = cv2.VideoWriter_fourcc(*'XVID')
        self.video_writer = cv2.VideoWriter(self.output_video, self.fourcc, 20.0, (1920, 1080))
        
        self.consumer_config = {
            'bootstrap.servers': self.bootstrap_servers,
            'group.id': self.group_id,
            'auto.offset.reset': 'earliest'
        }

        # * Frame's Consumer
        self.consumer_frames = Consumer(self.consumer_config)
        self.consumer_frames.subscribe([self.frame_topic])

        # * logs Consumer
        self.consumer_logs = Consumer(self.consumer_config)
        self.consumer_logs.subscribe([self.log_topic])

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

    def process_frames(self, frame, log, offset):
        keypoints = np.array(log['keypoints'])
        scores = np.array(log['scores'])
        bboxes = np.array(log['bboxes'])
        img_shape = log['img_shape']

        img = draw_bbox(img=frame['image'], bboxes=bboxes[:, :4])

        img = draw_skeleton(img=img, keypoints=keypoints,
                            scores=scores, kpt_thr=0.2)
        return img

    def vid_save_process(self):
        try:
            while True:

                message_frames = self.consumer_frames.poll(1)
                message_logs = self.consumer_logs.poll(1)

                # print(message_frames)
                message_frames = self.handle_mgs(message=message_frames)
                message_logs = self.handle_mgs(message=message_logs)

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

                if message_logs is True:
                    continue
                elif not message_logs:
                    break
                else:
                    decoded_log_data = json.loads(
                        message_logs.value().decode('utf-8'))

                    decoded_log_data['offset'] = message_logs.offset()

                    self.log_data_list.append(decoded_log_data)

                    print(
                        f'len det {len(self.frame_data_list)}, bbox {len(self.log_data_list)}')
                    if (len(self.log_data_list) >= 1) and (len(self.frame_data_list) >= 1):

                        log = self.log_data_list.pop(0)
                        frame = self.frame_data_list.pop(0)

                        img = self.process_frames(
                            frame=frame, log=log, offset=frame['offset'])
                        self.video_writer.write(img)
                        

        except KeyboardInterrupt:
            pass
        finally:
            self.consumer_frames.close()
            self.consumer_logs.close()
            

if __name__ == "__main__":
    save_vid = KafkaSaveVideo()
    save_vid.vid_save_process()

