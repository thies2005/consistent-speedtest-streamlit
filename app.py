import streamlit as st

# Set page config
st.set_page_config(
    page_title="Speedtest",
    page_icon="🚀",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
.main { background-color: #0e1117; }
</style>
""", unsafe_allow_html=True)

# Sidebar
st.sidebar.title("⚙️ Settings")
test_mode = st.sidebar.radio("Mode", ["Single Test", "Continuous"])
duration_sec = 30
freq_sec = 5
if test_mode == "Continuous":
    duration_sec = st.sidebar.slider("Duration (sec)", 10, 300, 30, step=10)  # Min 10 seconds
    freq_sec = st.sidebar.slider("Frequency (sec)", 2, 60, 5)

# Main UI
st.title("🚀 Device Speed Monitor")
st.caption("Measures your **browser/device** connection using Cloudflare.")

# Generate the HTML with dynamic continuous settings
is_continuous = "true" if test_mode == "Continuous" else "false"

speedtest_html = f"""
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

<div id="speedtest-container" style="padding: 20px; background: linear-gradient(135deg, #1a1a2e, #16213e); border-radius: 15px; margin-bottom: 20px; font-family: -apple-system, BlinkMacSystemFont, sans-serif;">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 20px;">
        <button id="startBtn" onclick="startTest()" style="background: linear-gradient(135deg, #00ffcc, #00bfff); color: #000; border: none; padding: 15px 40px; border-radius: 10px; font-size: 18px; font-weight: bold; cursor: pointer;">
            ▶ Start Test
        </button>
        <button id="stopBtn" onclick="stopTest()" style="background: #ff4444; color: #fff; border: none; padding: 15px 40px; border-radius: 10px; font-size: 18px; font-weight: bold; cursor: pointer; display: none;">
            ⏹ Stop
        </button>
        <div id="status" style="color: #888; font-size: 14px;"></div>
    </div>
    <div id="progressContainer" style="display: none; margin-top: 15px;">
        <div style="background: rgba(255,255,255,0.1); border-radius: 10px; height: 8px; overflow: hidden;">
            <div id="progressBar" style="background: linear-gradient(90deg, #00ffcc, #00bfff); height: 100%; width: 0%; transition: width 0.5s;"></div>
        </div>
        <div id="progressText" style="color: #888; font-size: 12px; margin-top: 5px;"></div>
    </div>
    
    <!-- Results -->
    <div id="results" style="display: none; margin-top: 30px;">
        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px;">
            <div style="background: rgba(0,191,255,0.1); padding: 20px; border-radius: 10px; text-align: center; border-left: 4px solid #00bfff;">
                <div style="color: #888; font-size: 12px;">PING</div>
                <div id="ping" style="color: #00bfff; font-size: 28px; font-weight: bold;">--</div>
                <div style="color: #666; font-size: 11px;">ms</div>
                <div id="avgPing" style="color: #00bfff; font-size: 11px; margin-top: 5px; opacity: 0.8;">Avg: --</div>
            </div>
            <div style="background: rgba(255,127,80,0.1); padding: 20px; border-radius: 10px; text-align: center; border-left: 4px solid #ff7f50;">
                <div style="color: #888; font-size: 12px;">JITTER</div>
                <div id="jitter" style="color: #ff7f50; font-size: 28px; font-weight: bold;">--</div>
                <div style="color: #666; font-size: 11px;">ms</div>
                <div id="avgJitter" style="color: #ff7f50; font-size: 11px; margin-top: 5px; opacity: 0.8;">Avg: --</div>
            </div>
            <div style="background: rgba(0,255,204,0.1); padding: 20px; border-radius: 10px; text-align: center; border-left: 4px solid #00ffcc;">
                <div style="color: #888; font-size: 12px;">DOWNLOAD</div>
                <div id="download" style="color: #00ffcc; font-size: 28px; font-weight: bold;">--</div>
                <div style="color: #666; font-size: 11px;">Mbps</div>
                <div id="avgDownload" style="color: #00ffcc; font-size: 11px; margin-top: 5px; opacity: 0.8;">Avg: --</div>
            </div>
            <div style="background: rgba(255,105,180,0.1); padding: 20px; border-radius: 10px; text-align: center; border-left: 4px solid #ff69b4;">
                <div style="color: #888; font-size: 12px;">UPLOAD</div>
                <div id="upload" style="color: #ff69b4; font-size: 28px; font-weight: bold;">--</div>
                <div style="color: #666; font-size: 11px;">Mbps</div>
                <div id="avgUpload" style="color: #ff69b4; font-size: 11px; margin-top: 5px; opacity: 0.8;">Avg: --</div>
            </div>
        </div>
    </div>
    
    <!-- Graph Section (only shown after 2+ tests) -->
    <div id="chartSection" style="display: none; margin-top: 30px; background: rgba(0,0,0,0.3); border-radius: 15px; padding: 20px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; flex-wrap: wrap; gap: 10px;">
            <div style="color: #fff; font-size: 16px; font-weight: bold;">📈 Performance Graph</div>
            <div id="legendContainer" style="display: flex; gap: 10px; flex-wrap: wrap;"></div>
        </div>
        <div style="height: 250px;">
            <canvas id="performanceChart"></canvas>
        </div>
    </div>
    
    <!-- History Section -->
    <div id="historySection" style="margin-top: 20px;">
        <div style="color: #888; font-size: 14px; margin-bottom: 10px;">📊 Test History (<span id="testCount">0</span> tests)</div>
        <div id="historyList" style="background: rgba(0,0,0,0.2); border-radius: 10px; padding: 10px;"></div>
        <button id="clearBtn" onclick="clearHistory()" style="margin-top: 10px; background: rgba(255,255,255,0.1); color: #888; border: 1px solid rgba(255,255,255,0.2); padding: 8px 20px; border-radius: 8px; cursor: pointer; display: none;">🗑 Clear History</button>
    </div>
</div>

<script>
const CONTINUOUS = {is_continuous};
const DURATION_MS = {duration_sec * 1000};
const FREQUENCY_MS = {freq_sec * 1000};

let isRunning = false;
let testInterval = null;
let progressInterval = null;
let startTime = null;
let testHistory = [];
let chart = null;

const metricColors = {{
    ping: '#00bfff',
    jitter: '#ff7f50',
    download: '#00ffcc',
    upload: '#ff69b4'
}};

let visibleMetrics = {{ ping: true, jitter: true, download: true, upload: true }};

function initChart() {{
    if (chart) {{
        chart.destroy();
        chart = null;
    }}
    
    const ctx = document.getElementById('performanceChart').getContext('2d');
    chart = new Chart(ctx, {{
        type: 'line',
        data: {{
            labels: [],
            datasets: [
                {{ label: 'Ping (ms)', data: [], borderColor: metricColors.ping, backgroundColor: 'rgba(0,191,255,0.1)', fill: true, tension: 0.4, pointRadius: 4, hidden: !visibleMetrics.ping }},
                {{ label: 'Jitter (ms)', data: [], borderColor: metricColors.jitter, backgroundColor: 'rgba(255,127,80,0.1)', fill: true, tension: 0.4, pointRadius: 4, hidden: !visibleMetrics.jitter }},
                {{ label: 'Download (Mbps)', data: [], borderColor: metricColors.download, backgroundColor: 'rgba(0,255,204,0.1)', fill: true, tension: 0.4, pointRadius: 4, hidden: !visibleMetrics.download }},
                {{ label: 'Upload (Mbps)', data: [], borderColor: metricColors.upload, backgroundColor: 'rgba(255,105,180,0.1)', fill: true, tension: 0.4, pointRadius: 4, hidden: !visibleMetrics.upload }}
            ]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            animation: {{ duration: 300 }},
            interaction: {{ mode: 'index', intersect: false }},
            plugins: {{ legend: {{ display: false }} }},
            scales: {{
                x: {{ grid: {{ color: 'rgba(255,255,255,0.05)' }}, ticks: {{ color: '#666', maxRotation: 0 }} }},
                y: {{ grid: {{ color: 'rgba(255,255,255,0.05)' }}, ticks: {{ color: '#666' }}, beginAtZero: true }}
            }}
        }}
    }});
    updateLegend();
}}

function updateLegend() {{
    const container = document.getElementById('legendContainer');
    container.innerHTML = '';
    const metrics = ['ping', 'jitter', 'download', 'upload'];
    const labels = ['Ping', 'Jitter', 'Download', 'Upload'];
    
    metrics.forEach((metric, i) => {{
        const btn = document.createElement('button');
        const isActive = visibleMetrics[metric];
        btn.style.cssText = `
            background: ${{isActive ? metricColors[metric] : 'transparent'}};
            color: ${{isActive ? '#000' : metricColors[metric]}};
            border: 2px solid ${{metricColors[metric]}};
            padding: 4px 12px;
            border-radius: 15px;
            font-size: 11px;
            font-weight: bold;
            cursor: pointer;
        `;
        btn.textContent = labels[i];
        btn.onclick = () => {{
            visibleMetrics[metric] = !visibleMetrics[metric];
            if (chart) {{
                chart.data.datasets[i].hidden = !visibleMetrics[metric];
                chart.update();
            }}
            updateLegend();
        }};
        container.appendChild(btn);
    }});
}}

function updateChart() {{
    if (!chart || testHistory.length < 2) return;
    
    chart.data.labels = testHistory.map(t => t.time);
    chart.data.datasets[0].data = testHistory.map(t => parseFloat(t.ping));
    chart.data.datasets[1].data = testHistory.map(t => parseFloat(t.jitter));
    chart.data.datasets[2].data = testHistory.map(t => parseFloat(t.dl));
    chart.data.datasets[3].data = testHistory.map(t => parseFloat(t.ul));
    chart.update('none');
}}

// Helper function for fetch with timeout
async function fetchWithTimeout(url, options = {{}}, timeoutMs = 30000) {{
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
    try {{
        const response = await fetch(url, {{ ...options, signal: controller.signal }});
        clearTimeout(timeoutId);
        return response;
    }} catch (error) {{
        clearTimeout(timeoutId);
        throw error;
    }}
}}

async function runSingleTest() {{
    const status = document.getElementById('status');

    try {{
        status.textContent = '🏓 Measuring latency...';
        const pings = [];
        for (let i = 0; i < 5; i++) {{
            const t0 = performance.now();
            await fetchWithTimeout('https://speed.cloudflare.com/__down?bytes=0', {{ cache: 'no-store' }}, 10000);
            pings.push(performance.now() - t0);
        }}
        const ping = Math.min(...pings);
        const jitter = pings.slice(1).reduce((sum, v, i) => sum + Math.abs(v - pings[i]), 0) / (pings.length - 1);

        status.textContent = '⬇️ Testing download...';
        const dlStart = performance.now();
        const dlResp = await fetchWithTimeout('https://speed.cloudflare.com/__down?bytes=25000000', {{ cache: 'no-store' }}, 60000);
        const dlBlob = await dlResp.blob();
        const dlTime = (performance.now() - dlStart) / 1000;
        const dlMbps = (dlBlob.size * 8 / 1_000_000) / dlTime;

        status.textContent = '⬆️ Testing upload...';
        const ulData = new Uint8Array(5000000);
        const ulStart = performance.now();
        await fetchWithTimeout('https://speed.cloudflare.com/__up', {{ method: 'POST', body: ulData }}, 60000);
        const ulTime = (performance.now() - ulStart) / 1000;
        const ulMbps = (ulData.length * 8 / 1_000_000) / ulTime;
        
        document.getElementById('ping').textContent = ping.toFixed(1);
        document.getElementById('jitter').textContent = jitter.toFixed(1);
        document.getElementById('download').textContent = dlMbps.toFixed(1);
        document.getElementById('upload').textContent = ulMbps.toFixed(1);
        document.getElementById('results').style.display = 'block';
        
        const now = new Date().toLocaleTimeString();
        testHistory.push({{ time: now, ping: ping.toFixed(1), jitter: jitter.toFixed(1), dl: dlMbps.toFixed(1), ul: ulMbps.toFixed(1) }});
        
        updateHistoryDisplay();
        updateAverages();
        
        // Show graph only after 2+ tests
        if (testHistory.length >= 2) {{
            document.getElementById('chartSection').style.display = 'block';
            if (!chart) initChart();
            updateChart();
        }}
        
        return true;
    }} catch(e) {{
        if (e.name === 'AbortError') {{
            status.textContent = '❌ Request timed out. Check your connection.';
        }} else {{
            status.textContent = '❌ Error: ' + e.message;
        }}
        return false;
    }}
}}

function updateAverages() {{
    if (testHistory.length === 0) return;
    
    // Helper to extract number from test object, handling legacy keys
    const getVal = (t, keys) => {{
        for (const k of keys) {{
            if (t[k] !== undefined) return parseFloat(t[k]);
        }}
        return 0;
    }};
    
    const validTests = testHistory.filter(t => !isNaN(parseFloat(t.ping))); // Filter out completely broken records
    if (validTests.length === 0) return;

    const avg = (arr) => arr.reduce((a, b) => a + b, 0) / arr.length;
    
    const avgPing = avg(validTests.map(t => getVal(t, ['ping']))).toFixed(1);
    const avgJitter = avg(validTests.map(t => getVal(t, ['jitter']))).toFixed(1);
    const avgDl = avg(validTests.map(t => getVal(t, ['dl', 'download']))).toFixed(1);
    const avgUl = avg(validTests.map(t => getVal(t, ['ul', 'upload']))).toFixed(1);
    
    document.getElementById('avgPing').textContent = `Avg: ${{avgPing}}`;
    document.getElementById('avgJitter').textContent = `Avg: ${{avgJitter}}`;
    document.getElementById('avgDownload').textContent = `Avg: ${{avgDl}}`;
    document.getElementById('avgUpload').textContent = `Avg: ${{avgUl}}`;
}}

function updateHistoryDisplay() {{
    const list = document.getElementById('historyList');
    const count = document.getElementById('testCount');
    const clearBtn = document.getElementById('clearBtn');
    
    count.textContent = testHistory.length;
    clearBtn.style.display = testHistory.length > 0 ? 'inline-block' : 'none';
    
    list.innerHTML = testHistory.slice().reverse().map(t => `
        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr 1fr 1fr; gap: 10px; padding: 10px; background: rgba(255,255,255,0.03); border-radius: 8px; margin-bottom: 6px; font-size: 12px;">
            <span style="color: #888;">${{t.time}}</span>
            <span style="color: #00bfff;">📶 ${{t.ping}}ms</span>
            <span style="color: #ff7f50;">📊 ${{t.jitter}}ms</span>
            <span style="color: #00ffcc;">⬇️ ${{t.dl}} Mbps</span>
            <span style="color: #ff69b4;">⬆️ ${{t.ul}} Mbps</span>
        </div>
    `).join('');
}}

function clearHistory() {{
    testHistory = [];
    localStorage.removeItem('speedtest_history');
    updateHistoryDisplay();
    document.getElementById('results').style.display = 'none';
    document.getElementById('chartSection').style.display = 'none';
    if (chart) {{
        chart.destroy();
        chart = null;
    }}
}}

function updateProgress() {{
    if (!startTime) return;
    const elapsed = Date.now() - startTime;
    const progress = Math.min(100, (elapsed / DURATION_MS) * 100);
    document.getElementById('progressBar').style.width = progress + '%';
    
    const remaining = Math.max(0, Math.ceil((DURATION_MS - elapsed) / 1000));
    document.getElementById('progressText').textContent = `Time remaining: ${{remaining}}s`;
}}

async function startTest() {{
    if (isRunning) return;
    isRunning = true;
    startTime = Date.now();
    
    document.getElementById('startBtn').style.display = 'none';
    document.getElementById('stopBtn').style.display = 'inline-block';
    document.getElementById('progressContainer').style.display = CONTINUOUS ? 'block' : 'none';
    
    await runSingleTest();
    document.getElementById('status').textContent = '✅ Test complete!';
    
    if (CONTINUOUS) {{
        document.getElementById('status').textContent = `🔄 Next test in ${{FREQUENCY_MS/1000}}s...`;
        
        testInterval = setInterval(async () => {{
            if (!isRunning) return;
            
            if (Date.now() - startTime >= DURATION_MS) {{
                stopTest();
                document.getElementById('status').textContent = '✅ Monitoring completed!';
                return;
            }}
            
            await runSingleTest();
            document.getElementById('status').textContent = `✅ Done! Next in ${{FREQUENCY_MS/1000}}s...`;
        }}, FREQUENCY_MS);
        
        progressInterval = setInterval(updateProgress, 500);
    }} else {{
        stopTest();
    }}
}}

function stopTest() {{
    isRunning = false;
    if (testInterval) {{ clearInterval(testInterval); testInterval = null; }}
    if (progressInterval) {{ clearInterval(progressInterval); progressInterval = null; }}
    document.getElementById('startBtn').style.display = 'inline-block';
    document.getElementById('stopBtn').style.display = 'none';
    document.getElementById('progressContainer').style.display = 'none';
}}

window.onload = function() {{
    const saved = localStorage.getItem('speedtest_history');
    if (saved) {{
        try {{
            testHistory = JSON.parse(saved);
            if (testHistory.length > 0) {{
                updateHistoryDisplay();
                updateAverages();
                const last = testHistory[testHistory.length - 1];
                document.getElementById('ping').textContent = last.ping;
                document.getElementById('jitter').textContent = last.jitter;
                document.getElementById('download').textContent = last.dl;
                document.getElementById('upload').textContent = last.ul;
                document.getElementById('results').style.display = 'block';
                
                if (testHistory.length >= 2) {{
                    document.getElementById('chartSection').style.display = 'block';
                    initChart();
                    updateChart();
                }}
            }}
        }} catch(e) {{}}
    }}
}};

setInterval(() => {{
    if (testHistory.length > 0) {{
        try {{
            localStorage.setItem('speedtest_history', JSON.stringify(testHistory.slice(-100)));
        }} catch(e) {{
            // localStorage unavailable (private browsing) or quota exceeded
            console.warn('Could not save to localStorage:', e.message);
        }}
    }}
}}, 3000);
</script>
"""

st.components.v1.html(speedtest_html, height=850)

st.sidebar.divider()
if test_mode == "Continuous":
    st.sidebar.success(f"Tests every {freq_sec}s for {duration_sec}s")
st.sidebar.caption("Runs in your browser via Cloudflare.")
