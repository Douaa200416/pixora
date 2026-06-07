import cv2
import os

def compress_image(path, comp_type, quality=85):
    img = cv2.imread(path)
    original_size = os.path.getsize(path)

    base_dir = os.path.dirname(os.path.abspath(path))
    outputs_dir = os.path.join(base_dir, '..', 'outputs')
    os.makedirs(outputs_dir, exist_ok=True)  

    if comp_type == 'lossless':
        out_path = os.path.join(outputs_dir, 'compressed.png')
        cv2.imwrite(out_path, img, [cv2.IMWRITE_PNG_COMPRESSION, 9])
    else:
        out_path = os.path.join(outputs_dir, 'compressed.jpg')
        cv2.imwrite(out_path, img, [cv2.IMWRITE_JPEG_QUALITY, quality])

    out_path = os.path.abspath(out_path)  

    compressed_size = os.path.getsize(out_path)
    stats = {
        'original_size':   round(original_size / 1024, 2),
        'compressed_size': round(compressed_size / 1024, 2),
        'ratio':           round(original_size / max(compressed_size, 1), 2)
    }

    return out_path, stats