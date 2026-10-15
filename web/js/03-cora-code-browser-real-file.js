// C.O.R.A web - CORA Code Browser - Real file/directory viewer with copy
// Classic script, loaded in order by index.html (shared global scope). Split from index.html on 2026-10-14.

// ============================================================
// CORA Code Browser - Real file/directory viewer with copy
// ============================================================

let codeBrowserCache = {};  // Cache fetched directory listings

function showCodeBrowserModal() {
    const { overlay, modal, content, close } = createDynamicModal('CORA - Code Browser', 1100, 700);

    // Custom layout for file browser
    content.innerHTML = `
        <div style="display: flex; height: 100%; gap: 10px;">
            <!-- Left: Directory Tree -->
            <div id="fileTree" style="
                width: 280px; background: #0d0d1a; border-radius: 4px;
                overflow-y: auto; padding: 10px; font-size: 12px;
            ">
                <div style="color: #ff00ff; font-weight: bold; margin-bottom: 10px; border-bottom: 1px solid #333; padding-bottom: 8px;">
                    📁 CORA Project Files
                </div>
                <div id="treeContent" style="color: #ccc;">Loading...</div>
            </div>
            <!-- Right: Code Viewer -->
            <div style="flex: 1; display: flex; flex-direction: column;">
                <!-- File Header -->
                <div id="fileHeader" style="
                    background: #1a1a2a; padding: 10px 15px; border-radius: 4px 4px 0 0;
                    display: flex; justify-content: space-between; align-items: center;
                ">
                    <div>
                        <span id="currentFileName" style="color: #00ffff; font-weight: bold;">Select a file</span>
                        <span id="fileInfo" style="color: #666; font-size: 11px; margin-left: 15px;"></span>
                    </div>
                    <div>
                        <button id="copyCodeBtn" style="
                            background: #ff00ff; border: none; padding: 6px 15px;
                            border-radius: 4px; color: white; font-size: 11px;
                            cursor: pointer; display: none;
                        " onclick="copyCurrentCode()">📋 COPY</button>
                    </div>
                </div>
                <!-- Code Content -->
                <pre id="codeViewer" style="
                    flex: 1; margin: 0; padding: 15px; background: #0a0a0f;
                    overflow: auto; font-size: 12px; line-height: 1.5;
                    color: #e0e0e0; border-radius: 0 0 4px 4px;
                    font-family: 'Consolas', monospace; white-space: pre-wrap;
                ">Click a file on the left to view its contents</pre>
            </div>
        </div>
    `;

    // Store current code for copy function
    window.currentCodeContent = '';

    // Load CORA's directory structure
    loadCoraDirectoryTree();

    return { close };
}

async function loadCoraDirectoryTree() {
    const treeContent = document.getElementById('treeContent');

    try {
        // Fetch CORA repo root
        const resp = await fetch('https://api.github.com/repos/Unity-Lab-AI/CORA/contents/');
        if (!resp.ok) throw new Error('API rate limited or repo not found');

        const items = await resp.json();
        codeBrowserCache['/'] = items;

        // Render tree
        treeContent.innerHTML = '';
        renderDirectoryItems(items, treeContent, '/');

    } catch (e) {
        treeContent.innerHTML = `
            <div style="color: #ff4444;">Failed to load: ${e.message}</div>
            <div style="color: #666; margin-top: 10px; font-size: 11px;">
                GitHub API might be rate-limited.<br>
                Try again in a minute.
            </div>
        `;
    }
}

