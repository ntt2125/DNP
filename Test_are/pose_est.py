
import mimetypes
import os
import time
from argparse import ArgumentParser


import cv2
import CV
import mmengine
import numpy as np

from Pose.apis import inference_topdown
from Pose.apis import init_model as init_pose_estimator
from Pose.structures import merge_data_samples, split_instances

from ultralytics import YOLO
from Pose.structures.pose_data_sample import PoseDataSample


def process_one_image(args,
                      img,
                      detector,
                      pose_estimator,
                      show_interval=0):

    # predict bbox
    det_result = detector(img, classes=0)
    bboxes = []
    for r in det_result:
        boxes = r.boxes

        for box in boxes:
            b = box.xyxy[0].cpu().numpy()
            bboxes.append(b)

    if not (not bboxes):
        bboxes = np.stack(bboxes, axis=0)

    # predict keypoints
    pose_results = inference_topdown(pose_estimator, img, bboxes)
    print(pose_results[0].__class__)
    print(isinstance(pose_results[0], PoseDataSample))
    # print(is_list_of(pose_results, PoseDataSample))
    print('-------------------------------------')
    data_samples = merge_data_samples(pose_results)
    print(data_samples)

    # show the results
    if isinstance(img, str):
        img = CV.imread(img, channel_order='rgb')
    elif isinstance(img, np.ndarray):
        img = CV.bgr2rgb(img)

    return data_samples.get('pred_instances', None)


def main():
    """Visualize the demo images.

    Using mmdet to detect the human.
    """
    parser = ArgumentParser()
    parser.add_argument('pose_config', help='Config file for pose')
    parser.add_argument('pose_checkpoint', help='Checkpoint file for pose')
    parser.add_argument(
        '--input', type=str, default='', help='Image/Video file')
    parser.add_argument(
        '--show',
        action='store_true',
        default=False,
        help='whether to show img')
    parser.add_argument(
        '--output-root',
        type=str,
        default='',
        help='root of the output img file. '
        'Default not saving the visualization images.')
    parser.add_argument(
        '--save-predictions',
        action='store_true',
        default=False,
        help='whether to save predicted results')
    parser.add_argument(
        '--device', default='cuda:0', help='Device used for inference')
    parser.add_argument(
        '--det-cat-id',
        type=int,
        default=0,
        help='Category id for bounding box detection model')
    parser.add_argument(
        '--bbox-thr',
        type=float,
        default=0.3,
        help='Bounding box score threshold')
    parser.add_argument(
        '--nms-thr',
        type=float,
        default=0.3,
        help='IoU threshold for bounding box NMS')
    parser.add_argument(
        '--kpt-thr',
        type=float,
        default=0.3,
        help='Visualizing keypoint thresholds')
    parser.add_argument(
        '--draw-heatmap',
        action='store_true',
        default=False,
        help='Draw heatmap predicted by the model')
    parser.add_argument(
        '--show-kpt-idx',
        action='store_true',
        default=False,
        help='Whether to show the index of keypoints')
    parser.add_argument(
        '--skeleton-style',
        default='mmpose',
        type=str,
        choices=['mmpose', 'openpose'],
        help='Skeleton style selection')
    parser.add_argument(
        '--radius',
        type=int,
        default=3,
        help='Keypoint radius for visualization')
    parser.add_argument(
        '--thickness',
        type=int,
        default=1,
        help='Link thickness for visualization')
    parser.add_argument(
        '--show-interval', type=int, default=0, help='Sleep seconds per frame')
    parser.add_argument(
        '--alpha', type=float, default=0.8, help='The transparency of bboxes')
    parser.add_argument(
        '--draw-bbox', action='store_true', help='Draw bboxes of instances')

    args = parser.parse_args()
    output_file = None
    if args.output_root:
        mmengine.mkdir_or_exist(args.output_root)
        output_file = os.path.join(args.output_root,
                                   os.path.basename(args.input))
        if args.input == 'webcam':
            output_file += '.mp4'

    if args.save_predictions:
        assert args.output_root != ''
        args.pred_save_path = f'{args.output_root}/results_' \
            f'{os.path.splitext(os.path.basename(args.input))[0]}.json'

    # detector
    detector = YOLO('yolov8n.pt')

    # Tracker

    # build pose estimator
    pose_estimator = init_pose_estimator(
        args.pose_config,
        args.pose_checkpoint,
        device=args.device,
        cfg_options=dict(
            model=dict(test_cfg=dict(output_heatmaps=args.draw_heatmap))))

    # build visualizer
    pose_estimator.cfg.visualizer.radius = args.radius
    pose_estimator.cfg.visualizer.alpha = args.alpha
    pose_estimator.cfg.visualizer.line_width = args.thickness

    if args.input == 'webcam':
        input_type = 'webcam'
    else:
        input_type = mimetypes.guess_type(args.input)[0].split('/')[0]

    if input_type == 'image':

        pred_instances = process_one_image(
            args, img=args.input, detector=detector, pose_estimator=pose_estimator)
        if args.save_predictions:
            pred_instances_list = split_instances(pred_instances)

    elif input_type in ['webcam', 'video']:

        if args.input == 'webcam':
            cap = cv2.VideoCapture(0)
        else:
            cap = cv2.VideoCapture(args.input)

        video_writer = None
        pred_instances_list = []
        frame_idx = 0

        while cap.isOpened():
            success, frame = cap.read()
            frame_idx += 1

            if not success:
                break

            # topdown pose estimation
            pred_instances = process_one_image(args, img=frame, detector=detector,
                                               pose_estimator=pose_estimator,
                                               show_interval=0.001)

            if args.save_predictions:
                # save prediction results
                pred_instances_list.append(
                    dict(
                        frame_id=frame_idx,
                        instances=split_instances(pred_instances)))
            if args.show:
                # press ESC to exit
                if cv2.waitKey(5) & 0xFF == 27:
                    break

                time.sleep(args.show_interval)

        if video_writer:
            video_writer.release()

        cap.release()

    else:
        args.save_predictions = False
        raise ValueError(
            f'file {os.path.basename(args.input)} has invalid format.')


if __name__ == "__main__":

    main()

    # model = YOLO('yolov8n.pt')

    # result = model('demo.jpg', classes = 0)
    # python -m Test_are.pose_est Config/Pose/Pose_config/rtmpose-m_8xb256-420e_coco-256x192.py   https://download.openmmlab.com/mmpose/v1/projects/rtmposev1/rtmpose-m_simcc-aic-coco_pt-aic-coco_420e-256x192-63eb25f7_20230126.pth     --input webcam     --show --device cpu
