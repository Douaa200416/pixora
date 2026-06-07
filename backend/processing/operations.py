import cv2
import numpy as np

def apply_basic_op(path, params):
    img = cv2.imread(path)
    if img is None:
        raise ValueError(f"Could not read image: {path}")
    
    op = params.get('op', '')

    if op == 'crop':
        x = int(params.get('x', 0))
        y = int(params.get('y', 0))
        w = int(params.get('w', img.shape[1]))
        h = int(params.get('h', img.shape[0]))
        result = img[y:y+h, x:x+w]

    elif op == 'rotate':
        angle = float(params.get('angle', 90))
        direction = params.get('dir', 'cw')
        if direction == 'ccw':
            angle = -angle
        cx, cy = img.shape[1] // 2, img.shape[0] // 2
        M = cv2.getRotationMatrix2D((cx, cy), -angle, 1.0)
        result = cv2.warpAffine(img, M, (img.shape[1], img.shape[0]))

    elif op == 'translate':
        tx = int(params.get('tx', 0))
        ty = int(params.get('ty', 0))
        M = np.float32([[1, 0, tx], [0, 1, ty]])
        result = cv2.warpAffine(img, M, (img.shape[1], img.shape[0]))

    elif op == 'scale':
        new_w = int(params.get('width', img.shape[1]))
        new_h = int(params.get('height', img.shape[0]))
        result = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_LINEAR)

    elif op == 'flip':
        axis = params.get('axis', 'horizontal')
        if axis == 'horizontal':
            result = cv2.flip(img, 1)
        elif axis == 'vertical':
            result = cv2.flip(img, 0)
        else:
            result = cv2.flip(img, -1)

    elif op == 'symmetry':
        result = cv2.flip(img, -1)

    else:
        result = img

    return result


def apply_arithmetic(path1, path2, op, value=50):
    img1 = cv2.imread(path1)
    if img1 is None:
        raise ValueError(f"Could not read first image: {path1}")

    if op == 'negative':
        return cv2.bitwise_not(img1)

    if op == 'not':
        return cv2.bitwise_not(img1)

    if op == 'add_const':
        return cv2.add(img1, np.full_like(img1, value))

    if op == 'sub_const':
        return cv2.subtract(img1, np.full_like(img1, value))

    img2 = cv2.imread(path2)
    if img2 is None:
        raise ValueError(f"Second image not loaded. Please upload a second image first.")

    img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))

    if op == 'add_img':
        return cv2.add(img1, img2)

    if op == 'sub_img':
        return cv2.subtract(img1, img2)

    if op == 'and':
        return cv2.bitwise_and(img1, img2)

    if op == 'or':
        return cv2.bitwise_or(img1, img2)

    if op == 'nor':
        return cv2.bitwise_not(cv2.bitwise_or(img1, img2))

    if op == 'xor':
        return cv2.bitwise_xor(img1, img2)

    return img1