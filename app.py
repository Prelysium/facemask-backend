import argparse
import tensorflow as tf
import cv2
import os

from view.mask_camera import run_mask_camera
from view.track_camera import run_track_camera
from mask.detect import inference
from DB.db import initialize_database
from config import config_import as conf

VIDEO_PATHS = conf.get_config_data_by_key("video_paths")
CAMERA_IN_VIDEO_PATH = VIDEO_PATHS["CAMERA_IN"]
CAMERA_OUT_VIDEO_PATH = VIDEO_PATHS["CAMERA_OUT"]

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Face Mask Detection")
    parser.add_argument(
        "--video-mode",
        type=int,
        default=0,
        help="run mask_camera or track_camera,\
                             `0` means mask_camera",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="0",
        help="save the result to a new video, \
                            `0` means dont save",
    )

    args = parser.parse_args()

    # for testing config via gui
    try:
        CAMERA_IN_VIDEO_PATH = int(CAMERA_IN_VIDEO_PATH)
        CAMERA_OUT_VIDEO_PATH = int(CAMERA_OUT_VIDEO_PATH)
    except ValueError:
        pass

    initialize_database()
    output_dir = ""

    if args.output == "1":
        output_dir = "./out_data/"
        try:
            os.mkdir(output_dir)
        except:
            pass
        output_dir += "test.avi"

    # Run the in camera in bidirectional mode
    # Tracking is set to False since the track camera
    # performs this task
    if args.video_mode:
        run_track_camera(
            CAMERA_OUT_VIDEO_PATH,
            output_dir,
            conf_thresh=0.5,
            target_shape=(260, 260),
            debug=True,
        )

    # Run the out camera in bidirectional mode
    else:
        run_mask_camera(
            CAMERA_IN_VIDEO_PATH, output_dir, conf_thresh=0.5, target_shape=(260, 260)
        )
