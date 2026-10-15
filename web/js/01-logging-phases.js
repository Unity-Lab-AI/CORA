// C.O.R.A web - Logging & Phases
// Classic script, loaded in order by index.html (shared global scope). Split from index.html on 2026-10-14.

// ============================================================
// Logging & Phases
// ============================================================

// Store log history for console window sync
const logHistory = [];
let consoleWindow = null;

// Function to send logs to console window
function sendToConsole(data) {
    // Save to localStorage (works for file://)
    localStorage.setItem('cora_log_history', JSON.stringify(logHistory));
    localStorage.setItem('cora_console_log', JSON.stringify(data));

    // Also try postMessage if console window exists
    if (consoleWindow && !consoleWindow.closed) {
        try {
            consoleWindow.postMessage(data, '*');
        } catch (e) {}
    }
}

// Listen for messages from console window
window.addEventListener('message', (e) => {
    if (e.data.type === 'ping') {
        e.source.postMessage({ type: 'pong' }, '*');
    } else if (e.data.type === 'requestHistory') {
        e.source.postMessage({ type: 'history', logs: logHistory }, '*');
    }
});

function log(text, type = 'info') {
    const container = document.getElementById('logContainer');
    const timestamp = new Date().toLocaleTimeString('en-US', { hour12: false });
    const line = document.createElement('div');
    line.className = `log-line log-${type}`;

    let fullText;
    if (type === 'phase') {
        line.style.marginTop = '10px';
        fullText = `[${timestamp}] ═══════════════ ${text} ═══════════════`;
    } else {
        const prefix = type === 'ok' ? '✓' : type === 'warn' ? '⚠' : type === 'fail' ? '✗' : '';
        fullText = `[${timestamp}] ${prefix ? prefix + ' ' : ''}${text}`;
    }
    line.textContent = fullText;

    container.appendChild(line);
    container.scrollTop = container.scrollHeight;

    // Store in history and send to console window
    logHistory.push({ text: fullText, logType: type });
    sendToConsole({ type: 'log', text: fullText, logType: type });

    // Also pipe to setup terminal (backend console) for split view
    const setupColor = type === 'ok' ? '#00ff00' : type === 'warn' ? '#ffaa00' : type === 'fail' ? '#ff4444' : type === 'phase' ? '#ff00ff' : '#cccccc';
    setupLog(`[BOOT] ${text}`, setupColor);
}

function renderPhases() {
    const container = document.getElementById('phasesSection');
    container.innerHTML = '';
    PHASES.forEach(phase => {
        const item = document.createElement('div');
        item.className = 'phase-item';
        let indicator = '○';
        if (phase.status === 'running') indicator = '◐';
        else if (['ok', 'warn', 'fail'].includes(phase.status)) indicator = '●';
        item.innerHTML = `<span class="phase-indicator ${phase.status}">${indicator}</span><span>${phase.name}</span>`;
        container.appendChild(item);
    });
}

function setPhase(id, status) {
    const phase = PHASES.find(p => p.id === id);
    if (phase) { phase.status = status; renderPhases(); }
}

function updateProgress(percent, text) {
    document.getElementById('progressFill').style.width = percent + '%';
    document.getElementById('progressText').textContent = text;
}

// ============================================================
// Window Manager - Windows 11 style windows with drag/resize/z-level
// Matches desktop window_manager.py behavior
// ============================================================

let windowZIndex = 2000;  // Track z-index for layering
const openWindows = {};   // Track open windows

