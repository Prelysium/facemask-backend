class TrackableObject:
    """
    A class for trackable object containing relevant information

    Attributes:
        objectID (int): ID of the object
        centroids (list): List of the object's centroids
        counted (bool): Flag whether the object was counted as going in or not
        direction (str): Direction of the object (in/out)
    """

    def __init__(self, objectID, centroid):
        """
        Args:
            objectID (int): ID of the object
            centroid (tuple): X,Y coordinates of the object centroid
        """
        # store the object ID, then initialize a list of centroids
        # using the current centroid
        self.objectID = objectID
        self.centroids = [centroid]
        # indicates whether object has been counted or not
        self.counted = False
        self.direction = ""
        self.prev_direction = ""
        self.start_point = ""
