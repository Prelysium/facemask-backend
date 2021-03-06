from aiortc import MediaStreamTrack
import cv2
from av import VideoFrame
import numpy as np
import time

from mask.detect import inference as detect_masks


class MaskMessage:
    def __init__(self):
        self.message = -1

    def set(self, mask_on):
        if mask_on:
            if self.message != 1:
                self.message = 1
        else:
            if self.message != 0:
                self.message = 0

    def get(self):
        return self.message


message_class = MaskMessage()


class OpenCVStreamTrack(MediaStreamTrack):

    kind = "video"

    def __init__(self, track, mode):
        super().__init__()
        self.track = track
        self.mode = mode


    async def recv(self):
        frame = await self.track.recv()
        while not self.track._queue.empty():
            frame = await self.track.recv()

        # if self.mode == "regular":
        #     time.sleep(0.05)
        #     return frame

        img = cv2.cvtColor(np.copy(frame.to_ndarray(format="bgr24")), cv2.COLOR_BGR2RGB)
        # img = np.array(frame)

        now = time.time()
        _, masks_on = detect_masks(img, blur=self.mode == "blur")
        message_class.set(masks_on)

        # print(self.track._id, time.time() - now)

        # # prepare color
        # img_color = cv2.pyrDown(cv2.pyrDown(img))
        # for _ in range(6):
        #     img_color = cv2.bilateralFilter(img_color, 9, 9, 7)
        # img_color = cv2.pyrUp(cv2.pyrUp(img_color))

        # # prepare edges
        # img_edges = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        # img_edges = cv2.adaptiveThreshold(
        #     cv2.medianBlur(img_edges, 7),
        #     255,
        #     cv2.ADAPTIVE_THRESH_MEAN_C,
        #     cv2.THRESH_BINARY,
        #     9,
        #     2,
        # )
        # img_edges = cv2.cvtColor(img_edges, cv2.COLOR_GRAY2RGB)

        # # combine color and edges
        # img = cv2.bitwise_and(img_color, img_edges)

        # rebuild a VideoFrame, preserving timing information
        new_frame = VideoFrame.from_ndarray(
            cv2.cvtColor(img, cv2.COLOR_RGB2BGR), format="bgr24"
        )
        new_frame.pts = frame.pts
        new_frame.time_base = frame.time_base

        return new_frame