function renderDirectoryItems(items, container, parentPath) {
    // Sort: directories first, then files
    const sorted = [...items].sort((a, b) => {
        if (a.type === 'dir' && b.type !== 'dir') return -1;
        if (a.type !== 'dir' && b.type === 'dir') return 1;
        return a.name.localeCompare(b.name);
    });

    sorted.forEach(item => {
        const div = document.createElement('div');
        div.style.cssText = 'padding: 4px 8px; cursor: pointer; border-radius: 3px;';
        div.onmouseover = () => div.style.background = '#1a1a2a';
        div.onmouseout = () => div.style.background = 'transparent';

        const icon = item.type === 'dir' ? '📁' : getFileIcon(item.name);
        const color = item.type === 'dir' ? '#ffaa00' : '#ccc';

        div.innerHTML = `<span style="color: ${color};">${icon} ${item.name}</span>`;

        if (item.type === 'dir') {
            // Directory - expandable
            const subContainer = document.createElement('div');
            subContainer.style.cssText = 'margin-left: 15px; display: none;';

            div.onclick = async (e) => {
                e.stopPropagation();
                if (subContainer.style.display === 'none') {
                    // Expand
                    subContainer.style.display = 'block';
                    div.innerHTML = `<span style="color: ${color};">📂 ${item.name}</span>`;

                    // Load contents if not cached
                    const path = parentPath + item.name + '/';
                    if (!codeBrowserCache[path]) {
                        subContainer.innerHTML = '<div style="color: #666; padding: 5px;">Loading...</div>';
                        try {
                            const resp = await fetch(item.url);
                            if (resp.ok) {
                                const subItems = await resp.json();
                                codeBrowserCache[path] = subItems;
                                subContainer.innerHTML = '';
                                renderDirectoryItems(subItems, subContainer, path);
                            }
                        } catch (e) {
                            subContainer.innerHTML = `<div style="color: #ff4444; padding: 5px;">Error loading</div>`;
                        }
                    }
                } else {
                    // Collapse
                    subContainer.style.display = 'none';
                    div.innerHTML = `<span style="color: ${color};">📁 ${item.name}</span>`;
                }
            };

            container.appendChild(div);
            container.appendChild(subContainer);
        } else {
            // File - load content on click
            div.onclick = () => loadFileContent(item);
            container.appendChild(div);
        }
    });
}

function getFileIcon(filename) {
    const ext = filename.split('.').pop().toLowerCase();
    const icons = {
        'py': '🐍', 'js': '📜', 'ts': '📘', 'html': '🌐',
        'css': '🎨', 'json': '📋', 'md': '📝', 'txt': '📄',
        'bat': '⚙️', 'sh': '🔧', 'yml': '⚙️', 'yaml': '⚙️',
        'png': '🖼️', 'jpg': '🖼️', 'gif': '🖼️', 'svg': '🖼️'
    };
    return icons[ext] || '📄';
}

async function loadFileContent(item) {
    const viewer = document.getElementById('codeViewer');
    const fileName = document.getElementById('currentFileName');
    const fileInfo = document.getElementById('fileInfo');
    const copyBtn = document.getElementById('copyCodeBtn');

    fileName.textContent = item.name;
    viewer.textContent = 'Loading...';
    copyBtn.style.display = 'none';

    try {
        const resp = await fetch(item.download_url);
        if (!resp.ok) throw new Error('Failed to fetch');

        const content = await resp.text();
        const lines = content.split('\n').length;
        const sizeKb = (item.size / 1024).toFixed(1);

        fileInfo.textContent = `${lines} lines | ${sizeKb} KB`;
        viewer.innerHTML = highlightCode(content, item.name);

        // Store for copy
        window.currentCodeContent = content;
        copyBtn.style.display = 'inline-block';

    } catch (e) {
        viewer.textContent = `Error loading file: ${e.message}`;
    }
}

function highlightCode(code, filename) {
    // Simple syntax highlighting
    const ext = filename.split('.').pop().toLowerCase();
    let escaped = escapeHtml(code);

    if (['py', 'js', 'ts'].includes(ext)) {
        // Keywords
        const keywords = ['def', 'class', 'import', 'from', 'return', 'if', 'else', 'elif',
            'for', 'while', 'try', 'except', 'finally', 'with', 'as', 'async', 'await',
            'function', 'const', 'let', 'var', 'export', 'async', 'true', 'false', 'None', 'True', 'False'];
        keywords.forEach(kw => {
            escaped = escaped.replace(new RegExp(`\\b${kw}\\b`, 'g'),
                `<span style="color: #ff79c6;">${kw}</span>`);
        });

        // Strings (simple - single and double quotes)
        escaped = escaped.replace(/(["'])(?:(?=(\\?))\2.)*?\1/g,
            '<span style="color: #f1fa8c;">$&</span>');

        // Comments
        escaped = escaped.replace(/(#.*)$/gm,
            '<span style="color: #6272a4;">$1</span>');
        escaped = escaped.replace(/(\/\/.*)$/gm,
            '<span style="color: #6272a4;">$1</span>');
    }

    return escaped;
}

function copyCurrentCode() {
    if (!window.currentCodeContent) return;

    navigator.clipboard.writeText(window.currentCodeContent).then(() => {
        const btn = document.getElementById('copyCodeBtn');
        const originalText = btn.textContent;
        btn.textContent = '✅ COPIED!';
        btn.style.background = '#00ff88';
        setTimeout(() => {
            btn.textContent = originalText;
            btn.style.background = '#ff00ff';
        }, 2000);
    }).catch(err => {
        console.error('Copy failed:', err);
        alert('Copy failed - browser might have blocked clipboard access');
    });
}
