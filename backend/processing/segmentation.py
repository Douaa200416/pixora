import cv2
import numpy as np
import os
import urllib.request


def apply_segmentation(path, method, params={}):
    img = cv2.imread(path)

    if img is None:
        raise ValueError("Image not loaded")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    if method == 'threshold':
        thresh_type = params.get('thresh_type', 'simple')
        t1 = int(params.get('thresh1', 127))
        t2 = int(params.get('thresh2', 200))
        t3 = int(params.get('thresh3', 192))

        if thresh_type in ['simple', 'global']:
            _, result = cv2.threshold(gray, t1, 255, cv2.THRESH_BINARY)

        elif thresh_type == 'double':
            result = np.zeros_like(gray)
            result[(gray >= t1) & (gray <= t2)] = 255

        elif thresh_type == 'multi':
            result = np.zeros_like(gray)
            result[gray >= t1] = 85
            result[gray >= t2] = 170
            result[gray >= t3] = 255

        elif thresh_type == 'otsu':
            _, result = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        elif thresh_type in ['local', 'adaptive']:
            result = cv2.adaptiveThreshold(gray, 255,
                         cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                         cv2.THRESH_BINARY, 11, 2)
        else:
            _, result = cv2.threshold(gray, t1, 255, cv2.THRESH_BINARY)

        result = cv2.cvtColor(result, cv2.COLOR_GRAY2BGR)
        return result

    elif method == 'roberts':
        kernel_x = np.array([[1, 0], [0, -1]], dtype=np.float32)
        kernel_y = np.array([[0, 1], [-1, 0]], dtype=np.float32)
        gx = cv2.filter2D(gray.astype(np.float32), -1, kernel_x)
        gy = cv2.filter2D(gray.astype(np.float32), -1, kernel_y)
        result = np.sqrt(gx**2 + gy**2)
        result = np.clip(result, 0, 255).astype(np.uint8)
        return cv2.cvtColor(result, cv2.COLOR_GRAY2BGR)

    elif method == 'prewitt':
        kernel_x = np.array([[-1, 0, 1], [-1, 0, 1], [-1, 0, 1]], dtype=np.float32)
        kernel_y = np.array([[-1, -1, -1], [0, 0, 0], [1, 1, 1]], dtype=np.float32)
        gx = cv2.filter2D(gray.astype(np.float32), -1, kernel_x)
        gy = cv2.filter2D(gray.astype(np.float32), -1, kernel_y)
        result = np.clip(np.sqrt(gx**2 + gy**2), 0, 255).astype(np.uint8)
        return cv2.cvtColor(result, cv2.COLOR_GRAY2BGR)

    elif method == 'sobel':
        gx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        gy = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        result = cv2.convertScaleAbs(np.sqrt(gx**2 + gy**2))
        return cv2.cvtColor(result, cv2.COLOR_GRAY2BGR)

    elif method == 'canny':
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        result = cv2.Canny(blurred, threshold1=50, threshold2=150)
        return cv2.cvtColor(result, cv2.COLOR_GRAY2BGR)

    elif method == 'laplacian':
        lap = cv2.Laplacian(gray, cv2.CV_64F)
        result = cv2.convertScaleAbs(lap)
        return cv2.cvtColor(result, cv2.COLOR_GRAY2BGR)

    elif method == 'log':
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        log = cv2.Laplacian(blurred, cv2.CV_64F)
        result = cv2.convertScaleAbs(log)
        return cv2.cvtColor(result, cv2.COLOR_GRAY2BGR)

    elif method == 'snake':
        try:
            from skimage.segmentation import active_contour
            from skimage.filters import gaussian

            s = np.linspace(0, 2 * np.pi, 400)
            cx = gray.shape[1] // 2
            cy = gray.shape[0] // 2
            r = min(cx, cy) * 0.6
            init = np.array([cy + r * np.sin(s),
                             cx + r * np.cos(s)]).T

            snake = active_contour(
                gaussian(gray.astype(np.float32) / 255, sigma=3),
                init, alpha=0.015, beta=10, gamma=0.001
            )

            result = img.copy()
            pts = snake.astype(np.int32)
            for i in range(len(pts) - 1):
                cv2.line(result, (pts[i][1], pts[i][0]),
                         (pts[i+1][1], pts[i+1][0]), (0, 255, 100), 2)
            return result
        except Exception:
            return img

    elif method == 'region_growing':
        result = _region_growing(gray)
        return cv2.cvtColor(result, cv2.COLOR_GRAY2BGR)

    elif method == 'split_merge':
        result = _split_merge(gray)
        return cv2.cvtColor(result, cv2.COLOR_GRAY2BGR)

    elif method in ['erosion', 'dilation', 'opening', 'closing']:
        shape_map = {
            'rect':    cv2.MORPH_RECT,
            'cross':   cv2.MORPH_CROSS,
            'ellipse': cv2.MORPH_ELLIPSE
        }
        se_shape = shape_map.get(params.get('morphShape', 'rect'), cv2.MORPH_RECT)
        se_size = int(params.get('morphSize', 3))
        kernel = cv2.getStructuringElement(se_shape, (se_size, se_size))

        morph_ops = {
            'erosion':  cv2.MORPH_ERODE,
            'dilation': cv2.MORPH_DILATE,
            'opening':  cv2.MORPH_OPEN,
            'closing':  cv2.MORPH_CLOSE,
        }
        result = cv2.morphologyEx(img, morph_ops[method], kernel)
        return result

    elif method == 'kmeans':
        K = int(params.get('k', 3))
        pixels = img.reshape(-1, 3).astype(np.float32)
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.2)
        _, labels, centers = cv2.kmeans(
            pixels, K, None, criteria, 10,
            cv2.KMEANS_RANDOM_CENTERS
        )
        centers = np.uint8(centers)
        result = centers[labels.flatten()].reshape(img.shape)
        return result

    elif method == 'fcm':
        try:
            import skfuzzy as fuzz
            K = int(params.get('k', 3))
            pixels = img.reshape(-1, 3).astype(np.float64).T
            cntr, u, *_ = fuzz.cluster.cmeans(
                pixels, K, 2, error=0.005, maxiter=100
            )
            labels = np.argmax(u, axis=0)
            centers = np.uint8(cntr)
            result = centers[labels].reshape(img.shape)
            return result
        except ImportError:
            return apply_segmentation(path, 'kmeans', params)

    elif method == 'pcm':
        try:
            import skfuzzy as fuzz
            K = int(params.get('k', 3))
            pixels = img.reshape(-1, 3).astype(np.float64).T
            cntr, u, *_ = fuzz.cluster.cmeans(
                pixels, K, 2, error=0.005, maxiter=100
            )
            labels = np.argmax(u, axis=0)
            centers = np.uint8(cntr)
            result = centers[labels].reshape(img.shape)
            return result
        except ImportError:
            return apply_segmentation(path, 'kmeans', params)

    elif method == 'deeplearning':
        # PASCAL VOC 21-class color palette
        PALETTE = np.array([
            [0,   0,   0  ], [128, 0,   0  ], [0,   128, 0  ], [128, 128, 0  ],
            [0,   0,   128], [128, 0,   128], [0,   128, 128], [128, 128, 128],
            [64,  0,   0  ], [192, 0,   0  ], [64,  128, 0  ], [192, 128, 0  ],
            [64,  0,   128], [192, 0,   128], [64,  128, 128], [192, 128, 128],
            [0,   64,  0  ], [128, 64,  0  ], [0,   192, 0  ], [128, 192, 0  ],
            [0,   64,  128]
        ], dtype=np.uint8)

        MODEL_PATH = "model_fcn.onnx"
        MODEL_URL  = (
            "https://github.com/onnx/models/raw/main/validated/"
            "vision/object_detection_segmentation/fcn-resnet50/"
            "model/fcn-resnet50-11.onnx"
        )

        # --- Download model once, cache locally ---
        if not os.path.exists(MODEL_PATH):
            try:
                print("[deeplearning] Downloading FCN-ResNet50 (~50 MB) — first run only...")
                urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
                print("[deeplearning] Model downloaded and cached.")
            except Exception as e:
                print(f"[deeplearning] Download failed ({e}). Using GrabCut fallback.")
                return _grabcut_segment(img)

        # --- Run inference ---
        try:
            h, w = img.shape[:2]

            # Per-channel ImageNet normalisation (mean/std in RGB order)
            mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
            std  = np.array([0.229, 0.224, 0.225], dtype=np.float32)

            inp = cv2.resize(img, (512, 512))
            inp = cv2.cvtColor(inp, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
            inp = (inp - mean) / std                      # HWC, normalised
            blob = inp.transpose(2, 0, 1)[np.newaxis]     # NCHW float32

            net = cv2.dnn.readNetFromONNX(MODEL_PATH)
            net.setInput(blob.astype(np.float32))
            out = net.forward()                           # (1, num_classes, H, W)

            # Argmax across class dimension → integer label map
            label_map = np.argmax(out[0], axis=0).astype(np.uint8)           # (H, W)
            label_map = cv2.resize(label_map, (w, h), interpolation=cv2.INTER_NEAREST)

            # Map labels → BGR colours
            colored_rgb = PALETTE[label_map % len(PALETTE)]                  # (H, W, 3) RGB
            colored_bgr = cv2.cvtColor(colored_rgb, cv2.COLOR_RGB2BGR)

            # Blend colour mask with original for visibility
            result = cv2.addWeighted(img, 0.45, colored_bgr, 0.55, 0)
            return result

        except Exception as e:
            print(f"[deeplearning] Inference failed ({e}). Using GrabCut fallback.")
            return _grabcut_segment(img)

    else:
        raise ValueError(f"Unknown segmentation method: {method}")


# ---------------------------------------------------------------------------
# Helper: improved GrabCut fallback
# ---------------------------------------------------------------------------

def _grabcut_segment(img):
    """
    Iterative GrabCut with morphological cleanup.
    Used as a graceful fallback when the ONNX model is unavailable.
    """
    h, w = img.shape[:2]
    margin_x = max(10, w // 8)
    margin_y = max(10, h // 8)
    rect = (margin_x, margin_y, w - 2 * margin_x, h - 2 * margin_y)

    mask      = np.zeros((h, w), np.uint8)
    bgd_model = np.zeros((1, 65), np.float64)
    fgd_model = np.zeros((1, 65), np.float64)

    # Initial pass with rect, then refine
    cv2.grabCut(img, mask, rect, bgd_model, fgd_model, 5, cv2.GC_INIT_WITH_RECT)
    cv2.grabCut(img, mask, None, bgd_model, fgd_model, 5, cv2.GC_EVAL)

    fg_mask = np.where(
        (mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 255, 0
    ).astype(np.uint8)

    # Morphological cleanup to smooth jagged edges
    kernel  = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel)
    fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN,  kernel)

    result = img.copy()
    result[fg_mask == 0] = 0
    return result


# ---------------------------------------------------------------------------
# Helper: region growing
# ---------------------------------------------------------------------------

def _region_growing(gray, seed=None, threshold=15):
    if seed is None:
        seed = (gray.shape[0] // 2, gray.shape[1] // 2)

    result   = np.zeros_like(gray)
    visited  = np.zeros_like(gray, dtype=bool)
    seed_val = int(gray[seed])

    queue = [seed]
    while queue:
        y, x = queue.pop(0)
        if visited[y, x]:
            continue
        visited[y, x] = True

        if abs(int(gray[y, x]) - seed_val) <= threshold:
            result[y, x] = 255
            for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                ny, nx = y + dy, x + dx
                if 0 <= ny < gray.shape[0] and 0 <= nx < gray.shape[1]:
                    if not visited[ny, nx]:
                        queue.append((ny, nx))
    return result


# ---------------------------------------------------------------------------
# Helper: split and merge
# ---------------------------------------------------------------------------

def _split_merge(gray, threshold=20):
    result = np.zeros_like(gray)
    h, w   = gray.shape
    bsize  = 16

    for y in range(0, h, bsize):
        for x in range(0, w, bsize):
            block = gray[y:y + bsize, x:x + bsize]
            if block.std() < threshold:
                result[y:y + bsize, x:x + bsize] = int(block.mean())
            else:
                result[y:y + bsize, x:x + bsize] = block

    return result