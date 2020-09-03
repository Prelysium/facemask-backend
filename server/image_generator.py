class ImageGenerator:
    def __init__(self):
        self.image_id = 0
        self.image_dic = {}
        self.image_name_dic = {}

    def get_image_id(self):
        temp = self.image_id
        self.image_id += 1
        return temp

    def add_image(self, image_id, image, name):
        self.image_dic[str(image_id)] = image
        self.image_name_dic[str(image_id)] = name

    def get_image(self, image_id):
        return self.image_dic[image_id]

    def get_image_name(self, image_id):
        return self.image_name_dic[image_id]
