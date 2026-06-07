from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
import os
import io
from processing.conversion   import convert_image
from processing.digitization import apply_digitization
from processing.operations   import apply_basic_op, apply_arithmetic
from processing.histogram    import process_histogram
from processing.noise        import add_noise
from processing.filters      import apply_filter
from processing.segmentation import apply_segmentation
from processing.compression  import compress_image
from processing.characteristics import get_characteristics
 
app = Flask(__name__)
CORS(app, expose_headers=['X-Original-Size', 'X-Compressed-Size', 'X-Ratio'])
 
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
 
def save_uploaded(file):
    path = os.path.join(UPLOAD_FOLDER, 'current.png')
    file.save(path)
    return path
 
def save_second(file):
    path = os.path.join(UPLOAD_FOLDER, 'second.png')
    file.save(path)
    return path
def send_image(img_array):#to browser
    import cv2
    import numpy as np
    success, buffer = cv2.imencode('.png', img_array)
    return send_file(
        io.BytesIO(buffer.tobytes()),
        mimetype='image/png'
    )
 
@app.route('/ping', methods=['GET'])
def ping():
    return jsonify({'status': 'Pixora is running '})
 
 
@app.route('/upload', methods=['POST'])
def upload():
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400
    file = request.files['image']
    path = save_uploaded(file)
    import shutil
    shutil.copy(path, os.path.join(UPLOAD_FOLDER, 'original.png'))
    info = get_characteristics(path)
    return jsonify({'message': 'Image uploaded successfully', 'filename': file.filename, 'info': info})
 
@app.route('/upload_second', methods=['POST'])
def upload_second():
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400

    file = request.files['image']
    path = save_second(file)
    
    return jsonify({
        'message': 'Second image uploaded successfully',
        'filename': file.filename
    })
@app.route('/update', methods=['POST'])
def update():
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400
    file = request.files['image']
    path = os.path.join(UPLOAD_FOLDER, 'current.png')
    file.save(path)
    return jsonify({'message': 'Image updated'})
 
@app.route('/convert/<mode>', methods=['POST'])
def convert(mode):
    path = os.path.join(UPLOAD_FOLDER, 'original.png')
    threshold = int(request.form.get('threshold', 128))
    result = convert_image(path, mode, threshold)
    import cv2
    cv2.imwrite(os.path.join(UPLOAD_FOLDER, 'current.png'), result)
    return send_image(result)
    
@app.route('/digitize', methods=['POST'])
def digitize():
    path = os.path.join(UPLOAD_FOLDER, 'current.png')
    sampling    = int(request.form.get('sampling', 100))
    quantization = int(request.form.get('quantization', 8))
    result = apply_digitization(path, sampling, quantization)
    return send_image(result)
 
 
@app.route('/operations/basic', methods=['POST'])
def basic_op():
    path = os.path.join(UPLOAD_FOLDER, 'current.png')
    params = request.form.to_dict()
    result = apply_basic_op(path, params)
    return send_image(result)
 
 
@app.route('/operations/arithmetic', methods=['POST'])
def arithmetic():
    path1  = os.path.join(UPLOAD_FOLDER, 'current.png')
    path2  = os.path.join(UPLOAD_FOLDER, 'second.png')
    op     = request.form.get('op', 'negative')
    value  = request.form.get('value', 50)
    
    try:
        result = apply_arithmetic(path1, path2, op, int(value))
        return send_image(result)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Operation failed: {str(e)}'}), 500
 
 
@app.route('/histogram/<action>', methods=['POST'])
def histogram(action):
    path = os.path.join(UPLOAD_FOLDER, 'current.png')

    print("DEBUG PATH:", path)
    print("EXISTS:", os.path.exists(path))

    if not os.path.exists(path):
        return jsonify({"error": "No image uploaded yet"}), 400

    params = request.form.to_dict()

    try:
        result = process_histogram(path, action, params)

        # JSON outputs
        if action in ['show', 'local_contrast']:
            return jsonify(result)

        # image outputs (future use)
        return send_image(result)

    except Exception as e:
        print("HISTOGRAM ERROR:", e)
        return jsonify({
            "error": "Histogram processing failed",
            "details": str(e)
        }), 500
 
@app.route('/noise/add', methods=['POST'])
def noise():
    path       = os.path.join(UPLOAD_FOLDER, 'current.png')
    noise_type = request.form.get('type', 'gaussian')
    param      = float(request.form.get('param', 10))
    result     = add_noise(path, noise_type, param)
    return send_image(result)
 
@app.route('/filter/apply', methods=['POST'])
def filter_apply():
    path = os.path.join(UPLOAD_FOLDER, 'current.png')
    
    import shutil
    shutil.copy(path, os.path.join(OUTPUT_FOLDER, 'before_filter.png'))
    
    filter_type = request.form.get('filter', 'mean')
    kernel  = int(request.form.get('kernel', 3))
    padding = request.form.get('padding', 'zeros')
    result, metrics = apply_filter(path, filter_type, kernel, padding)
    import cv2
    cv2.imwrite(os.path.join(OUTPUT_FOLDER, 'filtered.png'), result)
    return send_image(result)
 
