import cv2
import numpy as np

PADDING_MAP = {
    'zeros':     cv2.BORDER_CONSTANT,   
    'mirror':    cv2.BORDER_REFLECT,    
    'replicate': cv2.BORDER_REPLICATE, 
}


def apply_filter(path, filter_type, kernel=3, padding='zeros'):
    img        = cv2.imread(path)
    original   = img.copy()
    border     = PADDING_MAP.get(padding, cv2.BORDER_CONSTANT)
    k          = int(kernel)

    if filter_type == 'mean':
        result = cv2.blur(img, (k, k),
                          borderType=border)

    elif filter_type == 'gaussian_f':
        result = cv2.GaussianBlur(img, (k, k), sigmaX=0,
                                  borderType=border)

    elif filter_type == 'median':
        result = cv2.medianBlur(img, k)

    elif filter_type == 'sharpen':
        sharpen_kernel = np.array([[ 0, -1,  0],
                                   [-1,  5, -1],
                                   [ 0, -1,  0]], dtype=np.float32)
        result = cv2.filter2D(img, -1, sharpen_kernel,
                              borderType=border)

    elif filter_type == 'laplacian_f':
        laplacian = cv2.Laplacian(img, cv2.CV_64F)
        result = cv2.convertScaleAbs(laplacian)

    elif filter_type == 'unsharp':
        blurred = cv2.GaussianBlur(img, (k, k), sigmaX=0)
        result  = cv2.addWeighted(img, 1.5, blurred, -0.5, 0)

  

    elif filter_type == 'knn':
        result = _knn_filter(img, k)

    elif filter_type == 'snn':
        result = _snn_filter(img, k)

    elif filter_type == 'sigma':
        result = _sigma_filter(img, k)

    else:
        result = img

    metrics = compute_metrics_arrays(original, result)
    return result, metrics

def _knn_filter(img, k=3):

    result = img.copy().astype(np.float32)
    pad    = k // 2
    padded = cv2.copyMakeBorder(img, pad, pad, pad, pad, cv2.BORDER_REFLECT)

    for i in range(img.shape[0]):
        for j in range(img.shape[1]):
            center    = img[i, j].astype(np.float32)
            neighbors = padded[i:i+k, j:j+k].reshape(-1, img.shape[2]).astype(np.float32)
            
            dists     = np.sqrt(np.sum((neighbors - center) ** 2, axis=1))
            kn        = max(1, len(dists) // 2)
            closest   = neighbors[np.argsort(dists)[:kn]]
            result[i, j] = np.mean(closest, axis=0)

    return np.clip(result, 0, 255).astype(np.uint8)

def _snn_filter(img, k=3):
    result = img.copy().astype(np.float32)
    pad    = k // 2
    padded = cv2.copyMakeBorder(img, pad, pad, pad, pad, cv2.BORDER_REFLECT)

    for i in range(img.shape[0]):
        for j in range(img.shape[1]):
            center = img[i, j].astype(np.float32)
            win    = padded[i:i+k, j:j+k].astype(np.float32)
            flipped = win[::-1, ::-1]
            diff_orig   = np.abs(win    - center).sum(axis=2)
            diff_flipped = np.abs(flipped - center).sum(axis=2)
            chosen = np.where(diff_orig < diff_flipped, 1, 0)
            selected = np.where(chosen[:,:,np.newaxis], win, flipped)
            result[i, j] = np.mean(selected.reshape(-1, img.shape[2]), axis=0)

    return np.clip(result, 0, 255).astype(np.uint8)

def _sigma_filter(img, k=3, sigma=20):
    result = img.copy().astype(np.float32)
    pad    = k // 2
    padded = cv2.copyMakeBorder(img, pad, pad, pad, pad, cv2.BORDER_REFLECT)

    for i in range(img.shape[0]):
        for j in range(img.shape[1]):
            center    = img[i, j].astype(np.float32)
            neighbors = padded[i:i+k, j:j+k].reshape(-1, img.shape[2]).astype(np.float32)
            # Only keep neighbors within sigma range
            dists   = np.abs(neighbors - center).sum(axis=1)
            within  = neighbors[dists <= sigma]
            if len(within) > 0:
                result[i, j] = np.mean(within, axis=0)
            else:
                result[i, j] = center

    return np.clip(result, 0, 255).astype(np.uint8)



def compute_metrics(path1, path2):
    
    img1 = cv2.imread(path1).astype(np.float32)
    img2 = cv2.imread(path2).astype(np.float32)
    img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))
    return compute_metrics_arrays(img1, img2)


def compute_metrics_arrays(original, processed):
    o = original.astype(np.float32)
    p = processed.astype(np.float32)

    if o.shape != p.shape:
        p = cv2.resize(p, (o.shape[1], o.shape[0]))
    mse = float(np.mean((o - p) ** 2))
    if mse == 0:
         psnr = 999.99 
    else:
        psnr = float(10 * np.log10((255 ** 2) / mse))

    result = {
        'mse':  round(mse, 4),
        'psnr': round(psnr, 2)
    }

    if len(o.shape) == 3 and o.shape[2] == 3:
        mse_b = float(np.mean((o[:,:,0] - p[:,:,0]) ** 2))
        mse_g = float(np.mean((o[:,:,1] - p[:,:,1]) ** 2))
        mse_r = float(np.mean((o[:,:,2] - p[:,:,2]) ** 2))
        mse_rgb = (mse_r + mse_g + mse_b) / 3

        psnr_b = 10 * np.log10(255**2 / mse_b)   if mse_b > 0 else 999
        psnr_g = 10 * np.log10(255**2 / mse_g)   if mse_g > 0 else 999
        psnr_r = 10 * np.log10(255**2 / mse_r)   if mse_r > 0 else 999

        result['mse_r']   = round(mse_r, 4)
        result['mse_g']   = round(mse_g, 4)
        result['mse_b']   = round(mse_b, 4)
        result['mse_rgb'] = round(mse_rgb, 4)
        result['psnr_r']  = round(float(psnr_r), 2)
        result['psnr_g']  = round(float(psnr_g), 2)
        result['psnr_b']  = round(float(psnr_b), 2)

    return result
