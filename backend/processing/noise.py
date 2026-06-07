import cv2
import numpy as np


def add_noise(path, noise_type, param=10):

    img = cv2.imread(path).astype(np.float32)

    if noise_type == 'gaussian':
        variance = param / 1000.0        
        sigma    = variance ** 0.5      
        noise    = np.random.normal(0, sigma * 255, img.shape)
        result   = img + noise

    elif noise_type == 'impulse':
        result  = img.copy()
        percent = param / 100.0
        total   = img.shape[0] * img.shape[1]

        n_salt = int(total * percent / 2)
        salt_coords = [np.random.randint(0, i, n_salt) for i in img.shape[:2]]
        result[salt_coords[0], salt_coords[1]] = 255

        n_pepper = int(total * percent / 2)
        pepper_coords = [np.random.randint(0, i, n_pepper) for i in img.shape[:2]]
        result[pepper_coords[0], pepper_coords[1]] = 0

    elif noise_type == 'speckle':
        #  result = image + image * noise
 
        intensity = param / 100.0
        noise  = np.random.randn(*img.shape) * intensity
        result = img + img * noise

    elif noise_type == 'poisson':
        scale  = param / 10.0
        noisy  = np.random.poisson(img / 255.0 * scale) / scale * 255
        result = noisy

    elif noise_type == 'periodic':
       
        freq   = param / 10.0
        h, w   = img.shape[:2]
 
        x      = np.arange(w)
        wave   = 30 * np.sin(2 * np.pi * freq * x / w)
        pattern = np.tile(wave, (h, 1))
        
        if len(img.shape) == 3:
            pattern = np.stack([pattern] * 3, axis=2)
        result = img + pattern

    else:
        result = img
    result = np.clip(result, 0, 255).astype(np.uint8)
    return result