function createDynamicModal(title, width = 800, height = 600) {
    const windowId = 'window_' + Date.now();

    // Transparent overlay (no grey background - windows float freely)
    const overlay = document.createElement('div');
    overlay.id = windowId + '_overlay';
    overlay.style.cssText = `
        position: fixed; top: 0; left: 0; right: 0; bottom: 0;
        background: transparent; z-index: ${windowZIndex - 1};
        pointer-events: none;
    `;

    // The window itself - positioned absolutely, not centered in flex
    const modal = document.createElement('div');
    modal.id = windowId;
    modal.className = 'cora-window';
    modal.style.cssText = `
        position: fixed;
        left: ${Math.max(50, (window.innerWidth - width) / 2)}px;
        top: ${Math.max(50, (window.innerHeight - height) / 2)}px;
        width: ${width}px;
        height: ${height}px;
        min-width: 300px;
        min-height: 200px;
        background: #1a1a2e;
        border: 2px solid #ff00ff;
        border-radius: 8px;
        box-shadow: 0 10px 40px rgba(255,0,255,0.3);
        display: flex;
        flex-direction: column;
        z-index: ${windowZIndex};
        overflow: hidden;
    `;

    // Title bar (draggable)
    const header = document.createElement('div');
    header.className = 'window-titlebar';
    header.style.cssText = `
        background: linear-gradient(135deg, #2d0040 0%, #1a0020 100%);
        padding: 8px 10px;
        border-bottom: 1px solid #ff00ff;
        display: flex;
        justify-content: space-between;
        align-items: center;
        cursor: move;
        user-select: none;
    `;

    const titleSpan = document.createElement('span');
    titleSpan.style.cssText = 'color: #ff00ff; font-weight: bold; font-size: 13px;';
    titleSpan.textContent = title;

    // Window control buttons (minimize, maximize, close)
    const controls = document.createElement('div');
    controls.style.cssText = 'display: flex; gap: 5px;';

    const minBtn = document.createElement('button');
    minBtn.innerHTML = '─';
    minBtn.title = 'Minimize';
    minBtn.style.cssText = `
        background: #444; border: none; color: white; width: 28px; height: 24px;
        border-radius: 3px; cursor: pointer; font-size: 12px;
    `;
    minBtn.onmouseover = () => minBtn.style.background = '#666';
    minBtn.onmouseout = () => minBtn.style.background = '#444';
    minBtn.onclick = (e) => { e.stopPropagation(); minimizeWindow(modal); };

    const maxBtn = document.createElement('button');
    maxBtn.innerHTML = '☐';
    maxBtn.title = 'Maximize';
    maxBtn.style.cssText = `
        background: #444; border: none; color: white; width: 28px; height: 24px;
        border-radius: 3px; cursor: pointer; font-size: 12px;
    `;
    maxBtn.onmouseover = () => maxBtn.style.background = '#666';
    maxBtn.onmouseout = () => maxBtn.style.background = '#444';
    maxBtn.onclick = (e) => { e.stopPropagation(); toggleMaximize(modal, maxBtn); };

    const closeBtn = document.createElement('button');
    closeBtn.innerHTML = '✕';
    closeBtn.title = 'Close';
    closeBtn.style.cssText = `
        background: #c42b1c; border: none; color: white; width: 28px; height: 24px;
        border-radius: 3px; cursor: pointer; font-size: 12px;
    `;
    closeBtn.onmouseover = () => closeBtn.style.background = '#e81123';
    closeBtn.onmouseout = () => closeBtn.style.background = '#c42b1c';
    closeBtn.onclick = (e) => { e.stopPropagation(); closeWindow(windowId); };

    controls.appendChild(minBtn);
    controls.appendChild(maxBtn);
    controls.appendChild(closeBtn);

    header.appendChild(titleSpan);
    header.appendChild(controls);

    // Content area
    const content = document.createElement('div');
    content.style.cssText = 'flex: 1; overflow: auto; padding: 15px;';

    // Resize handles (8 directions)
    const resizeHandles = createResizeHandles(modal);

    modal.appendChild(header);
    modal.appendChild(content);
    resizeHandles.forEach(h => modal.appendChild(h));

    document.body.appendChild(overlay);
    document.body.appendChild(modal);

    // Enable dragging
    enableDrag(modal, header);

    // Click to bring to front
    modal.addEventListener('mousedown', () => bringToFront(modal));

    // Store window state
    openWindows[windowId] = {
        modal, overlay, isMaximized: false, isMinimized: false,
        prevState: { left: modal.style.left, top: modal.style.top, width: modal.style.width, height: modal.style.height }
    };

    windowZIndex += 2;

    return { overlay, modal, content, close: () => closeWindow(windowId) };
}

