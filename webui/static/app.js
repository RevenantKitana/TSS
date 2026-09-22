/**
 * ZeroTTS Studio Web UI — Pure Vanilla JavaScript
 * Zero external dependencies, pure HTML5/ES6+
 */

(function () {
  'use strict';

  // ── DOM Elements ──────────────────────────────────────────────────────────
  const themeToggleBtn = document.getElementById('themeToggleBtn');
  const systemStatus = document.getElementById('systemStatus');
  const systemStatusText = document.getElementById('systemStatusText');

  const voiceSelect = document.getElementById('voiceSelect');
  const refreshVoicesBtn = document.getElementById('refreshVoicesBtn');
  const voiceMeta = document.getElementById('voiceMeta');
  const voicePreviewAudio = document.getElementById('voicePreviewAudio');

  const historyFolderSelect = document.getElementById('historyFolderSelect');
  const historyFileSelect = document.getElementById('historyFileSelect');
  const refreshHistoryBtn = document.getElementById('refreshHistoryBtn');
  const concatBtn = document.getElementById('concatBtn');
  const openHistoryFolderBtn = document.getElementById('openHistoryFolderBtn');
  const openOutputFolderBtn = document.getElementById('openOutputFolderBtn');

  const scriptFileInput = document.getElementById('scriptFileInput');
  const uploadScriptBtn = document.getElementById('uploadScriptBtn');
  const insertProjectBtn = document.getElementById('insertProjectBtn');
  const projectQueueSummary = document.getElementById('projectQueueSummary');
  const queueSummaryText = document.getElementById('queueSummaryText');
  const queueProjectsList = document.getElementById('queueProjectsList');

  const mainTextInput = document.getElementById('mainTextInput');
  const charCount = document.getElementById('charCount');
  const insertPauseBtn = document.getElementById('insertPauseBtn');
  const insertTagBtn = document.getElementById('insertTagBtn');
  const clearTextBtn = document.getElementById('clearTextBtn');
  const sampleTextBtn = document.getElementById('sampleTextBtn');

  const customNameInput = document.getElementById('customNameInput');
  const overwriteModeSelect = document.getElementById('overwriteModeSelect');
  const workersSelect = document.getElementById('workersSelect');
  const autoConcatCheck = document.getElementById('autoConcatCheck');
  const mergedFormatSelect = document.getElementById('mergedFormatSelect');

  const generateBtn = document.getElementById('generateBtn');
  const stopBtn = document.getElementById('stopBtn');

  const progressMessage = document.getElementById('progressMessage');
  const progressPercent = document.getElementById('progressPercent');
  const progressBarFill = document.getElementById('progressBarFill');

  const mainAudioPlayer = document.getElementById('mainAudioPlayer');
  const waveformCanvas = document.getElementById('waveformCanvas');
  const waveformScrollContainer = document.getElementById('waveformScrollContainer');
  const waveformZoomLevel = document.getElementById('waveformZoomLevel');
  const zoomInWaveformBtn = document.getElementById('zoomInWaveformBtn');
  const zoomOutWaveformBtn = document.getElementById('zoomOutWaveformBtn');
  const zoomResetWaveformBtn = document.getElementById('zoomResetWaveformBtn');
  const currentAudioLabel = document.getElementById('currentAudioLabel');
  const segmentsDetailsBox = document.getElementById('segmentsDetailsBox');
  const progressStatusBox = document.getElementById('progressStatusBox');
  const progressSpinner = document.getElementById('progressSpinner');
  const generateSpinner = document.getElementById('generateSpinner');
  const generateIcon = document.getElementById('generateIcon');
  const generateLabel = document.getElementById('generateLabel');
  const generateShortcut = document.getElementById('generateShortcut');

  const modeSelect = document.getElementById('modeSelect');
  const cfgSlider = document.getElementById('cfgSlider');
  const cfgVal = document.getElementById('cfgVal');
  const chunkSecSlider = document.getElementById('chunkSecSlider');
  const chunkSecVal = document.getElementById('chunkSecVal');
  const tempSlider = document.getElementById('tempSlider');
  const tempVal = document.getElementById('tempVal');
  const topkSlider = document.getElementById('topkSlider');
  const topkVal = document.getElementById('topkVal');
  const toppSlider = document.getElementById('toppSlider');
  const toppVal = document.getElementById('toppVal');
  const repSlider = document.getElementById('repSlider');
  const repVal = document.getElementById('repVal');
  const eoaSlider = document.getElementById('eoaSlider');
  const eoaVal = document.getElementById('eoaVal');

  const advancedOptionsCard = document.getElementById('advancedOptionsCard');
  const advancedLockBadge = document.getElementById('advancedLockBadge');
  const advancedLockNotice = document.getElementById('advancedLockNotice');
  const modeExplanationText = document.getElementById('modeExplanationText');

  const presetRadios = document.querySelectorAll('input[name="preset"]');

  // ── Global State ──────────────────────────────────────────────────────────
  let voicesList = [];
  let abortController = null;
  let lastActiveFolder = '';

  const PRESETS = {
    default: { cfg: 1.0, temp: 0.8, topk: 25, topp: 0.95, rep: 1.2 },
    expressive: { cfg: 1.5, temp: 0.85, topk: 30, topp: 0.95, rep: 1.25 },
    speed: { cfg: 1.0, temp: 0.7, topk: 20, topp: 0.9, rep: 1.15 },
  };

  const SAMPLE_MULTI_PROJECT_TEXT = `$[An_toàn_nghiệp_vụ] // Thư mục 1: An toàn lao động
[Text 1] Chào mừng các bạn đến với khóa đào tạo An toàn lao động. [pause: 1.5s]
[Text 2] Hãy luôn tuân thủ việc trang bị đồ bảo hộ cá nhân trước khi vào công trường.

$[Kỹ_năng_giao_tiếp] // Thư mục 2: Kỹ năng ứng xử
[Text 1] Giao tiếp hiệu quả là chìa khóa then chốt dẫn tới thành công. [pause: 1s]
[Text 2] Chúc các bạn có một ngày làm việc tràn đầy năng lượng và hiệu quả!`;

  // ── Theme Management ──────────────────────────────────────────────────────
  function initTheme() {
    const savedTheme = localStorage.getItem('zerotts_theme') || 'dark-theme';
    document.body.className = savedTheme;
    updateThemeIcon(savedTheme);
  }

  function updateThemeIcon(theme) {
    if (themeToggleBtn) {
      themeToggleBtn.querySelector('.theme-icon').textContent = theme === 'dark-theme' ? '🌙' : '☀️';
    }
  }

  if (themeToggleBtn) {
    themeToggleBtn.addEventListener('click', () => {
      const isDark = document.body.classList.contains('dark-theme');
      const newTheme = isDark ? 'light-theme' : 'dark-theme';
      document.body.className = newTheme;
      localStorage.setItem('zerotts_theme', newTheme);
      updateThemeIcon(newTheme);
    });
  }

  // ── Textarea & Project Queue Management ───────────────────────────────────
  function updateProjectQueuePreview() {
    const text = mainTextInput.value;
    const projectMatches = text.match(/\$\[(.*?)\]/g) || [];
    
    if (!projectQueueSummary || !queueProjectsList) return;

    if (projectMatches.length > 1 || (projectMatches.length === 1 && text.trim().startsWith('$['))) {
      projectQueueSummary.style.display = 'flex';
      queueSummaryText.textContent = `Phát hiện ${projectMatches.length} Dự án trong kịch bản (Chuỗi Batch Queue)`;
      queueProjectsList.innerHTML = '';

      projectMatches.forEach((pm, idx) => {
        const cleanName = pm.replace(/\$\[|\]/g, '').replace(/(?:\/\/|#).*$/, '').trim();
        const pill = document.createElement('span');
        pill.className = 'queue-project-pill';
        pill.innerHTML = `<span>📁 ${idx + 1}. ${cleanName}</span>`;
        queueProjectsList.appendChild(pill);
      });
    } else {
      projectQueueSummary.style.display = 'none';
      queueProjectsList.innerHTML = '';
    }
  }

  function updateCharCount() {
    const len = mainTextInput.value.length;
    charCount.textContent = `${len} / 5000`;
    charCount.style.color = len > 5000 ? '#ef4444' : '';
    localStorage.setItem('zerotts_saved_text', mainTextInput.value);
    updateProjectQueuePreview();
  }

  mainTextInput.addEventListener('input', updateCharCount);

  if (workersSelect) {
    const savedWorkers = localStorage.getItem('zerotts_saved_workers');
    if (savedWorkers) {
      workersSelect.value = savedWorkers;
    }
    workersSelect.addEventListener('change', () => {
      localStorage.setItem('zerotts_saved_workers', workersSelect.value);
    });
  }

  // File Upload (.txt / .docx)
  if (uploadScriptBtn && scriptFileInput) {
    uploadScriptBtn.addEventListener('click', () => {
      scriptFileInput.click();
    });

    scriptFileInput.addEventListener('change', async (e) => {
      const file = e.target.files && e.target.files[0];
      if (file) {
        await handleUploadedScriptFile(file);
      }
      scriptFileInput.value = '';
    });
  }

  function readFileAsBase64(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => {
        const result = reader.result;
        const base64 = typeof result === 'string' && result.includes(',') ? result.split(',')[1] : result;
        resolve(base64);
      };
      reader.onerror = (err) => reject(err);
      reader.readAsDataURL(file);
    });
  }

  async function handleUploadedScriptFile(file) {
    try {
      uploadScriptBtn.textContent = '⏳ Đang nạp...';
      const base64Data = await readFileAsBase64(file);

      const res = await fetch('/api/upload-file', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          filename: file.name,
          content_base64: base64Data,
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || 'Không thể đọc tệp');
      }

      const data = await res.json();
      if (data.text) {
        mainTextInput.value = data.text;
        if (data.default_name && !customNameInput.value.trim() && data.total_projects <= 1) {
          customNameInput.value = data.default_name;
        }
        updateCharCount();
        mainTextInput.focus();
        
        let msg = `Đã nạp file: ${data.filename}`;
        if (data.total_projects > 1) {
          msg += ` (${data.total_projects} dự án, ${data.total_blocks} câu)`;
        } else {
          msg += ` (${data.total_blocks} câu)`;
        }
        progressMessage.textContent = `📄 ${msg}`;
      }
    } catch (err) {
      alert(`Lỗi khi nạp file: ${err.message}`);
    } finally {
      uploadScriptBtn.innerHTML = '📁 Nhập file (.txt/.docx)';
    }
  }

  // Drag and Drop File Upload
  const editorCard = document.querySelector('.editor-card');
  if (editorCard) {
    ['dragenter', 'dragover'].forEach((eventName) => {
      editorCard.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        editorCard.classList.add('drag-over');
      }, false);
    });

    ['dragleave', 'drop'].forEach((eventName) => {
      editorCard.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        editorCard.classList.remove('drag-over');
      }, false);
    });

    editorCard.addEventListener('drop', async (e) => {
      const dt = e.dataTransfer;
      const file = dt && dt.files && dt.files[0];
      if (file && (file.name.endsWith('.txt') || file.name.endsWith('.docx') || file.name.endsWith('.md'))) {
        await handleUploadedScriptFile(file);
      }
    }, false);
  }

  if (insertProjectBtn) {
    insertProjectBtn.addEventListener('click', () => {
      const val = mainTextInput.value;
      const matches = val.match(/\$\[(?:Dự án|Du_an|Project)\s*(\d+)\]/gi) || [];
      let nextIndex = 1;
      if (matches.length > 0) {
        const last = matches[matches.length - 1];
        const numMatch = last.match(/\d+/);
        if (numMatch) nextIndex = parseInt(numMatch[0], 10) + 1;
      } else {
        const allProjMatches = val.match(/\$\[(.*?)\]/g) || [];
        nextIndex = allProjMatches.length + 1;
      }
      const tagToInsert = `$[Dự án ${nextIndex}]\n[Text 1] `;
      const start = mainTextInput.selectionStart;
      const end = mainTextInput.selectionEnd;
      const textBefore = val.substring(0, start);
      const textAfter = val.substring(end);
      const newlineBefore = (start > 0 && val[start - 1] !== '\n') ? '\n\n' : '';
      
      mainTextInput.value = textBefore + newlineBefore + tagToInsert + textAfter;
      mainTextInput.selectionStart = mainTextInput.selectionEnd = start + newlineBefore.length + tagToInsert.length;
      mainTextInput.focus();
      updateCharCount();
    });
  }

  if (clearTextBtn) {
    clearTextBtn.addEventListener('click', () => {
      mainTextInput.value = '';
      updateCharCount();
      mainTextInput.focus();
    });
  }

  if (sampleTextBtn) {
    sampleTextBtn.addEventListener('click', () => {
      mainTextInput.value = SAMPLE_MULTI_PROJECT_TEXT;
      updateCharCount();
      mainTextInput.focus();
    });
  }

  if (insertPauseBtn) {
    insertPauseBtn.addEventListener('click', () => {
      const val = mainTextInput.value;
      const tagToInsert = ' [pause: 1.5s] ';
      const start = mainTextInput.selectionStart;
      const end = mainTextInput.selectionEnd;
      const textBefore = val.substring(0, start);
      const textAfter = val.substring(end);
      
      mainTextInput.value = textBefore + tagToInsert + textAfter;
      mainTextInput.selectionStart = mainTextInput.selectionEnd = start + tagToInsert.length;
      mainTextInput.focus();
      updateCharCount();
    });
  }

  if (insertTagBtn) {
    insertTagBtn.addEventListener('click', () => {
      const val = mainTextInput.value;
      const matches = val.match(/\[Text\s*(\d+)\]/gi) || [];
      let nextIndex = 1;
      if (matches.length > 0) {
        const last = matches[matches.length - 1];
        const numMatch = last.match(/\d+/);
        if (numMatch) nextIndex = parseInt(numMatch[0], 10) + 1;
      }
      const tagToInsert = `[Text ${nextIndex}] `;
      const start = mainTextInput.selectionStart;
      const end = mainTextInput.selectionEnd;
      const textBefore = val.substring(0, start);
      const textAfter = val.substring(end);
      const newlineBefore = (start > 0 && val[start - 1] !== '\n') ? '\n' : '';
      
      mainTextInput.value = textBefore + newlineBefore + tagToInsert + textAfter;
      mainTextInput.selectionStart = mainTextInput.selectionEnd = start + newlineBefore.length + tagToInsert.length;
      mainTextInput.focus();
      updateCharCount();
    });
  }

  // ── Voice List & Preview ──────────────────────────────────────────────────
  async function loadVoices() {
    try {
      voiceSelect.innerHTML = '<option value="">Đang tải giọng...</option>';
      const res = await fetch('/api/voices');
      const data = await res.json();
      voicesList = data.voices || [];

      voiceSelect.innerHTML = '';
      if (voicesList.length === 0) {
        voiceSelect.innerHTML = '<option value="">Không tìm thấy giọng nào</option>';
        return;
      }

      voicesList.forEach((v) => {
        const opt = document.createElement('option');
        opt.value = v.id;
        const tagsStr = v.tags && v.tags.length > 0 ? ` — ${v.tags.join(', ')}` : '';
        opt.textContent = `${v.name}${tagsStr}`;
        voiceSelect.appendChild(opt);
      });

      const savedVoice = localStorage.getItem('zerotts_voice');
      if (savedVoice && voicesList.some((v) => v.id === savedVoice)) {
        voiceSelect.value = savedVoice;
      } else if (data.default) {
        voiceSelect.value = data.default;
      }

      updateVoiceMeta();
    } catch (err) {
      console.error('Failed to load voices:', err);
      voiceSelect.innerHTML = '<option value="">Lỗi tải danh sách giọng</option>';
    }
  }

  function updateVoiceMeta() {
    const selectedId = voiceSelect.value;
    const voice = voicesList.find((v) => v.id === selectedId);
    voiceMeta.innerHTML = '';

    if (!voice) {
      voicePreviewAudio.src = '';
      return;
    }

    localStorage.setItem('zerotts_voice', selectedId);

    if (voice.tags && voice.tags.length > 0) {
      voice.tags.forEach((t) => {
        const tagSpan = document.createElement('span');
        tagSpan.className = 'voice-tag';
        tagSpan.textContent = t;
        voiceMeta.appendChild(tagSpan);
      });
    }

    if (voice.preview_url) {
      voicePreviewAudio.src = voice.preview_url;
    } else {
      voicePreviewAudio.src = '';
    }
  }

  voiceSelect.addEventListener('change', updateVoiceMeta);
  if (refreshVoicesBtn) refreshVoicesBtn.addEventListener('click', loadVoices);

  // ── History & File Management ─────────────────────────────────────────────
  async function loadHistoryFolders(preferredFolder = null, triggerFileSelect = true) {
    if (refreshHistoryBtn) refreshHistoryBtn.classList.add('spinning');
    try {
      const res = await fetch('/api/history/folders');
      const data = await res.json();
      const folders = data.folders || [];

      const savedFolder = localStorage.getItem('zerotts_last_folder');
      const targetFolder = preferredFolder || historyFolderSelect.value || savedFolder;

      historyFolderSelect.innerHTML = '';
      if (folders.length === 0) {
        historyFolderSelect.innerHTML = '<option value="">Chưa có dự án nào</option>';
        historyFileSelect.innerHTML = '<option value="">Chưa có file</option>';
        setAudioPlayer(null, null);
        segmentsDetailsBox.textContent = 'Chưa có dữ liệu phân đoạn.';
        return;
      }

      folders.forEach((f) => {
        const opt = document.createElement('option');
        opt.value = f.folder_name;
        opt.textContent = f.label;
        historyFolderSelect.appendChild(opt);
      });

      if (targetFolder && folders.some((f) => f.folder_name === targetFolder)) {
        historyFolderSelect.value = targetFolder;
      }

      if (triggerFileSelect) {
        await onFolderSelected();
      }
    } catch (err) {
      console.error('Failed to load history folders:', err);
    } finally {
      if (refreshHistoryBtn) {
        setTimeout(() => refreshHistoryBtn.classList.remove('spinning'), 500);
      }
    }
  }

  async function onFolderSelected(preferredFile = null) {
    const folder = historyFolderSelect.value;
    lastActiveFolder = folder;
    if (folder) {
      localStorage.setItem('zerotts_last_folder', folder);
    }

    if (!folder) {
      historyFileSelect.innerHTML = '<option value="">Chưa có file</option>';
      setAudioPlayer(null, null);
      segmentsDetailsBox.textContent = 'Chưa có dữ liệu phân đoạn.';
      return;
    }

    try {
      const res = await fetch(`/api/history/files?folder=${encodeURIComponent(folder)}`);
      const data = await res.json();
      const files = data.files || [];

      const savedFile = localStorage.getItem('zerotts_last_file');
      const targetFile = preferredFile || historyFileSelect.value || savedFile;

      historyFileSelect.innerHTML = '';
      if (files.length === 0) {
        historyFileSelect.innerHTML = '<option value="">Thư mục trống</option>';
        setAudioPlayer(null, null);
        segmentsDetailsBox.textContent = 'Chưa có dữ liệu phân đoạn.';
        return;
      }

      files.forEach((file) => {
        const opt = document.createElement('option');
        opt.value = file.path;
        opt.textContent = file.label;
        historyFileSelect.appendChild(opt);
      });

      if (targetFile && files.some((f) => f.path === targetFile)) {
        historyFileSelect.value = targetFile;
      }

      await onFileSelected();
    } catch (err) {
      console.error('Failed to load folder files:', err);
    }
  }

  async function onFileSelected() {
    const filePath = historyFileSelect.value;
    const folder = historyFolderSelect.value;

    if (!filePath) {
      setAudioPlayer(null, null);
      segmentsDetailsBox.textContent = 'Chưa có dữ liệu phân đoạn.';
      return;
    }

    localStorage.setItem('zerotts_last_file', filePath);

    const fileName = filePath.split(/[/\\]/).pop();
    const fileUrl = `/api/audio-file?path=${encodeURIComponent(filePath)}`;
    
    // Immediately set audio and trigger waveform rendering without blocking UI
    setAudioPlayer(fileUrl, fileName);

    // Fetch segment timeline details concurrently in background
    fetch(`/api/history/details?folder=${encodeURIComponent(folder)}&file=${encodeURIComponent(filePath)}`)
      .then((res) => res.json())
      .then((data) => {
        segmentsDetailsBox.textContent = data.details || 'Không có chi tiết phân đoạn.';
      })
      .catch((err) => {
        console.error('Failed to load details:', err);
      });
  }

  let audioCtx = null;
  let currentWaveformUrl = null;
  let currentAudioBuffer = null;
  let currentPeaks = null;
  let isScrubbingWaveform = false;
  let currentZoom = 1.0;

  const MIN_ZOOM = 1.0;
  const MAX_ZOOM = 16.0;
  const ZOOM_STEP = 1.4;

  function updateWaveformDimensions() {
    if (!waveformCanvas || !waveformScrollContainer) return;
    const baseWidth = waveformScrollContainer.clientWidth || 600;
    const targetWidth = Math.round(baseWidth * currentZoom);
    waveformCanvas.width = targetWidth;
    waveformCanvas.style.width = `${targetWidth}px`;
    if (waveformZoomLevel) {
      waveformZoomLevel.textContent = `${currentZoom.toFixed(1)}x`;
    }
  }

  function computePeaks(audioBuffer, width) {
    if (!audioBuffer || width <= 0) return null;
    const channelData = audioBuffer.getChannelData(0);
    const step = Math.ceil(channelData.length / width);
    const peaks = new Array(width);

    for (let i = 0; i < width; i++) {
      let min = 1.0;
      let max = -1.0;
      const start = i * step;
      const end = Math.min(start + step, channelData.length);

      for (let j = start; j < end; j++) {
        const val = channelData[j];
        if (val < min) min = val;
        if (val > max) max = val;
      }

      if (min > max) {
        min = 0;
        max = 0;
      }

      peaks[i] = { min, max };
    }
    return peaks;
  }

  function renderWaveform(progress = 0) {
    if (!waveformCanvas || !currentPeaks) return;
    const ctx = waveformCanvas.getContext('2d');
    const width = waveformCanvas.width;
    const height = waveformCanvas.height;
    const amp = height / 2;

    ctx.clearRect(0, 0, width, height);

    const playX = Math.floor(progress * width);

    for (let i = 0; i < width; i++) {
      const peak = currentPeaks[i];
      if (!peak) continue;
      const { min, max } = peak;
      const y1 = (1 + min) * amp;
      const y2 = (1 + max) * amp;
      const h = Math.max(1, y2 - y1);

      if (i <= playX) {
        ctx.fillStyle = '#f4530c';
      } else {
        ctx.fillStyle = 'rgba(244, 83, 12, 0.32)';
      }
      ctx.fillRect(i, y1, 1, h);
    }

    if (progress > 0 && progress < 1) {
      ctx.fillStyle = '#ffffff';
      ctx.fillRect(playX, 0, 1.5, height);
    }
  }

  function applyZoom(newZoom, cursorClientX = null) {
    const clampedZoom = Math.max(MIN_ZOOM, Math.min(MAX_ZOOM, parseFloat(newZoom.toFixed(2))));
    if (Math.abs(clampedZoom - currentZoom) < 0.01) return;

    let cursorRatio = 0.5;
    let cursorOffsetInContainer = (waveformScrollContainer ? waveformScrollContainer.clientWidth : 600) / 2;

    if (waveformScrollContainer && cursorClientX !== null) {
      const rect = waveformScrollContainer.getBoundingClientRect();
      cursorOffsetInContainer = Math.max(0, Math.min(waveformScrollContainer.clientWidth, cursorClientX - rect.left));
      const currentContentX = waveformScrollContainer.scrollLeft + cursorOffsetInContainer;
      cursorRatio = currentContentX / (waveformCanvas.width || 1);
    }

    currentZoom = clampedZoom;
    updateWaveformDimensions();

    if (currentAudioBuffer) {
      currentPeaks = computePeaks(currentAudioBuffer, waveformCanvas.width);
      const currentProgress = (mainAudioPlayer.duration && !isNaN(mainAudioPlayer.duration))
        ? mainAudioPlayer.currentTime / mainAudioPlayer.duration
        : 0;
      renderWaveform(currentProgress);
    }

    if (waveformScrollContainer) {
      if (currentZoom > 1.0) {
        const newContentX = cursorRatio * waveformCanvas.width;
        waveformScrollContainer.scrollLeft = newContentX - cursorOffsetInContainer;
      } else {
        waveformScrollContainer.scrollLeft = 0;
      }
    }
  }

  async function drawWaveform(url) {
    if (!waveformCanvas) return;
    currentWaveformUrl = url;
    currentAudioBuffer = null;
    currentPeaks = null;

    updateWaveformDimensions();
    const ctx = waveformCanvas.getContext('2d');
    ctx.clearRect(0, 0, waveformCanvas.width, waveformCanvas.height);
    if (!url) return;

    try {
      if (!audioCtx) {
        audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      }
      const response = await fetch(url);
      const arrayBuffer = await response.arrayBuffer();
      const audioBuffer = await audioCtx.decodeAudioData(arrayBuffer);

      if (currentWaveformUrl !== url) return;

      currentAudioBuffer = audioBuffer;
      updateWaveformDimensions();
      currentPeaks = computePeaks(currentAudioBuffer, waveformCanvas.width);

      const initialProgress = (mainAudioPlayer.duration && !isNaN(mainAudioPlayer.duration))
        ? mainAudioPlayer.currentTime / mainAudioPlayer.duration
        : 0;
      renderWaveform(initialProgress);
    } catch (err) {
      console.error('Error drawing waveform:', err);
    }
  }

  function seekAudioFromWaveform(e) {
    if (!mainAudioPlayer.duration || isNaN(mainAudioPlayer.duration)) return;
    const rect = waveformCanvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const ratio = Math.max(0, Math.min(1, x / rect.width));
    mainAudioPlayer.currentTime = ratio * mainAudioPlayer.duration;
    renderWaveform(ratio);
  }

  if (zoomInWaveformBtn) zoomInWaveformBtn.addEventListener('click', () => applyZoom(currentZoom * ZOOM_STEP));
  if (zoomOutWaveformBtn) zoomOutWaveformBtn.addEventListener('click', () => applyZoom(currentZoom / ZOOM_STEP));
  if (zoomResetWaveformBtn) zoomResetWaveformBtn.addEventListener('click', () => applyZoom(1.0));

  if (waveformScrollContainer) {
    waveformScrollContainer.addEventListener('wheel', (e) => {
      if (e.ctrlKey || e.altKey) {
        e.preventDefault();
        const factor = e.deltaY < 0 ? ZOOM_STEP : 1 / ZOOM_STEP;
        applyZoom(currentZoom * factor, e.clientX);
      }
    }, { passive: false });
  }

  window.addEventListener('resize', () => {
    if (currentAudioBuffer) {
      updateWaveformDimensions();
      currentPeaks = computePeaks(currentAudioBuffer, waveformCanvas.width);
      const currentProgress = (mainAudioPlayer.duration && !isNaN(mainAudioPlayer.duration))
        ? mainAudioPlayer.currentTime / mainAudioPlayer.duration
        : 0;
      renderWaveform(currentProgress);
    }
  });

  if (waveformCanvas) {
    waveformCanvas.addEventListener('click', seekAudioFromWaveform);
    waveformCanvas.addEventListener('mousedown', (e) => {
      isScrubbingWaveform = true;
      seekAudioFromWaveform(e);
    });
    window.addEventListener('mousemove', (e) => {
      if (isScrubbingWaveform) {
        seekAudioFromWaveform(e);
      }
    });
    window.addEventListener('mouseup', () => {
      if (isScrubbingWaveform) isScrubbingWaveform = false;
    });
  }

  if (mainAudioPlayer) {
    mainAudioPlayer.addEventListener('timeupdate', () => {
      if (mainAudioPlayer.duration && !isNaN(mainAudioPlayer.duration)) {
        const progress = mainAudioPlayer.currentTime / mainAudioPlayer.duration;
        renderWaveform(progress);

        if (currentZoom > 1.0 && waveformScrollContainer && !isScrubbingWaveform && !mainAudioPlayer.paused) {
          const playX = progress * waveformCanvas.width;
          const left = waveformScrollContainer.scrollLeft;
          const viewWidth = waveformScrollContainer.clientWidth;
          if (playX < left || playX > left + viewWidth - 60) {
            waveformScrollContainer.scrollLeft = playX - viewWidth / 3;
          }
        }
      }
    });
    mainAudioPlayer.addEventListener('ended', () => {
      renderWaveform(0);
      if (waveformScrollContainer) waveformScrollContainer.scrollLeft = 0;
    });
  }

  function setAudioPlayer(url, label) {
    if (url) {
      mainAudioPlayer.src = url;
      currentAudioLabel.textContent = `🎵 ${label || 'Bản thu'}`;
      drawWaveform(url);
    } else {
      mainAudioPlayer.src = '';
      currentAudioLabel.textContent = '🎵 Chưa có bản thu nào';
      drawWaveform(null);
    }
  }

  historyFolderSelect.addEventListener('change', () => onFolderSelected());
  historyFolderSelect.addEventListener('input', () => onFolderSelected());
  historyFolderSelect.addEventListener('focus', () => {
    // Light background sync without changing user selection
    fetch('/api/history/folders')
      .then((res) => res.json())
      .then((data) => {
        const folders = data.folders || [];
        const cur = historyFolderSelect.value;
        if (folders.length > 0 && folders.length !== historyFolderSelect.options.length) {
          loadHistoryFolders(cur, false);
        }
      })
      .catch(() => {});
  });

  historyFileSelect.addEventListener('change', onFileSelected);
  historyFileSelect.addEventListener('input', onFileSelected);
  if (refreshHistoryBtn) {
    refreshHistoryBtn.addEventListener('click', () => loadHistoryFolders(historyFolderSelect.value, true));
  }

  window.addEventListener('focus', () => {
    if (generateBtn && !generateBtn.disabled) {
      loadHistoryFolders(historyFolderSelect.value, false);
    }
  });

  // ── Folder & Audio Actions ────────────────────────────────────────────────
  if (concatBtn) {
    concatBtn.addEventListener('click', async () => {
      const folder = historyFolderSelect.value;
      if (!folder || folder === '__legacy__') {
        alert('Vui lòng chọn một thư mục dự án hợp lệ để nối audio.');
        return;
      }

      concatBtn.disabled = true;
      concatBtn.textContent = '⏳ Đang nối...';

      try {
        const res = await fetch('/api/concat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            folder_name: folder,
            merged_format: mergedFormatSelect.value,
          }),
        });

        const data = await res.json();
        if (!res.ok) {
          alert(`Lỗi: ${data.detail || 'Không thể nối file'}`);
          return;
        }

        await loadHistoryFolders(folder);
        if (data.merged_path) {
          historyFileSelect.value = data.merged_path;
          setAudioPlayer(data.file_url, data.file_name);
        }
        if (data.details) {
          segmentsDetailsBox.textContent = data.details;
        }
        progressMessage.textContent = `⭐ ${data.message}`;
      } catch (err) {
        alert(`Lỗi kết nối: ${err.message}`);
      } finally {
        concatBtn.disabled = false;
        concatBtn.innerHTML = '<span>🔗</span> Nối tất cả audio';
      }
    });
  }

  async function openFolder(pathOrName) {
    try {
      const res = await fetch('/api/open-folder', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ folder_name_or_path: pathOrName }),
      });
      const data = await res.json();
      progressMessage.textContent = data.status || 'Đã mở thư mục.';
    } catch (err) {
      console.error('Failed to open folder:', err);
    }
  }

  if (openHistoryFolderBtn) {
    openHistoryFolderBtn.addEventListener('click', () => openFolder(historyFolderSelect.value));
  }
  if (openOutputFolderBtn) {
    openOutputFolderBtn.addEventListener('click', () => openFolder(lastActiveFolder || historyFolderSelect.value));
  }

  // ── Mode Explanation & Presets ───────────────────────────────────────────
  const MODE_EXPLANATIONS = {
    voice: '<strong>Gói giọng (Voice Pack):</strong> Bắt chước âm sắc, phong cách và ngữ điệu từ tệp âm thanh mẫu của gói giọng được chọn.',
    uncond: '<strong>Tự do (Unconditioned):</strong> Mô hình tự do sáng tạo giọng đọc ngẫu nhiên trực tiếp từ văn bản mà không bị ràng buộc vào file mẫu (tốc độ xử lý nhanh hơn, chất giọng biến thiên phong phú).',
  };

  function updateModeExplanation() {
    if (modeExplanationText && modeSelect && MODE_EXPLANATIONS[modeSelect.value]) {
      modeExplanationText.innerHTML = MODE_EXPLANATIONS[modeSelect.value];
    }
  }

  if (modeSelect) {
    modeSelect.addEventListener('change', updateModeExplanation);
  }

  // ── Sliders & Presets ─────────────────────────────────────────────────────
  function bindSlider(slider, display, suffix = '') {
    slider.addEventListener('input', () => {
      display.textContent = `${slider.value}${suffix}`;
    });
  }

  bindSlider(cfgSlider, cfgVal);
  bindSlider(chunkSecSlider, chunkSecVal, ' s');
  bindSlider(tempSlider, tempVal);
  bindSlider(topkSlider, topkVal);
  bindSlider(toppSlider, toppVal);
  bindSlider(repSlider, repVal);
  bindSlider(eoaSlider, eoaVal);

  const advancedControls = [
    modeSelect,
    cfgSlider,
    chunkSecSlider,
    tempSlider,
    topkSlider,
    toppSlider,
    repSlider,
    eoaSlider,
  ];

  function setAdvancedLocked(isLocked) {
    advancedControls.forEach((el) => {
      if (el) el.disabled = isLocked;
    });

    if (advancedOptionsCard) {
      advancedOptionsCard.classList.toggle('is-locked', isLocked);
    }

    if (advancedLockBadge) {
      if (isLocked) {
        advancedLockBadge.className = 'badge-lock locked';
        advancedLockBadge.textContent = '🔒 Khóa theo Preset';
      } else {
        advancedLockBadge.className = 'badge-lock unlocked';
        advancedLockBadge.textContent = '🔓 Đang tùy chỉnh';
      }
    }

    if (advancedLockNotice) {
      if (isLocked) {
        advancedLockNotice.innerHTML = '<span>🔒 Các tham số đang khóa tự động theo Preset. <button type="button" id="switchToCustomBtn" class="notice-link-btn">Bật chế độ Tùy chỉnh 🛠️</button></span>';
        const switchBtn = document.getElementById('switchToCustomBtn');
        if (switchBtn) {
          switchBtn.addEventListener('click', activateCustomPreset);
        }
      } else {
        advancedLockNotice.innerHTML = '<span>✨ <strong>Chế độ Tùy chỉnh:</strong> Mở khóa toàn bộ tham số. Bạn có thể tự do điều chỉnh thanh trượt theo ý muốn.</span>';
      }
    }
  }

  function activateCustomPreset() {
    const customRadio = document.querySelector('input[name="preset"][value="custom"]');
    if (customRadio) {
      customRadio.checked = true;
      document.querySelectorAll('.preset-pill').forEach((p) => p.classList.remove('active'));
      const pill = customRadio.closest('.preset-pill');
      if (pill) pill.classList.add('active');
      setAdvancedLocked(false);
    }
  }

  presetRadios.forEach((radio) => {
    radio.addEventListener('change', () => {
      document.querySelectorAll('.preset-pill').forEach((p) => p.classList.remove('active'));
      const pill = radio.closest('.preset-pill');
      if (pill) pill.classList.add('active');

      if (radio.value === 'custom') {
        setAdvancedLocked(false);
      } else {
        const preset = PRESETS[radio.value];
        if (preset) {
          cfgSlider.value = preset.cfg;
          cfgVal.textContent = preset.cfg.toFixed(1);

          tempSlider.value = preset.temp;
          tempVal.textContent = preset.temp.toFixed(2);

          topkSlider.value = preset.topk;
          topkVal.textContent = preset.topk;

          toppSlider.value = preset.topp;
          toppVal.textContent = preset.topp.toFixed(2);

          repSlider.value = preset.rep;
          repVal.textContent = preset.rep.toFixed(2);
        }
        setAdvancedLocked(true);
      }
    });
  });

  // ── Synthesis & SSE Streaming Engine ──────────────────────────────────────
  function setGeneratingState(isBusy, customText = null, customType = 'busy') {
    generateBtn.disabled = isBusy;
    stopBtn.disabled = !isBusy;

    if (generateSpinner) generateSpinner.style.display = isBusy ? 'inline-block' : 'none';
    if (generateIcon) generateIcon.style.display = isBusy ? 'none' : 'inline';
    if (generateShortcut) generateShortcut.style.display = isBusy ? 'none' : 'inline-block';
    if (generateLabel) generateLabel.textContent = isBusy ? (customText || 'Đang tạo...') : 'Tạo giọng nói';

    if (progressSpinner) progressSpinner.style.display = isBusy ? 'inline-block' : 'none';
    if (progressStatusBox) progressStatusBox.classList.toggle('is-active', isBusy);

    if (isBusy) {
      if (customType === 'loading') {
        systemStatus.className = 'status-pill status-loading';
        systemStatusText.textContent = customText || 'Đang nạp mô hình...';
      } else if (customType === 'merging') {
        systemStatus.className = 'status-pill status-merging';
        systemStatusText.textContent = customText || 'Đang ghép file...';
      } else {
        systemStatus.className = 'status-pill status-busy';
        systemStatusText.textContent = customText || 'Đang tạo...';
      }
      progressBarFill.classList.add('active');
      progressBarFill.style.width = '100%';
    } else {
      systemStatus.className = 'status-pill status-ready';
      systemStatusText.textContent = 'Sẵn sàng';
      progressBarFill.classList.remove('active');
      progressBarFill.style.width = '0%';
    }
  }

  async function startGeneration() {
    const text = mainTextInput.value.trim();
    if (!text) {
      alert('Vui lòng nhập văn bản tiếng Việt cần tạo giọng nói.');
      mainTextInput.focus();
      return;
    }

    if (modeSelect.value === 'voice' && !voiceSelect.value) {
      alert('Vui lòng chọn một giọng đọc trước.');
      return;
    }

    setGeneratingState(true, 'Đang khởi tạo...', 'loading');
    progressMessage.textContent = '⏳ Khởi động quá trình tạo giọng nói...';
    segmentsDetailsBox.textContent = 'Đang phân đoạn câu...';

    abortController = new AbortController();

    const payload = {
      text: text,
      voice_name: voiceSelect.value,
      mode: modeSelect.value,
      custom_name: customNameInput.value.trim(),
      overwrite_mode: overwriteModeSelect.value,
      auto_concat: autoConcatCheck.checked,
      merged_format: mergedFormatSelect.value,
      max_chunk_sec: parseFloat(chunkSecSlider.value),
      cfg_scale: parseFloat(cfgSlider.value),
      temperature: parseFloat(tempSlider.value),
      topk: parseInt(topkSlider.value, 10),
      topp: parseFloat(toppSlider.value),
      repetition_penalty: parseFloat(repSlider.value),
      eoa_extra_frames: parseInt(eoaSlider.value, 10),
      num_workers: parseInt(workersSelect ? workersSelect.value : 1, 10),
    };

    try {
      const response = await fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        signal: abortController.signal,
      });

      if (!response.ok) {
        const errJson = await response.json().catch(() => ({}));
        throw new Error(errJson.detail || `Lỗi máy chủ (${response.status})`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      function processSSEBlock(block) {
        if (!block.trim()) return;
        let eventType = 'message';
        let dataStr = '';

        block.split('\n').forEach((line) => {
          if (line.startsWith('event:')) eventType = line.substring(6).trim();
          else if (line.startsWith('data:')) dataStr = line.substring(5).trim();
        });

        if (!dataStr) return;

        try {
          const data = JSON.parse(dataStr);
          handleSSEEvent(eventType, data);
        } catch (e) {
          console.error('SSE JSON parse error:', e, dataStr);
        }
      }

      while (true) {
        const { value, done } = await reader.read();
        if (done) {
          if (buffer.trim()) {
            buffer.split('\n\n').forEach(processSSEBlock);
            buffer = '';
          }
          break;
        }

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop(); // Keep partial tail

        for (const block of lines) {
          processSSEBlock(block);
        }
      }
    } catch (err) {
      if (err.name === 'AbortError') {
        progressMessage.textContent = '⏹️ Đã dừng quá trình tạo.';
      } else {
        progressMessage.textContent = `❌ Lỗi: ${err.message}`;
        alert(`Đã xảy ra lỗi: ${err.message}`);
      }
    } finally {
      setGeneratingState(false);
      abortController = null;
    }
  }

  function handleSSEEvent(type, data) {
    if (type === 'start') {
      setGeneratingState(true, 'Đang nạp mô hình...', 'loading');
      progressMessage.textContent = '🎙️ Bắt đầu sinh âm thanh...';
    } else if (type === 'progress') {
      if (data.status) {
        progressMessage.textContent = data.status;
        const statusLower = data.status.toLowerCase();
        if (statusLower.includes('xong') || statusLower.includes('hoàn thành') || statusLower.includes('hoàn tất')) {
          setGeneratingState(false);
        } else if (statusLower.includes('nối') || statusLower.includes('ghép') || statusLower.includes('merge')) {
          setGeneratingState(true, 'Đang ghép file...', 'merging');
        } else {
          setGeneratingState(true, 'Đang sinh audio...', 'busy');
        }
      }
      if (data.queue && data.queue.total_projects > 1) {
        const q = data.queue;
        progressPercent.textContent = `Dự án ${q.project_index}/${q.total_projects}`;
      } else {
        progressPercent.textContent = '';
      }
      if (data.segments) segmentsDetailsBox.textContent = data.segments;
      if (data.file_url) {
        setAudioPlayer(data.file_url, data.file_name);
      }
    } else if (type === 'complete') {
      setGeneratingState(false);
      progressPercent.textContent = '';
      if (data.all_folders && data.all_folders.length > 1) {
        progressMessage.textContent = `✅ Đã hoàn thành ${data.all_folders.length} dự án: ${data.all_folders.join(', ')}`;
      } else {
        progressMessage.textContent = '✅ Đã hoàn thành!';
      }
      if (data.file_url) {
        setAudioPlayer(data.file_url, data.file_name);
        mainAudioPlayer.play().catch(() => {});
      }
      if (data.details) {
        segmentsDetailsBox.textContent = data.details;
      }
      if (data.folder_name) {
        lastActiveFolder = data.folder_name;
        loadHistoryFolders(data.folder_name);
      }
    } else if (type === 'error') {
      setGeneratingState(false);
      progressPercent.textContent = '';
      progressMessage.textContent = `❌ Lỗi: ${data.error}`;
    }
  }

  function stopGeneration() {
    if (abortController) {
      abortController.abort();
      abortController = null;
    }
    setGeneratingState(false);
  }

  generateBtn.addEventListener('click', () => {
    if (!generateBtn.disabled) startGeneration();
  });
  stopBtn.addEventListener('click', () => {
    if (!stopBtn.disabled) stopGeneration();
  });

  // ── Keyboard Shortcuts ────────────────────────────────────────────────────
  document.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      if (!generateBtn.disabled) startGeneration();
    } else if (e.key === 'Escape') {
      if (!stopBtn.disabled) stopGeneration();
    }
  });

  // ── Mobile Notice Modal Trolling Easter Egg ──────────────────────────────
  const mobileNoticeModal = document.getElementById('mobileNoticeModal');
  const dismissMobileNoticeBtn = document.getElementById('dismissMobileNoticeBtn');

  const TROLL_MESSAGES = [
    'Bấm trúng đi đã 😜',
    'Đã bảo dùng máy tính mà! 💻',
    'Hụt rồi nha! 🏃‍♂️💨',
    'Không tắt được đâu! 😂',
    'Cố lên nào... đùa đấy 🤣',
    'Mở laptop lên bạn ơi! 🖥️',
    'Nhanh tay hơn nữa xem! ⚡',
    'Ủa tưởng dễ bấm lắm à? 🤭',
  ];

  let trollIndex = 0;

  function dodgeDismissButton(e) {
    if (!dismissMobileNoticeBtn) return;
    if (e) {
      e.preventDefault();
      e.stopPropagation();
    }

    const maxOffsetX = 120;
    const maxOffsetY = 80;
    const randX = (Math.random() * 2 - 1) * maxOffsetX;
    const randY = (Math.random() * 2 - 1) * maxOffsetY;

    dismissMobileNoticeBtn.style.transform = `translate(${randX.toFixed(0)}px, ${randY.toFixed(0)}px)`;

    trollIndex = (trollIndex + 1) % TROLL_MESSAGES.length;
    dismissMobileNoticeBtn.innerHTML = `<span>${TROLL_MESSAGES[trollIndex]}</span>`;

    if (navigator.vibrate) {
      try { navigator.vibrate(40); } catch (_) {}
    }
  }

  if (dismissMobileNoticeBtn) {
    dismissMobileNoticeBtn.addEventListener('mouseenter', dodgeDismissButton);
    dismissMobileNoticeBtn.addEventListener('touchstart', dodgeDismissButton, { passive: false });
    dismissMobileNoticeBtn.addEventListener('pointerdown', dodgeDismissButton);
    dismissMobileNoticeBtn.addEventListener('click', dodgeDismissButton);
  }

  // ── Initial Boot ──────────────────────────────────────────────────────────
  window.addEventListener('DOMContentLoaded', () => {
    initTheme();
    const saved = localStorage.getItem('zerotts_saved_text');
    if (saved) {
      mainTextInput.value = saved;
    }
    updateCharCount();

    loadVoices();
    loadHistoryFolders();
    updateModeExplanation();

    const selectedPresetRadio = document.querySelector('input[name="preset"]:checked');
    if (selectedPresetRadio) {
      setAdvancedLocked(selectedPresetRadio.value !== 'custom');
    } else {
      setAdvancedLocked(true);
    }
  });
})();
