import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import math

from config import config_import as cu
from DB.db import CounterDB

# Database object
DB = CounterDB()


# Import conf constants
FONT_CONF = cu.get_config_data_by_key('font')
TEXT_CONF = cu.get_config_data_by_key('text')
CAPACITY = cu.get_config_data_by_key('CAPACITY')
DISPLAY_CONF = cu.get_config_data_by_key('monitor_display')
WATERMARK_CONF = cu.get_config_data_by_key('watermarks')
OVERCROWD_CONF = cu.get_config_data_by_key('overcrowd')

# Store consts used across functions in-memory
FONT_PATH = FONT_CONF['FONT_PATH']
FONT_SMALL = ImageFont.truetype(FONT_PATH, FONT_CONF['FONT_SIZE_SMALL'])
FONT_MEDIUM = ImageFont.truetype(FONT_PATH, FONT_CONF['FONT_SIZE_MEDIUM'])
FONT_LARGE = ImageFont.truetype(FONT_PATH, FONT_CONF['FONT_SIZE_LARGE'])
FONT_WAIT = ImageFont.truetype(FONT_PATH, FONT_CONF['FONT_WAIT'])

TEXT_COUNTER = TEXT_CONF['TEXT_COUNTER']
TEXT_BITTE = TEXT_CONF['TEXT_BITTE']
TEXT_WAIT = TEXT_CONF['TEXT_WAIT']

WARNING_COLOR = DISPLAY_CONF['WARNING_COLOR']
WHITE = DISPLAY_CONF['WHITE']
OVERLAY_ALPHA = DISPLAY_CONF['OVERLAY_ALPHA']
OVERLAY_COLOR = DISPLAY_CONF['OVERLAY_COLOR']
PLEASE_WAIT_COLOR = DISPLAY_CONF['PLEASE_WAIT_COLOR']


def overcrowd_messages(img):
    """
    Add overcrowd messages on image

    Args:
        img (np.array): Image array

    Returns:
        (np.array)
    """
    # add alpha channel to image
    alpha_channel = np.ones((img.shape[0], img.shape[1]), dtype="uint8") * 255
    img = np.dstack([img, alpha_channel])

    img_pil = Image.fromarray(img)
    draw = ImageDraw.Draw(img_pil)

    X_center_right = OVERCROWD_CONF['X_CENTER_RIGHT']
    X_center_left = OVERCROWD_CONF['X_CENTER_LEFT']

    # texts, that need to be added using PIL
    text_stat_left = '{}'.format(CAPACITY)
    text_stat_right = ' / {}'.format(CAPACITY)

    # shapes of each text
    w_text_wait, h_text_wait = draw.textsize(
        TEXT_WAIT, stroke_width=3, font=FONT_WAIT)
    w_text_counter, h_text_counter = draw.textsize(
        TEXT_COUNTER, stroke_width=1, font=FONT_LARGE)
    w_stat_left, h_stat_left = draw.textsize(
        text_stat_left, stroke_width=2, font=FONT_LARGE)
    w_stat_right, h_stat_right = draw.textsize(
        text_stat_right, stroke_width=2, font=FONT_LARGE)

    # calculation of coordinates for each text
    X_text_wait = int(X_center_right - w_text_wait / 2)
    Y_text_wait = OVERCROWD_CONF['Y_TEXT_WAIT']
    X_text_counter = int(X_center_right - w_text_counter / 2)
    Y_text_counter = OVERCROWD_CONF['Y_TEXT_COUNTER']
    X_stat_left = int(X_center_right - (w_stat_left + w_stat_right) / 2)
    Y_stat = Y_text_counter + h_text_counter
    X_stat_right = X_stat_left + w_stat_left

    # draw texts on image
    draw.text((X_text_wait, Y_text_wait), TEXT_WAIT,
              font=FONT_WAIT, fill=PLEASE_WAIT_COLOR, stroke_width=3)
    draw.text((X_text_counter, Y_text_counter), TEXT_COUNTER,
              font=FONT_LARGE, fill=WHITE, stroke_width=1)
    draw.text((X_stat_left, Y_stat), text_stat_left,
              font=FONT_LARGE, fill=WARNING_COLOR, stroke_width=2)
    draw.text((X_stat_right, Y_stat), text_stat_right,
              font=FONT_LARGE, fill=WHITE, stroke_width=2)

    # add overlay on image
    overlay = np.zeros((1080, 1920, 4), dtype="uint8")
    img = Image.alpha_composite(img_pil, Image.fromarray(overlay, 'RGBA'))
    img = cv2.cvtColor(np.array(img, dtype="uint8"), cv2.COLOR_BGR2RGB)

    return img


