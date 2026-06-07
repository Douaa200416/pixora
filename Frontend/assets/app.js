const state = {
  originalFile: null,
  currentBlob: null, 
  secondFile: null,
  currentOp: null,
  currentFilter: 'mean',
  currentPad: 'zeros',
  currentNoise: 'gaussian',
  currentComp: 'lossless',
  currentThresh: 'simple',
  filterStack: [],
  sessionStart: Date.now(),
  hasImage: false,
};
let originalContrast = null;

const API = '';

// TOAST
function showToast(msg, type='success') {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.className = `toast ${type} show`;
  setTimeout(() => t.className = 'toast', 3000);
}

//  COLLAPSIBLE SECTIONS
function toggleSection(id) {
  const cont = document.getElementById(`cont-${id}`);
  const chev = document.getElementById(`chev-${id}`);
  cont.classList.toggle('open');
  chev.classList.toggle('open');
}

//  OVERLAY PANELS
function openPanel(name) {
  closeAllPanels();
  document.getElementById(`panel-${name}`).classList.add('open');
  document.getElementById('backdrop').style.display = 'block';
}
function closePanel(name) {
  document.getElementById(`panel-${name}`).classList.remove('open');
  document.getElementById('backdrop').style.display = 'none';
}
function closeAllPanels() {
  ['characteristics','metrics'].forEach(p => {
    const el = document.getElementById(`panel-${p}`);
    if (el) el.classList.remove('open');
  });
  document.getElementById('backdrop').style.display = 'none';
}

// FILE UPLOAD
document.getElementById('fileInput').addEventListener('change', async (e) => {
  const file = e.target.files[0];
  if (!file) return;
  state.originalFile = file;
  state.currentBlob = file;
  originalContrast = null;
  showLoading('orig', true);
  updateInfoBar(file);

  const reader = new FileReader();
  reader.onload = (ev) => {
    const img = document.getElementById('originalImage');
    img.src = ev.target.result;
    img.style.display = 'block';
    document.getElementById('origPlaceholder').style.display = 'none';
    document.getElementById('origBox').classList.add('has-image');
  };
  reader.readAsDataURL(file);

  // Upload to backend
  const formData = new FormData();
  formData.append('image', file);
  try {
    const res = await fetch(`${API}/upload`, { method:'POST', body: formData });
    const data = await res.json();
    showToast(`Loaded`, 'success');
    state.hasImage = true;
    console.log('upload info:', JSON.stringify(data.info));

    if (data.info) {
  const minVal = data.info.min_intensity ?? 0;
  const maxVal = data.info.max_intensity ?? 255;

  document.getElementById('charLum').textContent      = data.info.luminance ?? '—';
  document.getElementById('charContrast').textContent = data.info.contrast  ?? '—';
  document.getElementById('charDynRange').textContent = `${minVal} – ${maxVal}`;
  document.getElementById('charMin').textContent      = `Min: ${minVal}`;
  document.getElementById('charMax').textContent      = `Max: ${maxVal}`;

  document.getElementById('minMarker').style.left  = (minVal / 255 * 100).toFixed(1) + '%';
  document.getElementById('maxMarker').style.left  = (maxVal / 255 * 100).toFixed(1) + '%';
  document.getElementById('maxMarker').style.right = 'unset';
}
  

setTimeout(() => {
  loadHistogram();
}, 300);
  } catch(err) {
    showToast('⚠ Backend not connected — UI preview only', 'error');
  }
  showLoading('orig', false);
  e.target.value = '';
});

document.getElementById('fileInput2').addEventListener('change', async (e) => {
  const file = e.target.files[0];
  if (!file) return;
  state.secondFile = file;
  document.getElementById('img2name').textContent = `✓ ${file.name}`;
  showToast(`Second image loaded: ${file.name}`);

  const formData = new FormData();
  formData.append('image', file);
  try {
    const res = await fetch(`${API}/upload_second`, { 
      method: 'POST', 
      body: formData 
    });
    const data = await res.json();
    showToast(`Second image saved to server`);
  } catch(err) {
    showToast('⚠ Failed to upload second image to server', 'error');
  }

  e.target.value = '';
});

document.getElementById('groundTruthInput').addEventListener('change', async (e) => {
  const file = e.target.files[0];
  if (!file) return;
  if (!state.currentBlob && !state.originalFile) {
    showToast(' Run segmentation first before loading ground truth', 'error');
    return;
  }
  showToast(`Evaluating against: ${file.name}...`);
  try {
    const formData = new FormData();
    // send the current segmented result
    formData.append('segmented', state.currentBlob || state.originalFile, 'segmented.png');
    formData.append('ground_truth', file, file.name);
    const res = await fetch(`${API}/segmentation/evaluate`, { method: 'POST', body: formData });
    const metrics = await res.json();
    if (metrics.error) { showToast(`⚠ ${metrics.error}`, 'error'); return; }
    updateEvalMetrics(metrics);
    showToast('✅ Evaluation complete');
  } catch(err) {
    showToast(` Evaluation failed: ${err.message}`, 'error');
  }
  e.target.value = '';
});

