import cv2
import time
import numpy as np

from tracker.trackableobject import TrackableObject
from tracker.centroidtracker import CentroidTracker
from DB.db import CounterDB
from config import config_import as conf
# from notifications.sms_notification import publish_to_topic

ENTRANCE_CONF = conf.get_config_data_by_key('entrance')
CAPACITY = conf.get_config_data_by_key('CAPACITY')


class Tracker:
    """a class for tracking multiple objects

    Attributes:
        trackableObjects (dict): Dictionary of (ID - trackable object)
            key/value paits
        ct (CentroidTracker): CentroidTracker object
        people (int): Number of people in the frame
        DB (CounterDB): Database object
    """

    def __init__(self, track_in=True, maxDisappeared=5):
        """
        Args:
            track_in (bool): Flag to track people going in or out
            maxDissapeared (int): Number of consecutive missed frames to
                assume it dissapeared
        """
        self.trackableObjects = {}
        self.ct = CentroidTracker(maxDisappeared=maxDisappeared)
        self.track_in = track_in
        self.old_len = 0
        self.people = 0
        self.DB = CounterDB()
        self.timer = 0

    def track_object(self, frame_stamp, boxes, image,
                     threshold=0, debug=False):
        """
        Track objects, whether they have been counted in or not
        and update database information according to new entrances

        Args:
            frame_stamp (int): timestamp of frame
            boxes (list): Boxes of detected humans on frame
            image (array): Current frame (used only for debug purposes)
            threshold (int): Threshold line for in and out directions
            debug (bool): Flag for debugging
        """
        people_in = self.DB.in_count()
        people_out = self.DB.out_count()

        objects = self.ct.update(boxes)
        if len(objects) > self.old_len:
            self.people = len(objects)

        # people_currently_in = self.DB.in_current()

        # loop over the tracked objects
        for (objectID, centroid) in objects.items():
            # check to see if a trackable object exists for the current
            # object ID
            to = self.trackableObjects.get(objectID, None)
            # if there is no existing trackable object, create one
            if to is None:
                to = TrackableObject(objectID, centroid)
            # otherwise, there is a trackable object so we can utilize it
            # to determine direction
            else:
                # check to see if the object has been counted or
                # if there is a change in its direction
                if not to.counted:
                    to.counted = True
                    if centroid[1] > threshold:
                        to.start_point = 'down'
                    else:
                        to.start_point = 'up'

                print(f'total people: {people_in-people_out}')
                # the difference between the y-coordinate
                # of the current centroid & the mean
                # of previous centroids will tell us in
                # which direction the object is moving
                # (negative for 'up' & positive for 'down')
                y = [c[1] for c in to.centroids]
                direction = centroid[1] - np.mean(y)
                to.centroids.append(centroid)
                
                # Define the direction towards that the person
                # is walking to & update it on the obj instance
                if direction > 0 and centroid[1] > threshold:
                    to.direction = 'in'
                elif direction < 0 and centroid[1] < threshold:
                    to.direction = 'out'

                # If the new direction of the object is
                # different to its previous direction
                # update the people counter
                if to.direction != to.prev_direction:
                    # A person has just walked in
                    if to.direction == 'in' and to.start_point != 'down':
                        people_in += 1
                        to.prev_direction = 'in'
                        to.start_point = 'up'
                    # A person has just walked out
                    elif to.direction == 'out' and to.start_point != 'up':
                        to.prev_direction = 'out'
                        people_out += 1
                        to.start_point = 'down'

            # store the trackable object in our dictionary
            self.trackableObjects[objectID] = to

            # draw both the ID of the object and the centroid of the
            # object on the output frame
            # draw both the ID of the object and the centroid of the
            # object on the output frame
            if debug:
                text = "ID {}".format(objectID)
                cv2.putText(image, text, (centroid[0] - 10, centroid[1] - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                cv2.circle(image, (centroid[0], centroid[1]),
                           4, (0, 255, 0), -1)
        if people_out > people_in:
            people_out = people_in
        # update database information about total number
        # of people that entered/left the given space
        self.DB.update_out(people_out)
        self.DB.update_in(people_in)