@app.route('/filter/metrics', methods=['POST'])
def filter_metrics():
    original_path = os.path.join(OUTPUT_FOLDER, 'before_filter.png')  
    filtered_path = os.path.join(OUTPUT_FOLDER, 'filtered.png')

    if not os.path.exists(original_path):
        return jsonify({'error': 'No original snapshot found'}), 400
    if not os.path.exists(filtered_path):
        return jsonify({'error': 'No filtered image found'}), 400

    from processing.filters import compute_metrics
    try:
        metrics = compute_metrics(original_path, filtered_path)
        return jsonify(metrics)
    except Exception as e:
        return jsonify({'error': f'Metrics computation failed: {str(e)}'}), 500
 
@app.route('/segmentation/<method>', methods=['POST'])
def segmentation(method):
    path   = os.path.join(UPLOAD_FOLDER, 'current.png')
    params = request.form.to_dict()
    result = apply_segmentation(path, method, params)
    return send_image(result)
 
@app.route('/compress', methods=['POST'])
def compress():
    path      = os.path.join(UPLOAD_FOLDER, 'current.png')
    comp_type = request.form.get('type', 'lossless')
    quality   = int(request.form.get('quality', 85))
    result_path, stats = compress_image(path, comp_type, quality)
    return send_file(
        result_path,
        as_attachment=True,
        download_name=f"compressed.{'png' if comp_type == 'lossless' else 'jpg'}"
    ), 200, {
        'X-Original-Size':   str(stats['original_size']),
        'X-Compressed-Size': str(stats['compressed_size']),
        'X-Ratio':           str(stats['ratio'])
    }
 
@app.route('/characteristics', methods=['POST'])
def characteristics():
    path   = os.path.join(UPLOAD_FOLDER, 'current.png')
    result = get_characteristics(path)
    return jsonify(result)

@app.route('/segmentation/evaluate', methods=['POST'])
def segmentation_evaluate():
    import cv2
    import numpy as np

    if 'segmented' not in request.files or 'ground_truth' not in request.files:
        return jsonify({'error': 'Both segmented and ground_truth images required'}), 400

    # Read 2 images
    seg_file = request.files['segmented']
    gt_file  = request.files['ground_truth']

    seg_arr = np.frombuffer(seg_file.read(), np.uint8)
    gt_arr  = np.frombuffer(gt_file.read(), np.uint8)

    seg = cv2.imdecode(seg_arr, cv2.IMREAD_GRAYSCALE)
    gt  = cv2.imdecode(gt_arr,  cv2.IMREAD_GRAYSCALE)

    if seg is None or gt is None:
        return jsonify({'error': 'Could not decode images'}), 400

    if seg.shape != gt.shape:
        gt = cv2.resize(gt, (seg.shape[1], seg.shape[0]))

    _, seg_bin = cv2.threshold(seg, 127, 1, cv2.THRESH_BINARY)
    _, gt_bin  = cv2.threshold(gt,  127, 1, cv2.THRESH_BINARY)

    seg_flat = seg_bin.flatten()
    gt_flat  = gt_bin.flatten()

    # Compute metrics
    TP = int(np.sum((seg_flat == 1) & (gt_flat == 1)))
    TN = int(np.sum((seg_flat == 0) & (gt_flat == 0)))
    FP = int(np.sum((seg_flat == 1) & (gt_flat == 0)))
    FN = int(np.sum((seg_flat == 0) & (gt_flat == 1)))

    precision   = TP / (TP + FP) if (TP + FP) > 0 else 0.0
    recall      = TP / (TP + FN) if (TP + FN) > 0 else 0.0
    sensitivity = recall  
    f1          = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    accuracy    = (TP + TN) / (TP + TN + FP + FN) if (TP + TN + FP + FN) > 0 else 0.0
    iou         = TP / (TP + FP + FN) if (TP + FP + FN) > 0 else 0.0
    dice        = f1  # Dice = F1 for binary

    return jsonify({
        'f1':          round(f1, 3),
        'recall':      round(recall, 3),
        'sensitivity': round(sensitivity, 3),
        'precision':   round(precision, 3),
        'accuracy':    round(accuracy, 3),
        'iou':         round(iou, 3),
        'dice':        round(dice, 3),
        'TP': TP, 'TN': TN, 'FP': FP, 'FN': FN
    })
 

@app.route('/')
def index():
    return send_from_directory('../Frontend/assets', 'homepage.html')

@app.route('/Frontend/<path:path>')
def frontend_files(path):
    return send_from_directory('../Frontend', path)



if __name__ == '__main__':
    print("Pixora starting on http://127.0.0.1:5000")
    app.run(debug=True, port=5000)