def full_overlay(img, X_margin, Y_margin):
    """
    Adds black overlay covering most of the image

    Args:
        img (np.array): Image
        X_margin (int): Distance from image left/right edges in pixels
        Y_margin (int): Distance from image top/bottom edges in pixels
    Returns:
        (np.array): Updated image
    """
    overlay = img.copy()
    overlay = cv2.rectangle(overlay, (X_margin, Y_margin),
                            (img.shape[1] - X_margin, img.shape[0] - Y_margin),
                            OVERLAY_COLOR, -1)
    img = cv2.addWeighted(overlay, OVERLAY_ALPHA, img,
                          1 - OVERLAY_ALPHA, 0, img)


def overcrowd_overlay(img):
    """
    Adds a message about the place being full and
    an overlay covering most of the image

    Args:
        img (np.array): Image
    Returns:
        (np.array): Updated image
    """
    h, w, _ = img.shape
    Y_margin = int(h * 65 / 1080)
    X_margin = int(w * 60 / 1920)
    full_overlay(img, X_margin, Y_margin)

    img = overcrowd_messages(img)
    return img


def add_warning_text(img, box_height):
    """
    Add warning text on top centre of the image

    Args:
        img (np.array): Image to place warning text over
        box_height (int): height of the box in pixels

    Returns:
        (np.array): Updated image, with warning text
    """
    width = img.shape[1]
    img_pil = Image.fromarray(img)
    draw = ImageDraw.Draw(img_pil)

    # import conf constants for re-use
    SAFETY_FIRST = TEXT_CONF['SAFETY_FIRST']

    # get shape for parts of text
    w_text, h_text = draw.textsize(
        SAFETY_FIRST, stroke_width=1, font=FONT_LARGE)

    # ?make more descriptive name for w_exc
    w_exc, _ = draw.textsize('!', stroke_width=1, font=FONT_LARGE)
    w_triangle = h_text * 3 / math.sqrt(3)

    # calculate coordinates for text and add on image
    text_X = int(width / 2 - w_text / 2)
    text_Y = int(box_height / 2 - h_text / 2)

    # draw the warning message text
    draw.text((text_X, text_Y), SAFETY_FIRST, font=FONT_LARGE,
              fill=WARNING_COLOR, stroke_width=2)

    # transform img to np.array for cv2
    img = np.array(img_pil, dtype="uint8")

    # point coordinates for laft warning triangle
    point_left = [
        int(width / 2 - w_text / 2 + w_exc / 2 - w_triangle / 2),
        int(box_height / 2 + h_text * 0.75)
        ]
    point_up = [
        int(width / 2 - w_text / 2 + w_exc / 2),
        int(box_height / 2 - h_text * 0.75)
        ]
    point_right = [
        int(width / 2 - w_text / 2 + w_exc / 2 + w_triangle / 2),
        int(box_height / 2 + h_text * 0.75)
        ]

    # add triangle on image
    cv2.polylines(img, np.int32(
        np.array([[point_left, point_up, point_right]])),
        True,
        WARNING_COLOR,
        5)

    # point coordinates for right warning triangle
    point_left[0] = point_left[0] + w_text - w_exc
    point_up[0] = point_up[0] + w_text - w_exc
    point_right[0] = point_right[0] + w_text - w_exc

    # add right triangle on image
    cv2.polylines(
        img,
        np.int32(np.array([[point_left, point_up, point_right]])),
        True,
        WARNING_COLOR,
        5)

    return img


def add_counter_text(img, box_shape, people_in):
    """
    Add person counter text on the image

    Args:
        img (np.array): Image
        box_shape (tuple): (width, height) of the counter box
        people_in (int): Number representing the amount of
            people inside the space

    Returns:
        (np.array): Updated image
    """
    box_width, box_height = box_shape
    img_pil = Image.fromarray(img)
    draw = ImageDraw.Draw(img_pil)

    # set in/capacity numbers
    text_in = '{}'.format(people_in)
    text_cap = '{}'.format(CAPACITY)

    # import constants for re-use
    TEXT_COUNTER_UP = TEXT_CONF['TEXT_COUNTER_UP']
    TEXT_COUNTER_DOWN = TEXT_CONF['TEXT_COUNTER_DOWN']

    # get shapes for parts of text
    w_up, h_up = draw.textsize(
        TEXT_COUNTER_UP, stroke_width=1, font=FONT_SMALL)
    w_down, h_down = draw.textsize(
        TEXT_COUNTER_DOWN, stroke_width=1, font=FONT_SMALL)
    w_in, h_in = draw.textsize(text_in, stroke_width=1, font=FONT_SMALL)
    w_cap, h_cap = draw.textsize(text_cap, stroke_width=1, font=FONT_SMALL)
    w_slash, h_slash = draw.textsize(' / ', stroke_width=1, font=FONT_SMALL)

    # calculate coordinates for each part of the text
    textX_up = int((box_width - w_up) / 2)
    textY_up = int(0.05 * box_height)
    textX_down = int((box_width - w_down) / 2)
    textY_down = int(0.1 * box_height + h_up)
    textX_in = int((box_width - w_slash) / 2 - w_in)
    textY_stat = int(0.2 * box_height + h_down + h_up)
    textX_slash = int((box_width - w_slash) / 2)
    textX_cap = int((box_width + w_slash) / 2)

    # add text on image
    draw.text((textX_up, textY_up), TEXT_COUNTER_UP, font=FONT_SMALL,
              fill=WHITE, stroke_width=1)
    draw.text((textX_down, textY_down), TEXT_COUNTER_DOWN, font=FONT_SMALL,
              fill=WHITE, stroke_width=1)
    draw.text((textX_in, textY_stat), text_in, font=FONT_SMALL,
              fill=(0, 255, 0), stroke_width=1)
    draw.text((textX_slash, textY_stat), ' / ', font=FONT_SMALL,
              fill=WHITE, stroke_width=1)
    draw.text((textX_cap, textY_stat), text_cap, font=FONT_SMALL,
              fill=WHITE, stroke_width=1)

    img = np.array(img_pil, dtype="uint8")
    return img


