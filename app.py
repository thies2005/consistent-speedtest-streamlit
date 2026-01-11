import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# Set page config
st.set_page_config(
    page_title="Consistent Speedtest",
    page_icon="🚀",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
.main { background-color: #0e1117; }
.stMetric { background: rgba(255, 255, 255, 0.05); padding: 15px; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

# Session State
if 'history' not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=['Timestamp', 'Ping (ms)', 'Jitter (ms)', 'Download (Mbps)', 'Upload (Mbps)'])

# Sidebar
st.sidebar.title("⚙️ Settings")
test_mode = st.sidebar.radio("Mode", ["Single Test", "Continuous"])
duration_min = 1
freq_sec = 10
if test_mode == "Continuous":
    duration_min = st.sidebar.slider("Duration (min)", 1, 60, 1)
    freq_sec = st.sidebar.slider("Frequency (sec)", 10, 120, 10)

def create_chart(df, column, color):
    fig = go.Figure()
    if not df.empty:
        fig.add_trace(go.Scatter(
            x=df['Timestamp'], y=df[column],
            mode='lines+markers',
            line=dict(color=color, width=3),
            marker=dict(size=8),
            fill='tozeroy',
            fillcolor=f'rgba{tuple(list(int(color.lstrip("#")[i:i+2], 16) for i in (0, 2, 4)) + [0.15])}'
        ))
    fig.update_layout(
        title=dict(text=column, font=dict(color='white', size=16)),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False, color='#666'),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', color='#666'),
        margin=dict(l=10, r=10, t=40, b=10),
        height=280
    )
    return fig

# Main UI
st.title("🚀 Device Speed Monitor")
st.caption("Measures your **browser/device** connection using Cloudflare.")

# Generate the HTML with dynamic continuous settings
is_continuous = "true" if test_mode == "Continuous" else "false"

speedtest_html = f"""
<div id="speedtest-container" style="padding: 20px; background: linear-gradient(135deg, #1a1a2e, #16213e); border-radius: 15px; margin-bottom: 20px;">
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
    <div id="results" style="display: none; margin-top: 30px;">
        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px;">
            <div style="background: rgba(0,191,255,0.1); padding: 20px; border-radius: 10px; text-align: center; border-left: 4px solid #00bfff;">
                <div style="color: #888; font-size: 12px;">PING</div>
                <div id="ping" style="color: #00bfff; font-size: 28px; font-weight: bold;">--</div>
                <div style="color: #666; font-size: 11px;">ms</div>
            </div>
            <div style="background: rgba(255,127,80,0.1); padding: 20px; border-radius: 10px; text-align: center; border-left: 4px solid #ff7f50;">
                <div style="color: #888; font-size: 12px;">JITTER</div>
                <div id="jitter" style="color: #ff7f50; font-size: 28px; font-weight: bold;">--</div>
                <div style="color: #666; font-size: 11px;">ms</div>
            </div>
            <div style="background: rgba(0,255,204,0.1); padding: 20px; border-radius: 10px; text-align: center; border-left: 4px solid #00ffcc;">
                <div style="color: #888; font-size: 12px;">DOWNLOAD</div>
                <div id="download" style="color: #00ffcc; font-size: 28px; font-weight: bold;">--</div>
                <div style="color: #666; font-size: 11px;">Mbps</div>
            </div>
            <div style="background: rgba(255,105,180,0.1); padding: 20px; border-radius: 10px; text-align: center; border-left: 4px solid #ff69b4;">
                <div style="color: #888; font-size: 12px;">UPLOAD</div>
                <div id="upload" style="color: #ff69b4; font-size: 28px; font-weight: bold;">--</div>
                <div style="color: #666; font-size: 11px;">Mbps</div>
            </div>
        </div>
    </div>
    <div id="historySection" style="margin-top: 20px;">
        <div style="color: #888; font-size: 14px; margin-bottom: 10px;">📊 Test History (<span id="testCount">0</span> tests)</div>
        <div id="historyList" style="max-height: 200px; overflow-y: auto; background: rgba(0,0,0,0.2); border-radius: 10px; padding: 10px;"></div>
    </div>
</div>

<script>
const CONTINUOUS = {is_continuous};
const DURATION_MS = {duration_min * 60 * 1000};
const FREQUENCY_MS = {freq_sec * 1000};

let isRunning = false;
let testInterval = null;
let startTime = null;
let testHistory = [];

async function runSingleTest() {{
    const status = document.getElementById('status');
    
    try {{
        // Ping test
        status.textContent = '🏓 Measuring latency...';
        const pings = [];
        for (let i = 0; i < 5; i++) {{
            const t0 = performance.now();
            await fetch('https://speed.cloudflare.com/__down?bytes=0', {{ cache: 'no-store' }});
            pings.push(performance.now() - t0);
        }}
        const ping = Math.min(...pings);
        const jitter = pings.slice(1).reduce((sum, v, i) => sum + Math.abs(v - pings[i]), 0) / (pings.length - 1);
        
        // Download test
        status.textContent = '⬇️ Testing download...';
        const dlStart = performance.now();
        const dlResp = await fetch('https://speed.cloudflare.com/__down?bytes=25000000', {{ cache: 'no-store' }});
        const dlBlob = await dlResp.blob();
        const dlTime = (performance.now() - dlStart) / 1000;
        const dlMbps = (dlBlob.size * 8 / 1_000_000) / dlTime;
        
        // Upload test
        status.textContent = '⬆️ Testing upload...';
        const ulData = new Uint8Array(5000000);
        const ulStart = performance.now();
        await fetch('https://speed.cloudflare.com/__up', {{ method: 'POST', body: ulData }});
        const ulTime = (performance.now() - ulStart) / 1000;
        const ulMbps = (ulData.length * 8 / 1_000_000) / ulTime;
        
        // Update display
        document.getElementById('ping').textContent = ping.toFixed(1);
        document.getElementById('jitter').textContent = jitter.toFixed(1);
        document.getElementById('download').textContent = dlMbps.toFixed(1);
        document.getElementById('upload').textContent = ulMbps.toFixed(1);
        document.getElementById('results').style.display = 'block';
        
        // Add to history
        const now = new Date().toLocaleTimeString();
        testHistory.push({{ time: now, ping: ping.toFixed(1), jitter: jitter.toFixed(1), dl: dlMbps.toFixed(1), ul: ulMbps.toFixed(1) }});
        updateHistoryDisplay();
        
        return true;
    }} catch(e) {{
        status.textContent = '❌ Error: ' + e.message;
        return false;
    }}
}}

function updateHistoryDisplay() {{
    const list = document.getElementById('historyList');
    const count = document.getElementById('testCount');
    count.textContent = testHistory.length;
    
    list.innerHTML = testHistory.slice().reverse().map((t, i) => `
        <div style="display: flex; justify-content: space-between; padding: 8px; background: rgba(255,255,255,0.05); border-radius: 5px; margin-bottom: 5px; font-size: 12px;">
            <span style="color: #888;">${{t.time}}</span>
            <span style="color: #00bfff;">📶 ${{t.ping}}ms</span>
            <span style="color: #00ffcc;">⬇️ ${{t.dl}} Mbps</span>
            <span style="color: #ff69b4;">⬆️ ${{t.ul}} Mbps</span>
        </div>
    `).join('');
}}

function updateProgress() {{
    if (!startTime) return;
    const elapsed = Date.now() - startTime;
    const progress = Math.min(100, (elapsed / DURATION_MS) * 100);
    document.getElementById('progressBar').style.width = progress + '%';
    
    const remaining = Math.max(0, Math.ceil((DURATION_MS - elapsed) / 1000));
    const mins = Math.floor(remaining / 60);
    const secs = remaining % 60;
    document.getElementById('progressText').textContent = `Time remaining: ${{mins}}m ${{secs}}s`;
}}

async function startTest() {{
    if (isRunning) return;
    isRunning = true;
    startTime = Date.now();
    
    document.getElementById('startBtn').style.display = 'none';
    document.getElementById('stopBtn').style.display = 'inline-block';
    document.getElementById('progressContainer').style.display = CONTINUOUS ? 'block' : 'none';
    
    // Run first test immediately
    await runSingleTest();
    document.getElementById('status').textContent = '✅ Test complete!';
    
    if (CONTINUOUS) {{
        document.getElementById('status').textContent = `🔄 Continuous mode: Next test in ${{FREQUENCY_MS/1000}}s...`;
        
        // Set up interval for continuous tests
        testInterval = setInterval(async () => {{
            if (!isRunning) return;
            
            // Check if duration exceeded
            if (Date.now() - startTime >= DURATION_MS) {{
                stopTest();
                document.getElementById('status').textContent = '✅ Continuous monitoring completed!';
                return;
            }}
            
            document.getElementById('status').textContent = '🔄 Running next test...';
            await runSingleTest();
            document.getElementById('status').textContent = `✅ Test complete! Next in ${{FREQUENCY_MS/1000}}s...`;
        }}, FREQUENCY_MS);
        
        // Update progress bar every second
        setInterval(updateProgress, 1000);
    }} else {{
        stopTest();
    }}
}}

function stopTest() {{
    isRunning = false;
    if (testInterval) {{
        clearInterval(testInterval);
        testInterval = null;
    }}
    document.getElementById('startBtn').style.display = 'inline-block';
    document.getElementById('stopBtn').style.display = 'none';
    document.getElementById('progressContainer').style.display = 'none';
    if (!CONTINUOUS) {{
        document.getElementById('status').textContent = '✅ Test complete!';
    }}
}}

// Load any previous history from localStorage
window.onload = function() {{
    const saved = localStorage.getItem('speedtest_history');
    if (saved) {{
        try {{
            testHistory = JSON.parse(saved);
            updateHistoryDisplay();
            if (testHistory.length > 0) {{
                const last = testHistory[testHistory.length - 1];
                document.getElementById('ping').textContent = last.ping;
                document.getElementById('jitter').textContent = last.jitter;
                document.getElementById('download').textContent = last.dl;
                document.getElementById('upload').textContent = last.ul;
                document.getElementById('results').style.display = 'block';
                document.getElementById('status').textContent = '📊 Showing last test results.';
            }}
        }} catch(e) {{}}
    }}
}};

// Save history when tests run
setInterval(() => {{
    if (testHistory.length > 0) {{
        localStorage.setItem('speedtest_history', JSON.stringify(testHistory.slice(-50)));
    }}
}}, 5000);
</script>
"""

# Render the speedtest component
st.components.v1.html(speedtest_html, height=550)

st.sidebar.divider()
if test_mode == "Continuous":
    st.sidebar.success(f"Will run tests every {freq_sec}s for {duration_min} min")
st.sidebar.caption("Tests run in your browser using Cloudflare endpoints.")
