import numpy as np
import cv2 as cv
import maestro
import time


class LineFollow:
    """
    Assumptions:
    - images have index [0, 0] in the upper left
    - a pixel can be accessed by frame[x][y]
    - x is the horizontal axis and increase from left to right
    - y is the vertical axis and increase from top to bottom
    """

    def __init__(self, image_name=None):
        self.tango = maestro.Controller()
        # zero all motors
        self.body = 6000
        self.headTurn = 6000
        self.headTilt = 6000
        self.motors = 6000
        self.turn = 6000
        self.MOTORS = 1
        self.TURN = 2
        self.end = False

        self.image_name = image_name
        self.video_use = self.image_name is None
        # set video size variables to small, actual size is camera dependent
        self.frame_x = 200
        self.frame_y = 200
        self.frame_name = "Video"
        cv.namedWindow(self.frame_name)
        # some good starting values
        self.min_canny = 247
        self.max_canny = 255
        # # start Editing window
        cv.namedWindow("Editing")
        # # set up editing track bars
        cv.createTrackbar("max Canny", "Editing", self.max_canny, 255, self.change_slider_max_canny)
        cv.createTrackbar("min Canny", "Editing", self.min_canny, 255, self.change_slider_min_canny)

    def pi_cam_loop(self, image):
        """
        Runs 1 loop of the path detection given the current frame
        :param image: current frame to evaluate
        :return:
        """
        self.frame = image
        self.frame_y, self.frame_x = self.frame.shape[:2]
        ed = self.detect_line(self.frame)
        # get the direction vector
        vec = self.get_direction_vector(ed)
        # location of the COG in as a box
        rec_center = np.array((int(vec[0]) + self.frame_x // 2, int(vec[1]) + self.frame_y // 2))
        cv.rectangle(ed, tuple(rec_center - 4), tuple(rec_center + 4), 255)
        # draw line from origin to COG
        cv.line(ed, (self.frame_x // 2, self.frame_y // 2), tuple(rec_center), 255)

        # show frame
        cv.imshow(self.frame_name, ed)

    # def replace_part(self, img, replacement, offset_xy):
    #     # h, w = replacement.shape[:2]
    #     local_img = img.__copy__()
    #     for y in range(len(replacement)):
    #         for x in range(len(replacement[0])):
    #             local_img[y + offset_xy[1]][x + offset_xy[0]] = replacement[y][x]
    #
    #     return local_img

    def detect_line(self, image):
        """
        Reduces image to binary edge detection
        :param image: image to reduce, non-destructive
        :return: reduced image
        """
        edges = np.zeros(image.shape, np.uint8)
        edges = cv.GaussianBlur(edges, (9, 9), cv.BORDER_DEFAULT)
        # normalize image, this is for changing room lighting
        cv.normalize(image, edges, 0, 255, cv.NORM_MINMAX)
        # edge detection
        edges = cv.Canny(edges, self.min_canny, self.max_canny)
        edges = cv.dilate(edges, np.ones((2, 2)))
        return edges

    def perform_movement(self):
        """
        Gets the motor commands needed for the current camera image
        and tells the motors to move
        :return:
        """
        # detect_line
        line_image = self.detect_line(self.frame)
        # get direction
        x_v, y_v = self.get_direction_vector(line_image)
        # move
        self.motor_control_from_dir(x_v, y_v)

    def get_direction_vector(self, bin_img):
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
            if number >= img_h * img_w // 6:
                # we probably ran off the path since >25% of the screen is white
                self.end = True
            avg_x = np.round(avg_x / number, 0)
            avg_y = np.round(avg_y / number, 0)
            # return the movement vector, positive col = move forward, positive row = turn right
            return np.array([avg_x-img_w//2, avg_y-img_h])  # origin at center, bottom
        else:
            # image is all black, so don't move
            return np.zeros([2])

    @staticmethod
    def relative_speed_mod(action_value, current_level):
        """
        Finds if the action should increase or decrease
        :param action_value: the value of the intent
        :param current_level: the value of the current action
        :return: True if the action should increase, False if it should decrease
        """
        if action_value > 0:
            # increase action to more positive values
            return action_value * 150 + 6000 > current_level
        else:
            # increase action to more negative values
            return action_value * 150 + 6000 < current_level

    def motor_control_from_dir(self, x_scale, y_scale):
        """
        - left-right directions are unknown

        Generates a motor command from the COG vector
        :param x_scale: horizontal component of the COG vector
        :param y_scale: vertical component of the COG vector
        :return: None
        """
        left = False
        right = False
        forward = False

        min_turn_div = 0  # |x_scale| or |y_scale| must be larger then this for any action to happen
        min_forward_div = 15

        if np.abs(x_scale) > np.abs(y_scale):
            # turning wins
            if x_scale > min_turn_div:
                # want to go right
                # should we speed up or slow down
                # right = self.relative_speed_mod(x_scale, self.turn)
                right = True
            elif x_scale < -min_turn_div:
                # want to go left
                # should we speed up or slow down
                # left = self.relative_speed_mod(x_scale, self.turn)
                left = True
            else:
                # stop
                pass
        else:
            # forward wins
            if np.abs(y_scale) > min_forward_div:
                # go forward if deviation is large enough
                forward = True
            else:
                # stop
                pass

        burst = 9
        for i in range(burst):
            if i == burst-1 or (i >= burst - 2 and (right or left)):
                left = False
                right = False
                forward = False
            if forward:
                self.motors -= 200
                if self.motors < 2300:
                    self.motors = 2400
                self.tango.setTarget(self.MOTORS, self.motors)

            elif left:
                self.turn += 200
                if self.turn > 7010:
                    self.turn = 7000
                self.tango.setTarget(self.TURN, self.turn)

            elif right:
                self.turn -= 200
                if self.turn < 3390:
                    self.turn = 3400
                self.tango.setTarget(self.TURN, self.turn)

            else:
                # stop
                self.motors = 6000
                self.turn = 6000
                self.tango.setTarget(self.MOTORS, self.motors)
                self.tango.setTarget(self.TURN, self.turn)
            time.sleep(0.1)

    def zero_motors(self):
        self.body = 6000
        self.headTurn = 6000
        self.headTilt = 6000
        self.motors = 6000
        self.turn = 6000

    def change_slider_max_canny(self, value):
        self.max_canny = value

    def change_slider_min_canny(self, value):
        self.min_canny = value

