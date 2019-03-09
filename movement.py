import numpy as np
import cv2 as cv
from multiprocessing import Process


class LineFollow:
    """
    Assumptions:
    - images have index [0, 0] in the upper left
    - a pixel can be accessed by img[x][y]
    - x is the horizontal axis and increase from left to right
    - y is the vertical axis and increase from top to bottom
    """

    def __init__(self, image_name):
        cv.namedWindow("Editing")
        # testing image
        self.img = cv.imread(image_name, cv.IMREAD_COLOR)
        # some good starting values
        self.min_canny = 105
        self.max_canny = 225

        # set up editing track bars
        cv.createTrackbar("max Canny", "Editing", self.max_canny, 255, self.change_slider_max_canny)
        cv.createTrackbar("min Canny", "Editing", self.min_canny, 255, self.change_slider_min_canny)

        while True:
            ed = self.detect_line(self.img)
            # bin_img = cv.inRange(img, np.array([250,100,150]), np.array([255,255,255]))

            # img_h, img_w = self.img.shape[:2]
            # # location of the image center in Blue
            # cv.circle(self.img, (img_w // 2, img_h // 2), 10, (255, 0, 0), 2)
            # vec = LineFollow.get_direction_vector(ed)
            # # location of the COG in Green
            # cv.circle(self.img, (int(vec[0]) + img_w // 2, int(vec[1]) + img_h // 2), 10, (0, 255, 0), 2)
            # cv.imshow("COG", self.img)
            cv.imshow("line detection", ed)

            k = cv.waitKey(1)
            # this is the "esc" key
            if k == 27:
                break
        cv.destroyAllWindows()

    def detect_line(self, image):
        """
        Reduces image to binary edge detection
        :param image: image to reduce, non-destructive
        :return: reduced image
        """
        edges = np.zeros(image.shape, np.uint8)
        # normalize image
        cv.normalize(image, edges, 0, 255, cv.NORM_MINMAX)
        # edge detection
        edges = cv.Canny(edges, self.min_canny, self.max_canny)
        # make lines thicker
        edges = cv.dilate(edges, np.ones((2, 2)), iterations=1)
        return edges

    def get_movement(self):
        """
        Gets the motor commands needed for the current camera image
        :return:
        """
        # detect_line
        line_image = self.detect_line(self.img)
        
        # get direction vector
        vec = self.get_direction_vector(line_image)

        # get motor commands
        pass

    @staticmethod
    def get_direction_vector(bin_img):
        """
        Finds the vector from the center of the image to the Center of Gravity of the given
        Binary image, the COG is found by averaging the locations of all the white pixels in the image
        :param bin_img: a binary image of the path, where the following path is white and the background is black
        :return: vector pointing in the direction of the COG from the center of the image
        """
        # get image size
        img_h, img_w = bin_img.shape

        # set up variables
        avg_x, avg_y = 0, 0
        number = 0
        for y in range(len(bin_img)):
            for x in range(len(bin_img[0])):
                # binary image so anything with a high value is taken as white
                if bin_img[y][x] > 255/2:
                    avg_x += x
                    avg_y += y
                    number += 1
        # check that the image is not all black
        if number > 0:
            avg_x = np.round(avg_x / number, 0)
            avg_y = np.round(avg_y / number, 0)
            # return the movement vector, positive col = move forward, positive row = turn right
            return np.array([avg_x-img_w//2, avg_y-img_h//2])
        else:
            # image is all black, so don't move
            return np.zeros([2])

    def change_slider_max_canny(self, value):
        self.max_canny = value

    def change_slider_min_canny(self, value):
        self.min_canny = value


if __name__ == '__main__':
    p1 = Process(target=LineFollow, args=("images/001.png",))
    p2 = Process(target=LineFollow, args=("images/002.png",))
    p1.start()
    p2.start()
    p1.join()
    p2.join()