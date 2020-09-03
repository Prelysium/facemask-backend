# -*- coding:utf-8 -*-
import time
import cv2
import numpy as np

from mask.detect import inference
from mask.utils import write_output_video
from tracker.tracker import Tracker
from human.detect import cocoDetection
from view.messages import add_view_messages
from config import config_import as conf

# from notifications import sms_notification as send_sms


CAMERA_CONF = conf.get_config_data_by_key("camera_in")

OUTPUT_WINDOW_TITLE = CAMERA_CONF["OUTPUT_WINDOW_TITLE"]
RELEASE_MESSAGE = CAMERA_CONF["RELEASE_MESSAGE"]
TIME_INFO_SAMPLE = CAMERA_CONF["TIME_INFO_SAMPLE"]


def video_output(writer, img_raw, save):
    """
    Display current frame in the video with model information and
    save it into the video

    Args:
        writer (cv2.VideoWriter): Writer object of the video
        img_raw (array): Array of image
        save (bool): Save frame or not

    Returns:
        (float): Time the function ended
    """
    if save:
        writer.write(img_raw[:, :, :])
    write_frame_stamp = time.time()

    cv2.namedWindow(OUTPUT_WINDOW_TITLE, cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty(
        OUTPUT_WINDOW_TITLE, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN
    )
    cv2.imshow(OUTPUT_WINDOW_TITLE, img_raw[:, :, :])
    cv2.waitKey(1)

    return write_frame_stamp


def run_mask_camera(video_path, output_video_name, conf_thresh, target_shape):
    """
    Runs the model on a video stream (file or camera input)

    Parameters:
        video_path (str): 0 for camera input or the path to the video
        output_video_name (str): Output video name
        conf_thresh (float): The min threshold of classification probability.
        target_shape (tuple): Shape of the target

    Returns:
        None
    """
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        raise ValueError("Video open failed.")
        return

    writer = write_output_video(cap, output_video_name)

    status_video_capture = True

    # capture video
    while status_video_capture:
        start_stamp = time.time()
        status_video_capture, img_raw = cap.read()

        if status_video_capture:
            img_raw = cv2.cvtColor(img_raw, cv2.COLOR_BGR2RGB)
            read_frame_stamp = time.time()

            mask_boxes, masks_on = inference(
                img_raw,
                conf_thresh,
                iou_thresh=0.5,
                target_shape=target_shape,
                show_result=False,
            )

            # add UI messages on image
            img_raw = add_view_messages(img_raw, len(mask_boxes), masks_on)

            inference_stamp = time.time()
            write_frame_stamp = video_output(writer, img_raw, bool(output_video_name))

            print(
                TIME_INFO_SAMPLE
                % (
                    read_frame_stamp - start_stamp,
                    inference_stamp - read_frame_stamp,
                    write_frame_stamp - inference_stamp,
                )
            )
        else:
            cap.release()
            print(RELEASE_MESSAGE)
            break
