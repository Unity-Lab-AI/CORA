// C.O.R.A web - Permission Prompt Modal - Pauses boot and notifies user
// Classic script, loaded in order by index.html (shared global scope). Split from index.html on 2026-10-14.

// ============================================================
// Permission Prompt Modal - Pauses boot and notifies user
// ============================================================

function showPermissionPrompt(title, description, icon) {
    return new Promise((resolve) => {
        const { content, close } = createDynamicModal(`CORA - ${title}`, 500, 320);
        content.innerHTML = `
            <div style="text-align: center; padding: 25px;">
                <div style="font-size: 50px; margin-bottom: 15px;">${icon}</div>
                <div style="color: #ff00ff; font-size: 18px; font-weight: bold; margin-bottom: 12px;">${title}</div>
                <div style="color: #ffffff; font-size: 14px; margin-bottom: 25px; line-height: 1.5;">${description}</div>
                <div style="display: flex; gap: 12px; justify-content: center; align-items: center; flex-wrap: wrap;">
                    <button id="permissionGrantBtn" style="
                        background: linear-gradient(135deg, #00cc66, #009944);
                        border: none; padding: 14px 35px; border-radius: 6px;
                        color: white; font-size: 15px; font-weight: bold;
                        cursor: pointer; text-transform: uppercase;
                    ">Grant Permission</button>
                    <button id="permissionDenyBtn" style="
                        background: linear-gradient(135deg, #cc3333, #992222);
                        border: none; padding: 14px 35px; border-radius: 6px;
                        color: white; font-size: 15px; font-weight: bold;
                        cursor: pointer; text-transform: uppercase;
                    ">Deny</button>
                    <button id="permissionSkipBtn" style="
                        background: #333; border: 1px solid #555;
                        padding: 10px 25px; border-radius: 4px;
                        color: #aaa; font-size: 12px; cursor: pointer;
                    ">Skip</button>
                </div>
            </div>
        `;

        document.getElementById('permissionGrantBtn').onclick = () => {
            close();
            resolve('granted');
        };
        document.getElementById('permissionDenyBtn').onclick = () => {
            close();
            resolve('denied');
        };
        document.getElementById('permissionSkipBtn').onclick = () => {
            close();
            resolve('skip');
        };
    });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
