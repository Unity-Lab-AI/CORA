// C.O.R.A web - Stats Server (localhost:11435) - Real GPU/CPU/RAM from host
// Classic script, loaded in order by index.html (shared global scope). Split from index.html on 2026-10-14.

// ============================================================
// Stats Server (localhost:11435) - Real GPU/CPU/RAM from host
// ============================================================

const STATS_URL = STATS_BASE;
let statsServerAvailable = false;

async function fetchSystemStats() {
    try {
        const res = await fetch(`${STATS_URL}/stats`, { method: 'GET' });
        if (res.ok) {
            const stats = await res.json();
            statsServerAvailable = true;
            updateStatsDisplay(stats);
            return stats;
        }
    } catch (e) {
        statsServerAvailable = false;
    }
    return null;
}

function updateStatsDisplay(stats) {
    if (!stats) return;

    // CPU
    document.getElementById('statCpu').textContent = `${Math.round(stats.cpu.percent)}%`;
    document.getElementById('statCpu').className = 'stat-value';

    // Memory
    document.getElementById('statMem').textContent = `${Math.round(stats.memory.percent)}%`;
    document.getElementById('statMem').className = 'stat-value';

    // Disk
    document.getElementById('statDisk').textContent = `${Math.round(stats.disk.percent)}%`;
    document.getElementById('statDisk').className = 'stat-value';

    // GPU
    if (stats.gpu && stats.gpu.available) {
        document.getElementById('statGpu').textContent = `${stats.gpu.utilization}%`;
        document.getElementById('statGpu').className = 'stat-value';
        // VRAM
        const vramPercent = Math.round((stats.gpu.memory_used / stats.gpu.memory_total) * 100);
        document.getElementById('statVram').textContent = `${vramPercent}%`;
        document.getElementById('statVram').className = 'stat-value';
    } else {
        document.getElementById('statGpu').textContent = 'N/A';
        document.getElementById('statGpu').className = 'stat-value na';
        document.getElementById('statVram').textContent = 'N/A';
        document.getElementById('statVram').className = 'stat-value na';
    }

    // Network
    document.getElementById('statNet').textContent = 'Online';
    document.getElementById('statNet').className = 'stat-value';
}

// Start polling stats every second
let statsInterval = null;
function startStatsPolling() {
    if (statsInterval) return;
    statsInterval = setInterval(fetchSystemStats, 1000);
    fetchSystemStats(); // Initial fetch
}

function stopStatsPolling() {
    if (statsInterval) {
        clearInterval(statsInterval);
        statsInterval = null;
    }
}
