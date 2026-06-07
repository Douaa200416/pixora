import cv2
import numpy as np

def process_histogram(path, action, params={}):

    img = cv2.imread(path)

    if img is None:
        return {
            "error": "Image not found or OpenCV failed to read it",
            "path": path
        }

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    if action == 'show':

        hist = cv2.calcHist([gray], [0], None, [256], [0, 256]).flatten().tolist()

        mean_val = float(np.mean(gray))
        std_val  = float(np.std(gray))
        min_val  = int(np.min(gray))
        max_val  = int(np.max(gray))

        under = float(np.sum(gray < 64)) / gray.size
        over  = float(np.sum(gray > 192)) / gray.size

        return {
            "histogram": hist,
            "mean": round(mean_val, 2),
            "std": round(std_val, 2),
            "min": min_val,
            "max": max_val,
            "underexposed": under > 0.6,
            "overexposed": over > 0.6,
            "global_contrast": round(std_val ** 2, 2)
        }

    elif action == 'stretch':
        min_val = np.min(gray)
        max_val = np.max(gray)

        result = img.astype(np.float32)
        if max_val > min_val:
            result = (result - min_val) / (max_val - min_val) * 255

        return np.clip(result, 0, 255).astype(np.uint8)

    elif action == 'equalize':
        ycrcb = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
        ycrcb[:, :, 0] = cv2.equalizeHist(ycrcb[:, :, 0])
        return cv2.cvtColor(ycrcb, cv2.COLOR_YCrCb2BGR)

    elif action == 'local_contrast':

        x = int(params.get('x', 0))
        y = int(params.get('y', 0))
        w = int(params.get('w', 100))
        h = int(params.get('h', 100))

        region = gray[y:y+h, x:x+w]

        return {
            "local_mean": round(float(np.mean(region)), 2),
            "local_std": round(float(np.std(region)), 2),
            "local_contrast": round(float(np.std(region) ** 2), 2),
            "region": f"({x},{y}) → ({x+w},{y+h})"
        }

    return {"error": "Invalid histogram action"}