function createResizeHandles(modal) {
    const handles = [];
    const positions = [
        { cursor: 'nw-resize', top: '-5px', left: '-5px', width: '15px', height: '15px' },
        { cursor: 'n-resize', top: '-5px', left: '10px', right: '10px', height: '10px' },
        { cursor: 'ne-resize', top: '-5px', right: '-5px', width: '15px', height: '15px' },
        { cursor: 'e-resize', top: '10px', right: '-5px', bottom: '10px', width: '10px' },
        { cursor: 'se-resize', bottom: '-5px', right: '-5px', width: '15px', height: '15px' },
        { cursor: 's-resize', bottom: '-5px', left: '10px', right: '10px', height: '10px' },
        { cursor: 'sw-resize', bottom: '-5px', left: '-5px', width: '15px', height: '15px' },
        { cursor: 'w-resize', top: '10px', left: '-5px', bottom: '10px', width: '10px' }
    ];

    positions.forEach(pos => {
        const handle = document.createElement('div');
        handle.style.cssText = `position: absolute; cursor: ${pos.cursor}; z-index: 10;`;
        if (pos.top) handle.style.top = pos.top;
        if (pos.bottom) handle.style.bottom = pos.bottom;
        if (pos.left) handle.style.left = pos.left;
        if (pos.right) handle.style.right = pos.right;
        if (pos.width) handle.style.width = pos.width;
        if (pos.height) handle.style.height = pos.height;

        enableResize(modal, handle, pos.cursor);
        handles.push(handle);
    });

    return handles;
}

function enableDrag(modal, handle) {
    let isDragging = false, startX, startY, startLeft, startTop;

    handle.addEventListener('mousedown', (e) => {
        if (e.target.tagName === 'BUTTON') return;
        const win = openWindows[modal.id];
        if (win && win.isMaximized) return;

        isDragging = true;
        startX = e.clientX;
        startY = e.clientY;
        startLeft = parseInt(modal.style.left);
        startTop = parseInt(modal.style.top);
        bringToFront(modal);
    });

    document.addEventListener('mousemove', (e) => {
        if (!isDragging) return;
        const dx = e.clientX - startX;
        const dy = e.clientY - startY;
        modal.style.left = Math.max(0, startLeft + dx) + 'px';
        modal.style.top = Math.max(0, startTop + dy) + 'px';
    });

    document.addEventListener('mouseup', () => isDragging = false);
}

function enableResize(modal, handle, cursor) {
    let isResizing = false, startX, startY, startW, startH, startL, startT;

    handle.addEventListener('mousedown', (e) => {
        const win = openWindows[modal.id];
        if (win && win.isMaximized) return;

        isResizing = true;
        startX = e.clientX;
        startY = e.clientY;
        startW = parseInt(modal.style.width);
        startH = parseInt(modal.style.height);
        startL = parseInt(modal.style.left);
        startT = parseInt(modal.style.top);
        e.preventDefault();
        bringToFront(modal);
    });

    document.addEventListener('mousemove', (e) => {
        if (!isResizing) return;
        const dx = e.clientX - startX;
        const dy = e.clientY - startY;
        const minW = 300, minH = 200;

        if (cursor.includes('e')) modal.style.width = Math.max(minW, startW + dx) + 'px';
        if (cursor.includes('s')) modal.style.height = Math.max(minH, startH + dy) + 'px';
        if (cursor.includes('w')) {
            const newW = Math.max(minW, startW - dx);
            modal.style.width = newW + 'px';
            modal.style.left = (startL + startW - newW) + 'px';
        }
        if (cursor.includes('n')) {
            const newH = Math.max(minH, startH - dy);
            modal.style.height = newH + 'px';
            modal.style.top = (startT + startH - newH) + 'px';
        }
    });

    document.addEventListener('mouseup', () => isResizing = false);
}