//  INFO BAR
function updateInfoBar(file) {
  const img = new Image();
  img.onload = () => {
    const w = img.width, h = img.height;
    const channels = 3;
    const theoKB = (w * h * channels * 8) / 8 / 1024;
    const fmt = file.name.split('.').pop().toUpperCase();
    document.getElementById('infoDims').textContent = `${w} × ${h} px`;
    document.getElementById('infoMode').textContent = `RGB (8-bit)`;
    document.getElementById('infoFormat').textContent = fmt;
    document.getElementById('infoSize').textContent = `${(file.size/1024).toFixed(1)} KB`;
    document.getElementById('infoTheo').textContent = theoKB > 1024 ? `${(theoKB/1024).toFixed(2)} MB` : `${theoKB.toFixed(1)} KB`;
    document.getElementById('infoRes').textContent = `${w}×${h}`;
    document.getElementById('origSizeComp').textContent = `${(file.size/1024).toFixed(1)} KB`;
    
    document.getElementById('charDims').textContent = `${w} × ${h}`;
    document.getElementById('charMem').textContent = theoKB > 1024 ? `${(theoKB/1024).toFixed(2)} MB` : `${theoKB.toFixed(1)} KB`;
    document.getElementById('charTheo').textContent = theoKB > 1024 ? `${(theoKB/1024).toFixed(2)} MB` : `${theoKB.toFixed(1)} KB`;
    document.getElementById('charReal').textContent = `${(file.size/1024).toFixed(1)} KB`;
    document.getElementById('charMode').textContent = 'RGB';
    document.getElementById('charFmt').textContent = fmt;
    document.getElementById('charMemType').textContent = 'Uncompressed RAW';
    document.getElementById('charTonal').textContent = '8-bit (256 levels)';
    document.getElementById('charSpatial').textContent = `72 DPI (screen)`;
    document.getElementById('charImgFmt').textContent = ['PNG','SVG','PDF'].includes(fmt) ? `Vector / ${fmt}` : `Bitmap / ${fmt}`;
    document.getElementById('charDynRange').textContent = '— (load completes on backend)';
   
    let std = '—';
    if (w >= 7680) std = '8K Ultra-HD';
    else if (w >= 3840) std = '4K Ultra-HD';
    else if (w >= 1920) std = '1080p Full HD';
    else if (w >= 1280) std = '720p HD';
    else std = 'SD';
    document.getElementById('charStandard').textContent = std;
    document.getElementById('charRes').textContent = std;
    // Resolution warning
    if (w < 400 || h < 400) {
      document.getElementById('resWarning').style.display = 'flex';
    }
  };
  img.src = URL.createObjectURL(file);
}

function updateCharacteristics(file, data) {
  
}

//  LOADING STATES
function showLoading(box, show, text='Processing...') {
  const el = document.getElementById(`${box}Loading`);
  if (show) el.classList.add('show');
  else el.classList.remove('show');
  if (box === 'proc') document.getElementById('procLoadingText').textContent = text;
}

async function sendOp(endpoint, params = {}) {
  if (!state.hasImage) { showToast('⚠ Load an image first', 'error'); return; }
  showLoading('proc', true);
  document.getElementById('processingLabel').textContent = `Applying: ${endpoint.split('/').pop()}...`;
  try {
    const formData = new FormData();
    formData.append('image', state.currentBlob || state.originalFile);
    Object.entries(params).forEach(([k,v]) => formData.append(k, v));
    const res = await fetch(`${API}/${endpoint}`, { method:'POST', body: formData });

    const contentType = res.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      const errData = await res.json();
      throw new Error(errData.error || `Server error ${res.status}`);
    }
    
    if (!res.ok) throw new Error(`Server error ${res.status}`);
    
    const blob = await res.blob();
    state.currentBlob = blob;
const url = URL.createObjectURL(blob);
showProcessed(url);
showToast(`✅ ${endpoint.split('/').pop()} applied`);

try {
  const updateForm = new FormData();
  updateForm.append('image', blob, 'result.png');
  await fetch(`${API}/update`, { method: 'POST', body: updateForm });

  const charRes  = await fetch(`${API}/characteristics`, { method: 'POST' });
  const charData = await charRes.json();
  if (charData.min_intensity !== undefined) {
    const minVal = charData.min_intensity;
    const maxVal = charData.max_intensity;
    document.getElementById('charLum').textContent      = charData.luminance  ?? '—';
    document.getElementById('charContrast').textContent = charData.contrast   ?? '—';
    document.getElementById('charDynRange').textContent = `${minVal} – ${maxVal}`;
    document.getElementById('charMin').textContent      = `Min: ${minVal}`;
    document.getElementById('charMax').textContent      = `Max: ${maxVal}`;
    document.getElementById('minMarker').style.left     = (minVal / 255 * 100).toFixed(1) + '%';
    document.getElementById('maxMarker').style.left     = (maxVal / 255 * 100).toFixed(1) + '%';
    document.getElementById('maxMarker').style.right    = 'unset';
  }

  const hRes = await fetch(`${API}/histogram/show`, { method: 'POST' });
  const hData = await hRes.json();
  if (hData.global_contrast !== undefined) {
    document.getElementById('contrastAfter').textContent = hData.global_contrast;
    drawHistogram(hData.histogram);
    displayHistogramStats(hData);
  }
} catch(e) {}

} catch(err) {
  showToast(`⚠ ${err.message}`, 'error');
  if (state.originalFile) {
    showProcessed(URL.createObjectURL(state.originalFile));
  }
}
  fetch(`${API}/histogram/show`, { method: 'POST' })
  .then(r => r.json())
  .then(d => {
    if (d.global_contrast !== undefined) {
      document.getElementById('contrastAfter').textContent = d.global_contrast;
    }
  })
  .catch(() => {});
  showLoading('proc', false);
  document.getElementById('processingLabel').textContent = `✓ ${endpoint.split('/').pop()}`;
}

