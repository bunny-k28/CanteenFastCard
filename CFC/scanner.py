import os
import cv2
import numpy as np

from pyzbar.pyzbar import decode


def scan():
    cap = cv2.VideoCapture(0)
    data = ''

    while True:
        frame = cap.read()[-1]
        barcodes = decode(frame)

        for barcode in barcodes:
            data = barcode.data.decode('utf-8')
            print("Barcode data:", data)

            pts = np.array([barcode.polygon], np.int32)
            pts = pts.reshape((-1, 1, 2))

            cv2.polylines(frame, [pts], True, (0, 0, 255), 5)

            if data.__len__() == 7: return int(data)
            else: continue
        
        # Display the frame (flipped)
        cv2.flip(frame, 1, frame)
        cv2.imshow('Barcode Scanner', frame)

        # Exit if data is digit and length is 7
        if cv2.waitKey(1) == ord('q'):
            break