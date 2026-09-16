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

  const mainTextInput = document.getElementById('mainTextInput');
  const charCount = document.getElementById('charCount');
  const insertTagBtn = document.getElementById('insertTagBtn');
  const clearTextBtn = document.getElementById('clearTextBtn');
  const sampleTextBtn = document.getElementById('sampleTextBtn');

  const customNameInput = document.getElementById('customNameInput');
  const overwriteModeSelect = document.getElementById('overwriteModeSelect');
  const autoConcatCheck = document.getElementById('autoConcatCheck');
  const mergedFormatSelect = document.getElementById('mergedFormatSelect');

  const generateBtn = document.getElementById('generateBtn');
  const stopBtn = document.getElementById('stopBtn');

  const progressMessage = document.getElementById('progressMessage');
  const progressPercent = document.getElementById('progressPercent');
  const progressBarFill = document.getElementById('progressBarFill');

  const mainAudioPlayer = document.getElementById('mainAudioPlayer');
  const currentAudioLabel = document.getElementById('currentAudioLabel');
  const downloadAudioLink = document.getElementById('downloadAudioLink');
  const segmentsDetailsBox = document.getElementById('segmentsDetailsBox');

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

  const SAMPLE_TEXT = `[Text 1] Xin chào tất cả mọi người! Chào mừng các bạn đã đến với ZeroTTS Bản Mod.
[Text 2] Hệ thống này hỗ trợ tạo giọng đọc tiếng Việt mượt mà với tốc độ cực nhanh ngay trên CPU.
[Text 3] Bạn có thể chia đoạn linh hoạt và ghép nối tự động thành tệp âm thanh hoàn chỉnh.`;

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

  // ── Textarea Management ───────────────────────────────────────────────────
  function updateCharCount() {
    const len = mainTextInput.value.length;
    charCount.textContent = `${len} / 5000`;
    charCount.style.color = len > 5000 ? '#ef4444' : '';
    localStorage.setItem('zerotts_saved_text', mainTextInput.value);
  }

  mainTextInput.addEventListener('input', updateCharCount);

  if (clearTextBtn) {
    clearTextBtn.addEventListener('click', () => {
      mainTextInput.value = '';
      updateCharCount();
      mainTextInput.focus();
    });
  }

  if (sampleTextBtn) {
    sampleTextBtn.addEventListener('click', () => {
      mainTextInput.value = SAMPLE_TEXT;
      updateCharCount();
      mainTextInput.focus();
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
  async function loadHistoryFolders(preferredFolder = null) {
    try {
      const res = await fetch('/api/history/folders');
      const data = await res.json();
      const folders = data.folders || [];

      historyFolderSelect.innerHTML = '';
      if (folders.length === 0) {
        historyFolderSelect.innerHTML = '<option value="">Chưa có dự án nào</option>';
        historyFileSelect.innerHTML = '<option value="">Chưa có file</option>';
        return;
      }

      folders.forEach((f) => {
        const opt = document.createElement('option');
        opt.value = f.folder_name;
        opt.textContent = f.label;
        historyFolderSelect.appendChild(opt);
      });

      if (preferredFolder && folders.some((f) => f.folder_name === preferredFolder)) {
        historyFolderSelect.value = preferredFolder;
      }

      await onFolderSelected();
    } catch (err) {
      console.error('Failed to load history folders:', err);
    }
  }

  async function onFolderSelected() {
    const folder = historyFolderSelect.value;
    lastActiveFolder = folder;
    if (!folder) {
      historyFileSelect.innerHTML = '<option value="">Chưa có file</option>';
      return;
    }

    try {
      const res = await fetch(`/api/history/files?folder=${encodeURIComponent(folder)}`);
      const data = await res.json();
      const files = data.files || [];

      historyFileSelect.innerHTML = '';
      if (files.length === 0) {
        historyFileSelect.innerHTML = '<option value="">Thư mục trống</option>';
        return;
      }

      files.forEach((file) => {
        const opt = document.createElement('option');
        opt.value = file.path;
        opt.textContent = file.label;
        historyFileSelect.appendChild(opt);
      });

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

    const fileName = filePath.split(/[/\\]/).pop();
    const fileUrl = `/api/audio-file?path=${encodeURIComponent(filePath)}`;
    setAudioPlayer(fileUrl, fileName);

    // Fetch segment timeline details
    try {
      const res = await fetch(`/api/history/details?folder=${encodeURIComponent(folder)}&file=${encodeURIComponent(filePath)}`);
      const data = await res.json();
      segmentsDetailsBox.textContent = data.details || 'Không có chi tiết phân đoạn.';
    } catch (err) {
      console.error('Failed to load details:', err);
    }
  }

  function setAudioPlayer(url, label) {
    if (url) {
      mainAudioPlayer.src = url;
      currentAudioLabel.textContent = `🎵 ${label || 'Bản thu'}`;
      downloadAudioLink.href = url;
      downloadAudioLink.download = label || 'output.wav';
      downloadAudioLink.style.display = 'inline-block';
    } else {
      mainAudioPlayer.src = '';
      currentAudioLabel.textContent = '🎵 Chưa có bản thu nào';
      downloadAudioLink.style.display = 'none';
    }
  }

  historyFolderSelect.addEventListener('change', onFolderSelected);
  historyFileSelect.addEventListener('change', onFileSelected);
  if (refreshHistoryBtn) refreshHistoryBtn.addEventListener('click', () => loadHistoryFolders(historyFolderSelect.value));

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

  presetRadios.forEach((radio) => {
    radio.addEventListener('change', () => {
      document.querySelectorAll('.preset-pill').forEach((p) => p.classList.remove('active'));
      radio.closest('.preset-pill').classList.add('active');

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
    });
  });

  // ── Synthesis & SSE Streaming Engine ──────────────────────────────────────
  function setGeneratingState(isBusy) {
    generateBtn.disabled = isBusy;
    stopBtn.disabled = !isBusy;
    if (isBusy) {
      systemStatus.className = 'status-pill status-busy';
      systemStatusText.textContent = 'Đang tạo...';
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

    setGeneratingState(true);
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

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop(); // Keep partial tail

        for (const block of lines) {
          if (!block.trim()) continue;
          let eventType = 'message';
          let dataStr = '';

          block.split('\n').forEach((line) => {
            if (line.startsWith('event:')) eventType = line.substring(6).trim();
            else if (line.startsWith('data:')) dataStr = line.substring(5).trim();
          });

          if (!dataStr) continue;

          try {
            const data = JSON.parse(dataStr);
            handleSSEEvent(eventType, data);
          } catch (e) {
            console.error('SSE JSON parse error:', e, dataStr);
          }
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
      progressMessage.textContent = '🎙️ Bắt đầu sinh âm thanh...';
    } else if (type === 'progress') {
      if (data.status) progressMessage.textContent = data.status;
      if (data.segments) segmentsDetailsBox.textContent = data.segments;
      if (data.file_url) {
        setAudioPlayer(data.file_url, data.file_name);
      }
    } else if (type === 'complete') {
      progressMessage.textContent = '✅ Đã hoàn thành!';
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
      progressMessage.textContent = `❌ Lỗi: ${data.error}`;
    }
  }

  function stopGeneration() {
    if (abortController) {
      abortController.abort();
    }
  }

  generateBtn.addEventListener('click', startGeneration);
  stopBtn.addEventListener('click', stopGeneration);

  // ── Keyboard Shortcuts ────────────────────────────────────────────────────
  document.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      if (!generateBtn.disabled) startGeneration();
    } else if (e.key === 'Escape') {
      if (!stopBtn.disabled) stopGeneration();
    }
  });

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
  });
})();