function showProcessed(url) {
  const img = document.getElementById('processedImage');
  img.src = url;
  img.style.display = 'block';
  document.getElementById('procPlaceholder').style.display = 'none';
  document.getElementById('procBox').classList.add('has-image');
  document.getElementById('procBox').style.borderColor = '#22d3a5';
  setTimeout(() => { document.getElementById('procBox').style.borderColor = '#F5EFEB'; }, 1000);
}

//  IMAGE CONVERSIONS
function convertType(type, btn) {
  document.querySelectorAll('#cont-types .pill-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  const thresh = document.getElementById('binaryThreshSlider').value;
  sendOp(`convert/${type}`, type === 'binary' ? { threshold: thresh } : {});
}

//DIGITIZATION
function updateSampling(val) {
  document.getElementById('samplingVal').textContent = `${val}%`;
}
function updateQuant(val) {
  const levels = Math.pow(2, val);
  document.getElementById('quantVal').textContent = `${val} bits (${levels} levels)`;
}
function applyDigitization() {
  sendOp('digitize', {
    sampling: document.getElementById('samplingSlider').value,
    quantization: document.getElementById('quantSlider').value
  });
}

//BASIC OPERATIONS
const opConfigs = {
  crop:     { title:'Crop Parameters', html:'<div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;"><input class="styled-input" placeholder="x" id="op_x" value="0"/><input class="styled-input" placeholder="y" id="op_y" value="0"/><input class="styled-input" placeholder="width" id="op_w" value="100"/><input class="styled-input" placeholder="height" id="op_h" value="100"/></div>' },
  rotate:   { title:'Rotate Parameters', html:'<div style="display:flex;gap:8px;align-items:center;"><input class="styled-input" placeholder="Angle (°)" id="op_angle" value="90" type="number"/><select class="styled-input" id="op_dir"><option value="cw">Clockwise</option><option value="ccw">Counter-CW</option></select></div>' },
  translate:{ title:'Translate Parameters', html:'<div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;"><input class="styled-input" placeholder="tx (pixels)" id="op_tx" value="10" type="number"/><input class="styled-input" placeholder="ty (pixels)" id="op_ty" value="10" type="number"/></div>' },
  scale:    { title:'Scale Parameters', html:'<div style="display:flex;gap:8px;"><input class="styled-input" placeholder="Width" id="op_sw" type="number" value="800"/><input class="styled-input" placeholder="Height" id="op_sh" type="number" value="600"/></div>' },
  flip:     { title:'Flip / Reflection', html:'<select class="styled-input" id="op_flip"><option value="horizontal">Horizontal</option><option value="vertical">Vertical</option><option value="both">Both</option></select>' },
  symmetry: { title:'Centric Symmetry', html:'<div style="font-size:12px;color:#7d8590;">Rotates 180° around center point.</div>' },
};
let currentOpType = null;
function showOpParams(type) {
  currentOpType = type;
  const cfg = opConfigs[type];
  document.getElementById('opParamsTitle').textContent = cfg.title;
  document.getElementById('opParamsContent').innerHTML = cfg.html;
  document.getElementById('opParamsArea').style.display = 'block';
}
function applyBasicOp() {
  if (!currentOpType) return;
  const params = { op: currentOpType };
  if (currentOpType === 'rotate') { params.angle = document.getElementById('op_angle')?.value; params.dir = document.getElementById('op_dir')?.value; }
  if (currentOpType === 'translate') { params.tx = document.getElementById('op_tx')?.value; params.ty = document.getElementById('op_ty')?.value; }
  if (currentOpType === 'scale') { params.width = document.getElementById('op_sw')?.value; params.height = document.getElementById('op_sh')?.value; }
  if (currentOpType === 'flip') { params.axis = document.getElementById('op_flip')?.value; }
  if (currentOpType === 'crop') { params.x = document.getElementById('op_x')?.value; params.y = document.getElementById('op_y')?.value; params.w = document.getElementById('op_w')?.value; params.h = document.getElementById('op_h')?.value; }
  sendOp('operations/basic', params);
}

// ARITHMETIC & LOGICAL
function applyArith(op) {
  if (!state.hasImage) { showToast('⚠ Load an image first', 'error'); return; }
  if (['add_img','sub_img','and','or','xor','nor'].includes(op) && !state.secondFile) {
    showToast('⚠ Load a second image first', 'error'); return;
  }
  const params = { op };
  if (op === 'add_const' || op === 'sub_const') params.value = document.getElementById('constVal').value;
  sendOp('operations/arithmetic', params);
}
function showConstInput() {
  const el = document.getElementById('constInputArea');
  el.style.display = el.style.display === 'none' ? 'block' : 'none';
}

//  NOISE
const noiseLabels = { gaussian:'Variance (σ²)', impulse:'Noise % (Salt & Pepper)', speckle:'Intensity', poisson:'Intensity', periodic:'Frequency' };
function selectNoise(type, btn) {
  state.currentNoise = type;
  document.querySelectorAll('#cont-noise .pill-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  document.getElementById('noiseParamLabel').textContent = noiseLabels[type];
}
function updateNoiseParam(val) {
  const v = state.currentNoise === 'gaussian' ? (val/1000).toFixed(3) : `${val}%`;
  document.getElementById('noiseParamVal').textContent = v;
}
function sendNoiseOp() {
  sendOp('noise/add', {
    type: state.currentNoise,
    param: document.getElementById('noiseParamSlider').value
  });
}

// FILTERING
function selectFilterCat(cat, btn) {
  document.querySelectorAll('#cont-filter .sub-tab').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  ['lpf','hpf','nlf'].forEach(c => {
    document.getElementById(`fcat-${c}`).style.display = c === cat ? 'block' : 'none';
  });
}
function selectFilter(f, btn) {
  state.currentFilter = f;
  document.querySelectorAll(`#fcat-lpf .pill-btn, #fcat-hpf .pill-btn, #fcat-nlf .pill-btn`).forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  document.getElementById('paddingArea').style.display = f === 'mean' ? 'block' : 'none';
}
function selectPad(pad, btn) {
  state.currentPad = pad;
  document.querySelectorAll('#cont-filter #paddingArea .pill-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
}
async function applyFilter() {
  const params = {
    filter: state.currentFilter,
    kernel: document.getElementById('kernelSize').value,
    shape: document.getElementById('maskShape').value,
    padding: state.currentPad
  };
  await sendOp('filter/apply', params);
  try {
    const mRes = await fetch(`${API}/filter/metrics`, { method: 'POST' });
    // fix Infinity invalid JSON by replacing before parsing
    const raw  = await mRes.text();
    const safe = raw.replace(/:\s*Infinity/g, ': 9999').replace(/:\s*-Infinity/g, ': -9999').replace(/:\s*NaN/g, ': 0');
    const mData = JSON.parse(safe);

    const mse  = parseFloat(mData.mse  ?? 0).toFixed(3);
    const psnr = parseFloat(mData.psnr ?? 0).toFixed(2);
    const mseR = parseFloat(mData.mse_r ?? mData.mse ?? 0).toFixed(3);
    const mseG = parseFloat(mData.mse_g ?? mData.mse ?? 0).toFixed(3);
    const mseB = parseFloat(mData.mse_b ?? mData.mse ?? 0).toFixed(3);

    const psnrLabel = parseFloat(psnr) > 40 ? '✅ Excellent' : parseFloat(psnr) > 30 ? '🆗 Acceptable' : '❌ Poor';
    const mseLabel  = parseFloat(mse) < 10 ? '✅ Low error' : '⚠ High error';
    const psnrDisplay = parseFloat(psnr) >= 9999 ? '∞ dB (identical)' : `${psnr} dB`;

    document.getElementById('filterMSE').textContent        = mse;
    document.getElementById('filterPSNR').textContent       = psnrDisplay;
    document.getElementById('filterMSE_rgb').textContent    = `R:${mseR} G:${mseG} B:${mseB}`;
    document.getElementById('filterPSNR_rgb').textContent   = `RGB avg: ${psnrDisplay}`;
    document.getElementById('mseValue').textContent         = mse;
    document.getElementById('psnrValue').textContent        = psnrDisplay;
    document.getElementById('mseLabel').textContent         = mseLabel;
    document.getElementById('psnrLabel').textContent        = psnrLabel;
    document.getElementById('metricsMSE').textContent       = mse;
    document.getElementById('metricsMSEstatus').textContent = mseLabel;
    document.getElementById('metricsPSNR').textContent      = psnrDisplay;
    document.getElementById('metricsPSNRstatus').textContent= psnrLabel;
    document.getElementById('mseR').textContent             = mseR;
    document.getElementById('mseG').textContent             = mseG;
    document.getElementById('mseB').textContent             = mseB;

  } catch (e) {
    console.error('Metrics fetch failed:', e);
    showToast('⚠ Could not load filter metrics', 'error');
    ['filterMSE','mseValue','metricsMSE','filterPSNR','psnrValue','metricsPSNR','mseR','mseG','mseB'].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.textContent = '—';
    });
  }
}
function addFilterStack() {
  const name = state.currentFilter;
  state.filterStack.push(name);
  const area = document.getElementById('filterStackArea');
  const tag = document.createElement('span');
  tag.className = 'tag';
  tag.innerHTML = `${name} <span class="remove" onclick="removeFilter(this,'${name}')">×</span>`;
  area.appendChild(tag);
}
function removeFilter(el, name) {
  el.parentElement.remove();
  state.filterStack = state.filterStack.filter(f => f !== name);
}

//  SEGMENTATION
function selectThresh(type, btn) {
  state.currentThresh = type;
  document.querySelectorAll('#cont-segmentation .sub-tab').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  const p = document.getElementById('threshParams');

  if (type === 'double') {
    p.innerHTML = `
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
        <span style="font-size:10px;color:#7d8590;min-width:20px;">T1:</span>
        <input type="range" min="0" max="255" value="80" id="thresh1" oninput="document.getElementById('t1v').textContent=this.value"/>
        <span style="font-size:11px;color:#22d3a5;font-weight:700;min-width:24px;" id="t1v">80</span>
      </div>
      <div style="display:flex;align-items:center;gap:8px;">
        <span style="font-size:10px;color:#7d8590;min-width:20px;">T2:</span>
        <input type="range" min="0" max="255" value="180" id="thresh2" oninput="document.getElementById('t2v').textContent=this.value"/>
        <span style="font-size:11px;color:#22d3a5;font-weight:700;min-width:24px;" id="t2v">180</span>
      </div>
      <div style="font-size:10px;color:#7d8590;margin-top:4px;">Creates 3 regions: 0–T1 / T1–T2 / T2–255</div>`;

  } else if (type === 'multi') {
    p.innerHTML = `
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
        <span style="font-size:10px;color:#7d8590;min-width:20px;">T1:</span>
        <input type="range" min="0" max="255" value="64"  id="thresh1" oninput="document.getElementById('t1v').textContent=this.value"/>
        <span style="font-size:11px;color:#22d3a5;font-weight:700;min-width:24px;" id="t1v">64</span>
      </div>
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
        <span style="font-size:10px;color:#7d8590;min-width:20px;">T2:</span>
        <input type="range" min="0" max="255" value="128" id="thresh2" oninput="document.getElementById('t2v').textContent=this.value"/>
        <span style="font-size:11px;color:#22d3a5;font-weight:700;min-width:24px;" id="t2v">128</span>
      </div>
      <div style="display:flex;align-items:center;gap:8px;">
        <span style="font-size:10px;color:#7d8590;min-width:20px;">T3:</span>
        <input type="range" min="0" max="255" value="192" id="thresh3" oninput="document.getElementById('t3v').textContent=this.value"/>
        <span style="font-size:11px;color:#22d3a5;font-weight:700;min-width:24px;" id="t3v">192</span>
      </div>
      <div style="font-size:10px;color:#7d8590;margin-top:4px;">Creates 4 regions: 0–T1 / T1–T2 / T2–T3 / T3–255</div>`;

  } else if (type === 'otsu' || type === 'adaptive' || type === 'global') {
    p.innerHTML = `<div style="font-size:11px;color:#7d8590;">Automatic — no threshold needed.</div>`;

  } else {
    // simple, local
    p.innerHTML = `
      <div style="display:flex;align-items:center;gap:8px;">
        <span style="font-size:10px;color:#7d8590;min-width:20px;">T:</span>
        <input type="range" min="0" max="255" value="127" id="thresh1" oninput="document.getElementById('thresh1val').textContent=this.value"/>
        <span style="font-size:11px;color:#22d3a5;font-weight:700;min-width:24px;" id="thresh1val">127</span>
      </div>`;
  }
}
function applySegmentation(method) {
  const params = {
    method,
    thresh_type: state.currentThresh,
    k:           document.getElementById('kValue').value,
    morphShape:  document.getElementById('morphShape').value,
    morphSize:   document.getElementById('morphSize').value,
    thresh1:     document.getElementById('thresh1')?.value ?? 127,
    thresh2:     document.getElementById('thresh2')?.value ?? 200,
    thresh3:     document.getElementById('thresh3')?.value ?? 192,
  };
  sendOp(`segmentation/${method}`, params);
}
//EVALUATION METRICS

  function updateEvalMetrics(m) {
  const metrics = [
    { key: 'f1',          elId: 'evalF1',     barId: 'evalF1Bar',     panelId: 'mF1',     panelBar: 'mF1bar'     },
    { key: 'recall',      elId: 'evalRecall', barId: 'evalRecallBar', panelId: 'mRecall', panelBar: 'mRecallbar' },
    { key: 'sensitivity', elId: 'evalSens',   barId: 'evalSensBar',   panelId: 'mSens',   panelBar: 'mSensbar'   },
    { key: 'precision',   elId: 'evalPrec',   barId: 'evalPrecBar',   panelId: 'mPrec',   panelBar: 'mPrecbar'   },
    { key: 'accuracy',    elId: 'evalAcc',    barId: 'evalAccBar',    panelId: 'mAcc',    panelBar: 'mAccbar'    },
  ];
  metrics.forEach(({ key, elId, barId, panelId, panelBar }) => {
    const v = m[key];
    if (v === undefined) return;
    const pct = (v * 100).toFixed(1);
    const el   = document.getElementById(elId);
    const bar  = document.getElementById(barId);
    const pel  = document.getElementById(panelId);
    const pbar = document.getElementById(panelBar);
    if (el)   el.textContent   = v.toFixed(3);
    if (bar)  bar.style.width  = pct + '%';
    if (pel)  pel.textContent  = v.toFixed(3);
    if (pbar) pbar.style.width = pct + '%';
  });
  document.getElementById('evalMetrics').style.display = 'block';
}

// HISTOGRAM 

let logScale = false;

// Toggle log scale
function toggleLogScale() {
  logScale = !logScale;
  document.getElementById('logScaleBtn')?.classList.toggle('active');
  loadHistogram();
}

function exportHistCSV() {
  if (!state.hasImage) {
    showToast('⚠ Load an image first', 'error');
    return;
  }

  fetch(`${API}/histogram/show`, { method: 'POST', mode: 'cors' })
    .then(res => res.json())
    .then(data => {
      if (data.error) throw new Error(data.error);
      let csv = 'Bin,Count\n';
      data.histogram.forEach((count, index) => {
        csv += `${index},${count}\n`;
      });
      csv += `\nMean,${data.mean}\n`;
      csv += `Std,${data.std}\n`;
      csv += `Min,${data.min}\n`;
      csv += `Max,${data.max}\n`;
      csv += `Global Contrast,${data.global_contrast ?? 'N/A'}\n`;
      csv += `Underexposed,${data.underexposed}\n`;
      csv += `Overexposed,${data.overexposed}\n`;
      const blob = new Blob([csv], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `pixora_histogram_${Date.now()}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      showToast('📊 Histogram CSV exported');
    })
    .catch(err => {
      console.error('CSV export failed:', err);
      showToast(`⚠ Export failed: ${err.message}`, 'error');
    });
}

async function loadHistogram() {
  if (!state.hasImage) {
    showToast('⚠ Load an image first', 'error');
    return;
  }

  try {
    const res = await fetch(`${API}/histogram/show`, {
      method: 'POST',
      mode: 'cors'
    });

    if (!res.ok) {
      throw new Error(`Server returned ${res.status}`);
    }

    const data = await res.json();

    if (data.error) {
      throw new Error(data.error);
    }

    drawHistogram(data.histogram);
    displayHistogramStats(data);
    xposure(data);
    showToast('📊 Histogram loaded');

  } catch (err) {
    console.error("Histogram fetch failed:", err);
    showToast(`⚠ Histogram failed: ${err.message}`, 'error');

    const container = document.getElementById("histogramDisplay");
    if (container) {
      container.innerHTML = `
        <div style="color:#ef4444; font-size:14px; width:100%; text-align:center; align-self:center;">
          Failed to load histogram<br>
          <span style="font-size:11px; color:#7d8590;">${err.message}</span>
        </div>`;
    }
  }
}

function drawHistogram(hist) {
  const container = document.getElementById("histogramDisplay");
  if (!container) return;

  container.innerHTML = "";

  if (!hist || hist.length === 0) {
    container.innerHTML = `
      <div style="color:#F5EFEB; font-size:14px; width:100%; text-align:center; align-self:center;">
        No histogram data
      </div>`;
    return;
  }

  let values = [...hist];

  if (logScale) {
    values = values.map(v => Math.log(1 + v));
  }

  const max = Math.max(...values);

  if (max === 0) return;

  values.forEach(v => {
    const bar = document.createElement("div");
    bar.style.flex = "1";
    bar.style.height = (v / max * 100) + "%";
    bar.style.background = "#C8D9E6";
    bar.style.borderRadius = "1px";
    bar.style.minWidth = "1px";
    container.appendChild(bar);
  });
}

function displayHistogramStats(data) {
  const el = document.getElementById("histStats");
  if (!el) return;

  el.innerHTML = `
    Mean: ${data.mean} |
    Std: ${data.std} |
    Min: ${data.min} |
    Max: ${data.max} |
    Contrast: ${data.global_contrast ?? "N/A"}
  `;
   document.getElementById('globalContrast').textContent = data.global_contrast ?? '—';
   if (originalContrast === null) {
    originalContrast = data.global_contrast ?? '—';
    document.getElementById('contrastBefore').textContent = originalContrast;
  }
  document.getElementById('contrastAfter').textContent = data.global_contrast ?? '—';
  const lum      = parseFloat(data.mean ?? 0);
  const contrast = parseFloat(data.global_contrast ?? 0);

  document.getElementById('mLum').textContent     = lum.toFixed(1);
  document.getElementById('mLumBar').style.width  = (lum / 255 * 100).toFixed(1) + '%';
  document.getElementById('mLumLabel').textContent =
    lum < 60 ? '🔵 Dark image' : lum > 200 ? '🔴 Bright image' : ' Normal brightness';

  document.getElementById('mContrast').textContent    = contrast.toFixed(1);
  document.getElementById('mContrastBar').style.width = Math.min(contrast / 5000 * 100, 100).toFixed(1) + '%';
  document.getElementById('mContrastLabel').textContent =
    contrast < 500 ? 'Low contrast — flat image' : contrast > 4000 ? ' Very high contrast' : 'Good contrast range';

  document.getElementById('mMinVal').textContent = data.min ?? '—';
  document.getElementById('mMaxVal').textContent = data.max ?? '—';

  const warn = document.getElementById('mExposureWarn');
  if (data.underexposed) {
    warn.style.display = 'block';
    warn.style.borderColor = '#567C8D';
    document.getElementById('mExposureText').textContent = 'Underexposed — shadows clipped, detail lost';
  } else if (data.overexposed) {
    warn.style.display = 'block';
    warn.style.borderColor = '#ef4444';
    document.getElementById('mExposureText').textContent = 'Overexposed — highlights clipped';
  } else {
    warn.style.display = 'none';
  }
}

function xposure(data) {
  const under = document.getElementById("underExp");
  const over = document.getElementById("overExp");

  if (under) {
    under.style.display = data.underexposed ? "inline-block" : "none";
  }

  if (over) {
    over.style.display = data.overexposed ? "inline-block" : "none";
  }
}


function toggleHistView(which) {
  const before = document.getElementById('histToggle-before');
  const after = document.getElementById('histToggle-after');

  if (before) before.classList.remove('active');
  if (after) after.classList.remove('active');

  const selected = document.getElementById(`histToggle-${which}`);
  if (selected) selected.classList.add('active');
}

function toggleLocalContrast() {
  const el = document.getElementById('localContrastArea');
  const toggle = document.getElementById('localContrastToggle');

  if (!el || !toggle) return;

  el.style.display = toggle.checked ? 'block' : 'none';
}

//COMPRESSION
function selectComp(type, btn) {
  state.currentComp = type;
  document.querySelectorAll('#cont-compression .pill-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  document.getElementById('qualityArea').style.display = type === 'lossy' ? 'block' : 'none';
}
async function compressAndSave() {
  if (!state.hasImage) { showToast('⚠ Load an image first', 'error'); return; }
  const formData = new FormData();
  formData.append('image', state.currentBlob || state.originalFile);
  formData.append('type', state.currentComp);
  formData.append('quality', document.getElementById('compQuality').value);
  try {
    const res = await fetch(`${API}/compress`, { method: 'POST', body: formData });
    if (!res.ok) { showToast('⚠ Compression failed', 'error'); return; }

    const originalSize   = res.headers.get('X-Original-Size');
    const compressedSize = res.headers.get('X-Compressed-Size');
    const ratio          = res.headers.get('X-Ratio');

    if (ratio)          document.getElementById('compRatio').textContent    = `${ratio}:1`;
    if (compressedSize) document.getElementById('compSizeComp').textContent = `${compressedSize} KB`;
    if (originalSize)   document.getElementById('origSizeComp').textContent = `${originalSize} KB`;
    const blob     = await res.blob();
    const url      = URL.createObjectURL(blob);
    const a        = document.createElement('a');
    a.href         = url;
    a.download     = state.currentComp === 'lossless' ? 'compressed.png' : 'compressed.jpg';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    showToast(`✅ Downloaded — ratio ${ratio}:1`);
  } catch(err) {
    showToast(`⚠ Compression failed: ${err.message}`, 'error');
  }
}

// MISC ACTIONS
function swapImages() {
  const o = document.getElementById('originalImage');
  const p = document.getElementById('processedImage');
  if (p.style.display !== 'none' && p.src) {
    const tmp = o.src;
    o.src = p.src;
    p.src = tmp;
    showToast('🔄 Images swapped');
  }
}
function saveImage() {
  const p = document.getElementById('processedImage');
  if (p.style.display === 'none') { showToast('⚠ No processed image to save', 'error'); return; }
  const a = document.createElement('a');
  a.href = p.src;
  a.download = 'pixora_result.png';
  a.click();
  showToast('💾 Image saved');
}
function resetImage() {
  state.currentBlob = state.originalFile;
  document.getElementById('processedImage').style.display = 'none';
  document.getElementById('procPlaceholder').style.display = 'block';
  document.getElementById('procBox').classList.remove('has-image');
  document.getElementById('processingLabel').textContent = '—';
  showToast('Reset to original');
}

function scrollToSection(id) {
  const el = document.getElementById(`sec-${id}`);
  if (el) {
    const cont = document.getElementById(`cont-${id}`);
    if (!cont.classList.contains('open')) toggleSection(id);
    el.scrollIntoView({ behavior:'smooth', block:'start' });
  }
  document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
  event.target.classList.add('active');
}

// CURSOR 
(function() {
  const _canvas = document.createElement('canvas');
  const _ctx = _canvas.getContext('2d');
  let _imgLoaded = false;

  function reloadCanvas() {
    const img = document.getElementById('originalImage');
    if (!img || img.style.display === 'none' || !img.src) { _imgLoaded = false; return; }
    _canvas.width = img.naturalWidth || img.width;
    _canvas.height = img.naturalHeight || img.height;
    _ctx.drawImage(img, 0, 0);
    _imgLoaded = true;
  }

  const _imgEl = document.getElementById('originalImage');
  if (_imgEl) _imgEl.addEventListener('load', reloadCanvas);

  document.addEventListener('mousemove', (e) => {
    const origBox = document.getElementById('origBox');
    const rect = origBox.getBoundingClientRect();
    if (e.clientX >= rect.left && e.clientX <= rect.right && e.clientY >= rect.top && e.clientY <= rect.bottom) {
      const boxX = e.clientX - rect.left;
      const boxY = e.clientY - rect.top;
      const x = Math.round(boxX);
      const y = Math.round(boxY);
      let rgb = 'R: — G: — B: —';
      if (_imgLoaded) {
        try {
          const imgEl = document.getElementById('originalImage');
          const scaleX = _canvas.width / rect.width;
          const scaleY = _canvas.height / rect.height;
          const px = Math.min(Math.round(boxX * scaleX), _canvas.width - 1);
          const py = Math.min(Math.round(boxY * scaleY), _canvas.height - 1);
          const [r, g, b] = _ctx.getImageData(px, py, 1, 1).data;
          rgb = `R: ${r} G: ${g} B: ${b}`;
        } catch(err) {
          rgb = 'R: — G: — B: —';
        }
      }
      document.getElementById('cursorCoords').textContent = `X: ${x}  Y: ${y}  |  ${rgb}`;
    }
  });
})();

function openHelp() {
  document.getElementById('helpModal').style.display = 'flex';
}
function closeHelp() {
  document.getElementById('helpModal').style.display = 'none';
}

// show on first visit
if (!localStorage.getItem('pixora_help_seen')) {
  setTimeout(() => {
    document.getElementById('helpModal').style.display = 'flex';
  }, 500);
}

async function computeLocalContrast() {
  if (!state.hasImage) { showToast('⚠ Load an image first', 'error'); return; }

  const x = document.getElementById('lcX').value;
  const y = document.getElementById('lcY').value;
  const w = document.getElementById('lcW').value;
  const h = document.getElementById('lcH').value;

  const formData = new FormData();
  formData.append('image', state.currentBlob || state.originalFile);
  formData.append('x', x);
  formData.append('y', y);
  formData.append('w', w);
  formData.append('h', h);

  try {
    const res = await fetch(`${API}/histogram/local_contrast`, {
      method: 'POST',
      body: formData
    });
    const data = await res.json();
    if (data.error) throw new Error(data.error);

    // Show whatever your backend returns — adjust key names as needed
    const resultEl = document.getElementById('localContrastResult');
    resultEl.textContent =
      `Local Contrast: ${data.local_contrast ?? data.contrast ?? JSON.stringify(data)}`;
  } catch (err) {
    showToast(`⚠ Local contrast failed: ${err.message}`, 'error');
  }
}

// MOBILE MENU
function toggleMobileMenu() {
  showToast('Use the navbar tabs to navigate');
}