def counter_overlay(img, people_in, people_on_frame, masks_on=False):
    """
    Implements overlay/message logic. Adds messages on image.

    Args:
        img (np.array): Image
        people_in (int): Number representing the amount of
            people inside the space
        people_on_frame (bool): True/False whether there are
            people on frame or not
        masks_on (bool): True/False whether everyone on
            frame wears a mask or not

    Returns:
        (np.array): Updated image
    """
    box_width = int(0.168 * img.shape[1])
    box_height = int(0.142 * img.shape[0])
    overlay = img.copy()

    if masks_on or not people_on_frame:
        overlay = cv2.rectangle(
            overlay, (0, 0), (box_width, box_height), OVERLAY_COLOR, -1)
    # otherwise for adding warning message we take overlay on full width
    else:
        overlay = cv2.rectangle(
            overlay, (0, 0), (img.shape[1], box_height), OVERLAY_COLOR, -1)

    img = cv2.addWeighted(overlay, OVERLAY_ALPHA, img, 1 - OVERLAY_ALPHA,
                          0, img)

    # add counter text on the overlay
    img = add_counter_text(img, (box_width, box_height), people_in)

    # if there are no people on frame just return, no need for messages
    if not people_on_frame:
        return img

    # if masks are on add 'thanks' message on bottom
    if masks_on:
        # if masks are on add 'thanks' message on bottom
        img = lower_overlay(img, TEXT_CONF['TEXT_DANKE_DOWN'])
    else:
        img = add_warning_text(img, box_height)
        img = lower_overlay(img, TEXT_CONF['TEXT_BITTE_DOWN'])
    return img


def lower_overlay(img, text):
    """
    Add overlay on bottom of the image

    Args:
        img (np.array): Image
        text (str): Message to add on the overlay

    Returns:
        (np.array): Updated image, with lower overlay
    """

    # add overlay on bottom
    overlay_height = int(0.13 * img.shape[0])
    overlay = img.copy()

    overlay = cv2.rectangle(
        overlay,
        (0, img.shape[0] - overlay_height),
        (img.shape[1], img.shape[0]),
        OVERLAY_COLOR, -1)
    img = cv2.addWeighted(
        overlay,
        OVERLAY_ALPHA,
        img,
        1 - OVERLAY_ALPHA,
        0,
        img)

    # transform image to PIL to add text on it
    img_pil = Image.fromarray(img)
    draw = ImageDraw.Draw(img_pil)

    # get width/height of text
    w, h = draw.textsize(text, stroke_width=1, font=FONT_LARGE)

    # calculate coordinates for text
    textX = int((img.shape[1] - w) / 2)
    textY = int(img.shape[0] - (overlay_height + h) / 2)

    # add text on bottom overlay
    draw.text((textX, textY), text, font=FONT_LARGE,
              fill=WHITE, stroke_width=1)

    img = np.array(img_pil)
    return img


def add_view_messages(img, people_on_frame, masks_on):
    """
    Add view messages on frame

    Args:
        img (np.array): Image
        people_on_frame (bool): Flag if there are people on frame or not
        mask_boxes (list):

    Returns:
        (np.array): Image, updated with messages on it
    """
    image_area = img.shape[0] * img.shape[1]

    # resize image to default resolution
    img = cv2.resize(img, DISPLAY_CONF['RESOLUTION'])

    # get the number of people inside the given space
    people_in = DB.in_current()

    # if place is full show the message for it
    if people_in >= CAPACITY:
        return overcrowd_overlay(img)

    # othewise show the messages according to the incoming people
    # counter_overlay handles displaying messages about capacity and warnings
    img = counter_overlay(img, people_in, people_on_frame, masks_on)
    img = cv2.cvtColor(np.array(img, dtype="uint8"), cv2.COLOR_BGR2RGB)
    return img
