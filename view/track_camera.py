# -*- coding:utf-8 -*-
import time
import cv2
import numpy as np

from mask.detect import inference
from tracker.tracker import Tracker
from human.detect import cocoDetection
from DB.db import CounterDB
from config import config_import as conf

CAMERA_CONF = conf.get_config_data_by_key("camera_out")
RELEASE_MESSAGE = CAMERA_CONF["RELEASE_MESSAGE"]
TIME_INFO_SAMPLE = CAMERA_CONF["TIME_INFO_SAMPLE"]
DOOR_VIEW_WINDOW_TITLE = CAMERA_CONF["DOOR_VIEW_WINDOW_TITLE"]


def run_track_camera(
    video_path, output_video_name, conf_thresh, target_shape, debug=False
):
    """
    Runs the model on a video stream (file or camera input)

    Parameters:
        video_path (str): 0 for camera input or
            string for the path to the video
        output_video_name (str): Output video name
        conf_thresh (float): The min threshold of classification probability.
        target_shape (tuple): Shape of the target
        debug (bool): True for imshow the frame

    Returns:
        None
    """
    coco = cocoDetection()
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError("Video open failed.")
        return

    # db = CounterDB()

    tracker = Tracker(track_in=False)
    status_video_capture = True

    # capture video
    while status_video_capture:
        start_stamp = time.time()
        status_video_capture, img_raw = cap.read()

        if status_video_capture:
            img_raw = cv2.cvtColor(img_raw, cv2.COLOR_BGR2RGB)
            read_frame_stamp = time.time()

            height, width, _ = img_raw.shape
            # Configurable threshold, currently
            # set to split the screen in half width wise
            threshold = height // 2

            # Human detection
            people_boxes = coco.inference(img_raw)
            # tracking
            tracker.track_object(
                read_frame_stamp,
                people_boxes,
                img_raw,
                threshold=threshold,
                debug=debug,
            )

            inference_stamp = time.time()
            # print(TIME_INFO_SAMPLE % (read_frame_stamp - start_stamp,
            #                           inference_stamp - read_frame_stamp))

            if debug:
                image = cv2.line(
                    img_raw, (0, threshold), (width, threshold), (0, 255, 255), 2
                )
                cv2.imshow(DOOR_VIEW_WINDOW_TITLE, image)
                cv2.waitKey(1)

        else:
            cap.release()
            print(RELEASE_MESSAGE)
            break
