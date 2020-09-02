

class ImageGenerator():
    def __init__(self):
        self.image_id = 0
        self.image_dic = {}

    def get_image_id(self):
        temp = self.image_id
        self.image_id += 1
        return temp

    def add_image(self, image_id, image):
        self.image_dic[str(image_id)] = image

    def get_image(self, image_id):
        return self.image_dic[image_id]
