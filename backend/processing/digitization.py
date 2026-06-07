import cv2
import numpy as np


def apply_digitization(path, sampling=100, quantization=8):
    
    img = cv2.imread(path)
    h, w = img.shape[:2]


    if sampling < 100:
        small_w = max(1, int(w * sampling / 100))
        small_h = max(1, int(h * sampling / 100))

        # Shrink the image 
        small = cv2.resize(img, (small_w, small_h), interpolation=cv2.INTER_NEAREST) #copy the value of the closest pixel

        # Stretch img back
        img = cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)

    # step = 256 / 2^bits

    if quantization < 8:
        levels = 2 ** quantization          
        step   = 256 // levels            
        #group values into blocks
        img = (img // step) * step # // floor div
        img = np.clip(img, 0, 255).astype(np.uint8)

    return img
