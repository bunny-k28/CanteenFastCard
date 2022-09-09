'''
Program to scan the BAR code
'''

import cv2
import tkinter as tk
import numpy as np

from PIL import Image, ImageTk
from pyzbar.pyzbar import decode


cam_window = cv2.VideoCapture(0)
cam_window.set(3, 640)
cam_window.set(4, 480)

data = str()


def scan():
    global data

    while True:
        _, img = cam_window.read()

        for qr in decode(img):
            data = qr.data.decode('utf-8')
            # print(data)

            pts = np.array([qr.polygon], np.int32)
            pts = pts.reshape((-1, 1, 2))

            cv2.polylines(img, [pts], True, (0, 0, 255), 5)

            pts2 = qr.rect

            cv2.putText(img, data, (pts2[0], pts2[1]), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
        
            return int(data)

        cv2.flip(img, 1, img)

        cv2.imshow('QR Scanner', img)
        if cv2.waitKey(1) == (data.__len__() == 7):
            break