function bringToFront(modal) {
    windowZIndex += 2;
    modal.style.zIndex = windowZIndex;
    const win = openWindows[modal.id];
    if (win) win.overlay.style.zIndex = windowZIndex - 1;
}

function minimizeWindow(modal) {
    const win = openWindows[modal.id];
    if (!win) return;
    win.isMinimized = !win.isMinimized;
    modal.style.display = win.isMinimized ? 'none' : 'flex';
    win.overlay.style.display = win.isMinimized ? 'none' : 'block';
}

function toggleMaximize(modal, btn) {
    const win = openWindows[modal.id];
    if (!win) return;

    if (win.isMaximized) {
        // Restore
        modal.style.left = win.prevState.left;
        modal.style.top = win.prevState.top;
        modal.style.width = win.prevState.width;
        modal.style.height = win.prevState.height;
        modal.style.borderRadius = '8px';
        btn.innerHTML = '☐';
        win.isMaximized = false;
    } else {
        // Save state and maximize
        win.prevState = {
            left: modal.style.left, top: modal.style.top,
            width: modal.style.width, height: modal.style.height
        };
        modal.style.left = '0';
        modal.style.top = '0';
        modal.style.width = '100vw';
        modal.style.height = '100vh';
        modal.style.borderRadius = '0';
        btn.innerHTML = '❐';
        win.isMaximized = true;
    }
}

function closeWindow(windowId) {
    const win = openWindows[windowId];
    if (win) {
        win.modal.remove();
        win.overlay.remove();
        delete openWindows[windowId];
    }
}

function showCodeModal(code, filename, language = 'python') {
    const { content, close } = createDynamicModal(`CORA - Code Import: ${filename}`, 900, 600);
    content.innerHTML = `
        <div style="color: #00ff88; margin-bottom: 10px; font-size: 12px;">
            Source: GitHub API | File: ${filename}
        </div>
        <pre style="background: #0d0d1a; padding: 15px; border-radius: 4px;
            overflow: auto; max-height: 450px; color: #e0e0e0; font-size: 12px;
            white-space: pre-wrap; word-wrap: break-word;">${escapeHtml(code)}</pre>
    `;
    return { close };
}

function showImageModal(imageUrl, title) {
    const { content, close } = createDynamicModal(title, 1000, 700);
    content.style.padding = '0';
    content.innerHTML = `
        <img src="${imageUrl}" style="width: 100%; height: 100%; object-fit: contain; background: black;">
    `;
    return { close };
}

function showVideoModal(videoId, title) {
    const { content, close } = createDynamicModal(title, 800, 500);
    content.style.padding = '0';
    content.innerHTML = `
        <iframe width="100%" height="100%" src="https://www.youtube.com/embed/${videoId}?autoplay=1"
            frameborder="0" allow="autoplay; encrypted-media" allowfullscreen></iframe>
    `;
    return { close };
}

function showQuoteModal(quote) {
    const { content, close } = createDynamicModal('CORA - Modal Test', 500, 300);
    content.innerHTML = `
        <div style="text-align: center; padding: 20px;">
            <div style="color: #00ff88; font-size: 16px; margin-bottom: 20px;">Modal Window Test</div>
            <div style="color: #ffffff; font-style: italic; font-size: 14px; margin-bottom: 20px;">"${quote}"</div>
            <div style="color: #888; font-size: 12px;">
                Modal Types Available:<br>
                - Message popups<br>
                - Code viewer<br>
                - Image viewer<br>
                - Video player
            </div>
        </div>
    `;
    return { close };
}
