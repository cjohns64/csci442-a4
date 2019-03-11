# import the necessary packages
from picamera.array import PiRGBArray
from picamera import PiCamera
from movement import LineFollow
import time
import cv2

# initialize the camera and grab a reference to the raw camera capture
camera = PiCamera()
camera.resolution = (320, 240)  # (640, 480)
camera.framerate = 32
rawCapture = PiRGBArray(camera, size=(320, 240))

path_follow = LineFollow()  # get movement directions from this class

# allow the camera to warmup
time.sleep(0.1)

# capture frames from the camera
for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
    # grab the raw NumPy array representing the image, then initialize the timestamp
    # and occupied/unoccupied text
    image = frame.array

    # do one loop
    path_follow.pi_cam_loop(image)
    # get movement direction
    # move_right, move_forward = path_follow.get_movement()

    key = cv2.waitKey(1) & 0xFF
    # clear the stream in preparation for the next frame
    rawCapture.truncate(0)

    # if the `q` key was pressed, break from the loop
    if key == ord("q"):
            break
