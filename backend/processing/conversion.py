import cv2
import numpy as np


def convert_image(path, mode, threshold=128):

    img = cv2.imread(path)

    if mode == 'grayscale':

        result = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
       #convert back to RGB
        result = cv2.cvtColor(result, cv2.COLOR_GRAY2BGR)

    elif mode == 'binary':
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, result = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY)
        result = cv2.cvtColor(result, cv2.COLOR_GRAY2BGR)

    elif mode == 'rgb':
        result = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        #for sending
        result = cv2.cvtColor(result, cv2.COLOR_RGB2BGR)

    elif mode == 'cmy':
        # CMY = Cyan, Magenta, Yellow
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB).astype(np.float32)
        cmy = 255 - rgb
        result = cv2.cvtColor(cmy.astype(np.uint8), cv2.COLOR_RGB2BGR)

    elif mode == 'cmyk':
        rgb = img[:, :, ::-1].astype(np.float32) / 255.0  # 0-1
        K = 1 - np.max(rgb, axis=2)      #black channel
        K3 = np.stack([K, K, K], axis=2)#copied in 3 channels

        # Avoid division by zero
        denom = np.where(K3 < 1, 1 - K3, 1)
        C = (1 - rgb[:,:,0] - K) / denom[:,:,0]
        M = (1 - rgb[:,:,1] - K) / denom[:,:,1]
        Y = (1 - rgb[:,:,2] - K) / denom[:,:,2]

        cmy_display = np.stack([C, M, Y], axis=2) * 255
        result = np.clip(cmy_display, 0, 255).astype(np.uint8)
        result = cv2.cvtColor(result, cv2.COLOR_RGB2BGR)

    elif mode == 'indexed':
        pixels = img.reshape(-1, 3).astype(np.float32)
        K = 64  #nb of colors 
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 0.5)
        _, labels, centers = cv2.kmeans(pixels, K, None, criteria, 5, cv2.KMEANS_RANDOM_CENTERS)
        centers = np.uint8(centers)
        result = centers[labels.flatten()].reshape(img.shape)

    else:
        raise ValueError("Unknown mode")
        result = img

    return result
