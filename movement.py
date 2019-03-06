import numpy as np
import cv2 as cv


def get_direction_vector(bin_img):
    """
    Assumes:
    - the input image has index [0, 0] in the upper left
    - a pixel can be accessed by img[x][y]
    - x is the horizontal axis and increase from left to right
    - y is the vertical axis and increase from top to bottom

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
    print(img_h, img_w)
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
        print(number, avg_x, avg_y)
        return np.array([avg_x-img_w//2, avg_y-img_h//2])
    else:
        # image is all black, so don't move
        return np.zeros([2])


# testing image
img = cv.imread("test.png", cv.IMREAD_COLOR)
bin_img = cv.inRange(img, np.array([250,100,150]), np.array([255,255,255]))
cv.imshow("threshold", bin_img)
img_h, img_w = img.shape[:2]
# location of the image center in Blue
cv.circle(img, (img_w//2, img_h//2), 10, (255,0,0), 2)
vec = get_direction_vector(bin_img)
# location of the COG in Green
cv.circle(img, (int(vec[0])+img_w//2, int(vec[1])+img_h//2), 10, (0,255,0), 2)
cv.imshow("COG", img)

cv.waitKey(0)
cv.destroyAllWindows()
