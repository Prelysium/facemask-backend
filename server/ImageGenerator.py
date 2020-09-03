class ImageGenerator:
    """
    This class organizes images and videos uploaded from the server.
    It save them in dictionary by generated id and returns file when asked.
    Args:

    Attributes:
        image_id (int): the increasing id of the files.
        image_dic (dic): python dictionary to save file on the id. key(id), value(file).
        image_name_dic (dic): python dicionary to save file name on the id. key(id), value(filename).
    """

    def __init__(self):
        self.image_id = 0
        self.image_dic = {}
        self.image_name_dic = {}

    def get_image_id(self):
        """
        This method takes no argument. It increases id and returns the previous one.
        """
        temp = self.image_id
        self.image_id += 1
        return temp

    def add_image(self, image_id, image, name):
        """
        This method fills two python dictionary.
        1) id- file
        2) id- filename

        Args:
            image_id (int): generated image id
            image (object): python pillow object of the image.
            name (str): name of the image.
        """
        self.image_dic[str(image_id)] = image
        self.image_name_dic[str(image_id)] = name

    def get_image(self, image_id):
        """
        This method return image file on the id.
        Args:
            image_id (int): generated image id

        Returns:
            image file on the id.
        """
        return self.image_dic[image_id]

    def get_image_name(self, image_id):
        """
        This method return image name on the id.
        Args:
            image_id (int): generated image id

        Returns:
            image name on the id.
        """
        return self.image_name_dic[image_id]
