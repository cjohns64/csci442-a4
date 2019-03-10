import numpy as np
import cv2 as cv
from multiprocessing import Process


class LineFollow:
    """
    Assumptions:
    - images have index [0, 0] in the upper left
    - a pixel can be accessed by frame[x][y]
    - x is the horizontal axis and increase from left to right
    - y is the vertical axis and increase from top to bottom
    """

    def __init__(self, image_name=None):
        video_use = image_name is None
        # set video size variables to small, actual size is camera dependent
        self.frame_x = 200
        self.frame_y = 200
        self.frame_name = "Video"
        cv.namedWindow(self.frame_name)
        cv.namedWindow("Editing")

        # start video
        if not video_use:
            # do testing image
            self.frame = cv.imread(image_name)
            cv.resize(self.frame, (self.frame_x, self.frame_y), self.frame)
            self.frame_y, self.frame_x = self.frame.shape[:2]
        else:
            cap = cv.VideoCapture(0)
            cap.set(cv.CAP_PROP_FRAME_WIDTH, self.frame_x)
            cap.set(cv.CAP_PROP_FRAME_HEIGHT, self.frame_y)

        # some good starting values
        self.min_canny = 105
        self.max_canny = 225

        # set up editing track bars
        cv.createTrackbar("max Canny", "Editing", self.max_canny, 255, self.change_slider_max_canny)
        cv.createTrackbar("min Canny", "Editing", self.min_canny, 255, self.change_slider_min_canny)

        while True:
            # get video frame
            if video_use:
                _, self.frame = cap.read()
                self.frame_y, self.frame_x = self.frame.shape[:2]
            # start path detection
            ed = self.detect_line(self.frame)
            # get the direction vector
            vec = LineFollow.get_direction_vector(ed)
            # location of the COG in as a box
            rec_center = np.array((int(vec[0]) + self.frame_x // 2, int(vec[1]) + self.frame_y // 2))
            cv.rectangle(ed, tuple(rec_center - 4), tuple(rec_center + 4), 255)
            # draw line from origin to COG
            cv.line(ed, (self.frame_x//2, self.frame_y//2), tuple(rec_center), 255)

            # show frame
            cv.imshow(self.frame_name, ed)

            # exit when "esc" key is pressed
            k = cv.waitKey(1)
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
        # normalize image, this is for changing room lighting
        cv.normalize(image, edges, 0, 255, cv.NORM_MINMAX)
        # edge detection
        edges = cv.Canny(edges, self.min_canny, self.max_canny)
        return edges

    def get_movement(self):
        """
        Gets the motor commands needed for the current camera image
        :return:
        """
        # detect_line
        line_image = self.detect_line(self.frame)

        # get direction vector
        turn_scaler, forward_scaler = self.get_direction_vector(line_image)

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


def sample_image_testing():
    """
    Allows for easy controlled testing by replacing video input for 2 static images run in parallel
    :return: None
    """
    p1 = Process(target=LineFollow, args=("images/001.png",))
    p2 = Process(target=LineFollow, args=("images/002.png",))
    p1.start()
    p2.start()
    p1.join()
    p2.join()


if __name__ == '__main__':
    testing = False
    if testing:
        # use some sample images for testing
        sample_image_testing()
    else:
        # use the video for operation
        LineFollow()
