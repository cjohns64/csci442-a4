import numpy as np
import cv2 as cv


def get_direction_vector(bin_img):
    """
    Assumes the input image has index [0, 0] in the upper left,
    a pixel can be accessed by img[row][col],
    and rows increase from left to right, cols increase from top to bottom

    Finds the vector from the center of the image to the Center of Gravity of the given
    Binary image, the COG is found by averaging the locations of all the white pixels in the image
    :param bin_img: a binary image of the path, where the following path is white and the background is black
    :return: vector pointing in the direction of the COG from the center of the image
    """
    # get image size
    img_w, img_h = bin_img.shape

    # set up variables
    avg_row, avg_col = 0, 0
    number = 0
    for r in range(len(bin_img)):
        for c in range(len(bin_img[0])):
            # binary image so anything with a high value is taken as white
            if bin_img[r][c] > 255/2:
                avg_row += r
                avg_col += c
                number += 1
    # check that the image is not all black
    if number > 0:
        avg_row = np.round(avg_row / number - img_w/2, 0)
        avg_col = np.round(avg_col / number - img_h/2, 0)
        # return the movement vector, positive col = move forward, positive row = turn right
        return np.array([avg_row, -avg_col])
    else:
        # image is all black, so don't move
        return np.zeros([2])
