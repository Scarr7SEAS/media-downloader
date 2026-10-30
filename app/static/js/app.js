document.addEventListener('DOMContentLoaded', () => {
    // Elements
    const urlForm = document.getElementById('urlForm');
    const videoUrlInput = document.getElementById('videoUrl');
    const pasteBtn = document.getElementById('pasteBtn');
    const fetchBtn = document.getElementById('fetchBtn');
    const urlError = document.getElementById('urlError');

    const previewCard = document.getElementById('previewCard');
    const thumbImg = document.getElementById('thumbImg');
    const videoDuration = document.getElementById('videoDuration');
    const extractorTag = document.getElementById('extractorTag');
    const uploaderName = document.getElementById('uploaderName');
    const videoTitle = document.getElementById('videoTitle');
    const startDownloadBtn = document.getElementById('startDownloadBtn');
    const qualityCards = document.querySelectorAll('.quality-card');

    const progressCard = document.getElementById('progressCard');
    const progressStatus = document.getElementById('progressStatus');
    const progressPercent = document.getElementById('progressPercent');
    const progressBar = document.getElementById('progressBar');
    const progressSpeed = document.getElementById('progressSpeed');
    const progressEta = document.getElementById('progressEta');

    const completeSection = document.getElementById('completeSection');
    const fileDetailText = document.getElementById('fileDetailText');
    const downloadFileBtn = document.getElementById('downloadFileBtn');
    const newDownloadBtn = document.getElementById('newDownloadBtn');

    const inlinePlayerContainer = document.getElementById('inlinePlayerContainer');
    const inlineVideoPlayer = document.getElementById('inlineVideoPlayer');
    const inlineAudioPlayer = document.getElementById('inlineAudioPlayer');

    const historyList = document.getElementById('historyList');
    const refreshHistoryBtn = document.getElementById('refreshHistoryBtn');

    let currentUrl = '';
    let currentTaskId = null;
    let pollInterval = null;

    // Paste from Clipboard
    pasteBtn.addEventListener('click', async () => {
        try {
            const text = await navigator.clipboard.readText();
            if (text) {
                videoUrlInput.value = text.trim();
                triggerFetchInfo();
            }
        } catch (err) {
            console.log('Clipboard permission not granted', err);
            videoUrlInput.focus();
        }
    });

    // Quality card selection
    qualityCards.forEach(card => {
        card.addEventListener('click', () => {
            qualityCards.forEach(c => c.classList.remove('active'));
            card.classList.add('active');
            const radio = card.querySelector('input[type="radio"]');
            if (radio) radio.checked = true;
        });
    });

    // Form submit
    urlForm.addEventListener('submit', (e) => {
        e.preventDefault();
        triggerFetchInfo();
    });

    function showError(msg) {
        urlError.textContent = msg;
        urlError.classList.remove('hidden');
    }

    function hideError() {
        urlError.textContent = '';
        urlError.classList.add('hidden');
    }

    function setFetchLoading(loading) {
        const text = fetchBtn.querySelector('.btn-text');
        const spinner = fetchBtn.querySelector('.spinner');
        if (loading) {
            text.textContent = 'Mengecek...';
            spinner.classList.remove('hidden');
            fetchBtn.disabled = true;
        } else {
            text.textContent = 'Cek Video';
            spinner.classList.add('hidden');
            fetchBtn.disabled = false;
        }
    }

    async function triggerFetchInfo() {
        const url = videoUrlInput.value.trim();
        if (!url) {
            showError('Masukkan tautan video YouTube atau TikTok terlebih dahulu.');
            return;
        }

        hideError();
        setFetchLoading(true);
        previewCard.classList.add('hidden');
        progressCard.classList.add('hidden');
        completeSection.classList.add('hidden');

        try {
            const res = await fetch('/api/info', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url })
            });

            const data = await res.json();
            if (!res.ok || !data.success) {
                throw new Error(data.detail || data.error || 'Gagal mengambil informasi video.');
            }

            currentUrl = url;
            // Render preview info
            videoTitle.textContent = data.title;
            uploaderName.textContent = data.uploader;
            videoDuration.textContent = data.duration;
            extractorTag.textContent = data.extractor;
            thumbImg.src = data.thumbnail || 'https://via.placeholder.com/320x180?text=No+Thumbnail';

            // Dynamic original quality label
            const fullQualityTitle = document.getElementById('fullQualityTitle');
            const fullQualityBadge = document.getElementById('fullQualityBadge');
            const fullQualityDesc = document.getElementById('fullQualityDesc');
            if (data.max_resolution && fullQualityTitle) {
                fullQualityTitle.textContent = `Kualitas Asli (${data.max_resolution})`;
                if (data.max_height >= 2160) {
                    fullQualityBadge.textContent = '4K Ultra';
                } else if (data.max_height >= 1440) {
                    fullQualityBadge.textContent = '2K Quad';
                } else if (data.max_height >= 1080) {
                    fullQualityBadge.textContent = 'Full HD';
                } else {
                    fullQualityBadge.textContent = 'Original';
                }
                fullQualityDesc.textContent = `Resolusi original ${data.max_resolution} tanpa kompresi resolusi, visual tajam & kompatibel semua platform.`;
            }

            previewCard.classList.remove('hidden');
            previewCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

        } catch (err) {
            showError(err.message || 'Terjadi kesalahan saat memeriksa tautan.');
        } finally {
            setFetchLoading(false);
        }
    }

    // Start Download
    startDownloadBtn.addEventListener('click', async () => {
        if (!currentUrl) return;

        const selectedQuality = document.querySelector('input[name="quality"]:checked')?.value || 'medium';

        // UI Transition
        startDownloadBtn.disabled = true;
        const btnText = startDownloadBtn.querySelector('.btn-text');
        const btnSpinner = startDownloadBtn.querySelector('.spinner');
        btnText.textContent = 'Memulai proses...';
        btnSpinner.classList.remove('hidden');

        progressCard.classList.remove('hidden');
        completeSection.classList.add('hidden');
        inlinePlayerContainer.classList.add('hidden');
        inlineVideoPlayer.pause();
        inlineAudioPlayer.pause();
        inlineVideoPlayer.classList.add('hidden');
        inlineAudioPlayer.classList.add('hidden');

        updateProgressBar(5, 'Sedang mengirim permintaan ke server...');
        progressSpeed.textContent = 'Kecepatan: --';
        progressEta.textContent = 'Sisa Waktu: --';

        progressCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

        try {
            const res = await fetch('/api/download', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url: currentUrl, quality: selectedQuality })
            });

            const data = await res.json();
            if (!res.ok || !data.success) {
                throw new Error(data.detail || 'Gagal memulai unduhan.');
            }

            currentTaskId = data.task_id;
            startPollingStatus(currentTaskId);

        } catch (err) {
            updateProgressBar(0, `Gagal: ${err.message}`);
            startDownloadBtn.disabled = false;
            btnText.textContent = 'Mulai Mengunduh';
            btnSpinner.classList.add('hidden');
        }
    });

    function updateProgressBar(percent, statusText) {
        progressBar.style.width = `${percent}%`;
        progressPercent.textContent = `${Math.round(percent)}%`;
        if (statusText) progressStatus.textContent = statusText;
    }

    function startPollingStatus(taskId) {
        if (pollInterval) clearInterval(pollInterval);

        pollInterval = setInterval(async () => {
            try {
                const res = await fetch(`/api/status/${taskId}`);
                if (!res.ok) return;

                const task = await res.json();
                handleTaskUpdate(task);
            } catch (err) {
                console.error('Status poll error:', err);
            }
        }, 800);
    }

    function handleTaskUpdate(task) {
        const { status, progress, speed, eta, error, filename, file_size, download_url } = task;

        if (status === 'starting' || status === 'fetching_info') {
            updateProgressBar(15, 'Menganalisis link & metadata...');
        } else if (status === 'downloading') {
            updateProgressBar(Math.max(20, progress * 0.75), `Sedang mengunduh media (${Math.round(progress)}%)...`);
            progressSpeed.textContent = `Kecepatan: ${speed || '--'}`;
            progressEta.textContent = `Sisa Waktu: ${eta || '--'}`;
        } else if (status === 'processing') {
            updateProgressBar(85, 'Menggabungkan audio & video...');
            progressSpeed.textContent = 'Status: Processing';
            progressEta.textContent = 'Hampir selesai...';
        } else if (status === 'optimizing') {
            updateProgressBar(92, 'Optimasi format H.264 + FastStart (kompatibel semua platform)...');
            progressSpeed.textContent = 'Codec: Transcoding / Remuxing';
            progressEta.textContent = 'Sesaat lagi...';
        } else if (status === 'completed') {
            clearInterval(pollInterval);
            updateProgressBar(100, 'Unduhan & optimasi selesai 100%!');
            progressSpeed.textContent = `Ukuran File: ${file_size || '--'}`;
            progressEta.textContent = 'Selesai!';

            // Reset start button
            startDownloadBtn.disabled = false;
            startDownloadBtn.querySelector('.btn-text').textContent = 'Mulai Mengunduh';
            startDownloadBtn.querySelector('.spinner').classList.add('hidden');

            // Show Complete Section
            completeSection.classList.remove('hidden');
            fileDetailText.textContent = `${filename} (${file_size})`;
            downloadFileBtn.href = download_url;
            downloadFileBtn.setAttribute('download', filename);

            // Setup Inline Player
            inlinePlayerContainer.classList.remove('hidden');
            if (filename.toLowerCase().endsWith('.mp3')) {
                inlineAudioPlayer.src = download_url;
                inlineAudioPlayer.classList.remove('hidden');
                inlineVideoPlayer.classList.add('hidden');
            } else {
                inlineVideoPlayer.src = download_url;
                inlineVideoPlayer.classList.remove('hidden');
                inlineAudioPlayer.classList.add('hidden');
            }

            // Refresh history
            loadHistory();
        } else if (status === 'error') {
            clearInterval(pollInterval);
            updateProgressBar(0, `Error: ${error || 'Gagal mengunduh file'}`);
            startDownloadBtn.disabled = false;
            startDownloadBtn.querySelector('.btn-text').textContent = 'Mulai Mengunduh';
            startDownloadBtn.querySelector('.spinner').classList.add('hidden');
        }
    }

    // New Download Button
    newDownloadBtn.addEventListener('click', () => {
        videoUrlInput.value = '';
        currentUrl = '';
        previewCard.classList.add('hidden');
        progressCard.classList.add('hidden');
        completeSection.classList.add('hidden');
        inlineVideoPlayer.pause();
        inlineAudioPlayer.pause();
        inlinePlayerContainer.classList.add('hidden');
        videoUrlInput.focus();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });

    // History Management
    async function loadHistory() {
        try {
            const res = await fetch('/api/history');
            if (!res.ok) return;
            const data = await res.json();
            renderHistory(data.files || []);
        } catch (err) {
            console.error('Failed to load history:', err);
        }
    }

    function renderHistory(files) {
        if (!files.length) {
            historyList.innerHTML = '<div class="empty-history">Belum ada file yang diunduh.</div>';
            return;
        }

        historyList.innerHTML = files.map(file => `
            <div class="history-item">
                <div class="hi-left">
                    <span class="hi-badge ${file.ext}">${file.ext}</span>
                    <span class="hi-name" title="${file.name}">${file.name}</span>
                    <span class="hi-size">${file.size}</span>
                </div>
                <div class="hi-actions">
                    <a href="${file.download_url}" class="hi-btn download" download="${file.name}" title="Unduh File">
                        <svg class="svg-icon svg-xs" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                            <polyline points="7 10 12 15 17 10"/>
                            <line x1="12" x2="12" y1="15" y2="3"/>
                        </svg>
                        <span>Unduh</span>
                    </a>
                    <button class="hi-btn delete" data-filename="${file.name}" title="Hapus File">
                        <svg class="svg-icon svg-xs" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="pointer-events: none;">
                            <path d="M3 6h18"/>
                            <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/>
                            <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/>
                        </svg>
                    </button>
                </div>
            </div>
        `).join('');

        // Attach delete handlers
        document.querySelectorAll('.hi-btn.delete').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                const fname = e.target.dataset.filename;
                if (!fname) return;
                if (confirm(`Hapus file "${fname}" dari server?`)) {
                    await fetch(`/api/delete/${encodeURIComponent(fname)}`, { method: 'DELETE' });
                    loadHistory();
                }
            });
        });
    }

    refreshHistoryBtn.addEventListener('click', loadHistory);

    // Initial load
    loadHistory();
});
