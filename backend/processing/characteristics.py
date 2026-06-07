import cv2
import numpy as np
import os


def get_characteristics(path):
    
    img  = cv2.imread(path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    h, w     = img.shape[:2]
    channels = img.shape[2] if len(img.shape) == 3 else 1

    # Theoretical size = W × H × channels × bits per channel / 8
    theo_bytes = w * h * channels * 8 // 8
    real_bytes = os.path.getsize(path)

    # Luminance = average brightness 
    luminance = float(np.mean(gray))

    # Contrast=variance
    contrast = float(np.std(gray) ** 2)

    # Dynamic range 
    min_val = int(np.min(gray))
    max_val = int(np.max(gray))

    # standard based on resolution 
    if h >= 7680: standard = '8K Ultra-HD (7680×4320)'
    elif h >= 3840: standard = '4K Ultra-HD (3840×2160)'
    elif h >= 1920: standard = '1080p Full HD'
    elif h >= 1280: standard = '720p HD'
    elif h >= 640:  standard = '480p SD'
    else:           standard = 'Low Resolution'

    aliasing_risk = w < 800 or h < 600

    return {
        'width':         w,
        'height':        h,
        'channels':      channels,
        'theo_size_kb':  round(theo_bytes / 1024, 2),
        'real_size_kb':  round(real_bytes / 1024, 2),
        'luminance':     round(luminance, 2),
        'contrast':      round(contrast, 2),
        'min_intensity': min_val,
        'max_intensity': max_val,
        'standard':      standard,
        'aliasing_risk': aliasing_risk,
        'tonal':         '8-bit (256 levels)',
        'format_type':   'Bitmap'
    }
