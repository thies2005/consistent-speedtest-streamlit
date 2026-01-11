import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import time
from datetime import datetime
from streamlit_js_eval import streamlit_js_eval

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
.metric-card {
    background: linear-gradient(135deg, rgba(0,191,255,0.1), rgba(0,255,204,0.1));
    border-radius: 15px;
    padding: 20px;
    border: 1px solid rgba(255,255,255,0.1);
    text-align: center;
}
.metric-value { font-size: 2.5rem; font-weight: bold; color: #00ffcc; }
.metric-label { color: #888; font-size: 0.9rem; }
</style>
""", unsafe_allow_html=True)

# Session State
if 'history' not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=['Timestamp', 'Ping (ms)', 'Jitter (ms)', 'Download (Mbps)', 'Upload (Mbps)'])
if 'is_running' not in st.session_state:
    st.session_state.is_running = False
if 'run_start' not in st.session_state:
    st.session_state.run_start = None

# Sidebar
st.sidebar.title("⚙️ Settings")
test_mode = st.sidebar.radio("Mode", ["Single Test", "Continuous"])
duration_min = 5
freq_sec = 30
if test_mode == "Continuous":
    duration_min = st.sidebar.slider("Duration (min)", 1, 60, 5)
    freq_sec = st.sidebar.slider("Frequency (sec)", 10, 120, 30)

# JavaScript for speed test (simplified, synchronous-friendly)
JS_SPEEDTEST = """
(async () => {
    try {
        // Ping test (5 samples)
        const pings = [];
        for (let i = 0; i < 5; i++) {
            const t0 = performance.now();
            await fetch('https://www.google.com/favicon.ico?_=' + Date.now(), {mode: 'no-cors', cache: 'no-store'});
            pings.push(performance.now() - t0);
        }
        const ping = Math.min(...pings);
        const jitter = pings.slice(1).reduce((sum, v, i) => sum + Math.abs(v - pings[i]), 0) / (pings.length - 1);

        // Download test (fetch ~2MB)
        const dlStart = performance.now();
        const dlResp = await fetch('https://www.google.com/images/branding/googlelogo/2x/googlelogo_color_272x92dp.png?_=' + Date.now(), {cache: 'no-store'});
        const dlBlob = await dlResp.blob();
        const dlTime = (performance.now() - dlStart) / 1000;
        const dlMbps = (dlBlob.size * 8 / 1_000_000) / dlTime;

        // Upload test (simulated with POST timing)
        const ulData = new Uint8Array(100000); // 100KB
        const ulStart = performance.now();
        await fetch('https://httpbin.org/post', {method: 'POST', body: ulData, mode: 'no-cors'});
        const ulTime = (performance.now() - ulStart) / 1000;
        const ulMbps = (ulData.length * 8 / 1_000_000) / ulTime;

        return JSON.stringify({
            ping: ping.toFixed(2),
            jitter: jitter.toFixed(2),
            download: dlMbps.toFixed(2),
            upload: ulMbps.toFixed(2)
        });
    } catch(e) {
        return JSON.stringify({error: e.message});
    }
})();
"""

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
st.caption("Measures your **browser/device** connection, not the server.")

# Control buttons
col_start, col_stop = st.columns(2)
with col_start:
    start_btn = st.button("▶ Start Test", use_container_width=True, disabled=st.session_state.is_running)
with col_stop:
    stop_btn = st.button("⏹ Stop", use_container_width=True, disabled=not st.session_state.is_running)

if start_btn:
    st.session_state.is_running = True
    st.session_state.run_start = datetime.now()
    st.rerun()

if stop_btn:
    st.session_state.is_running = False
    st.rerun()

# Run test
if st.session_state.is_running:
    # Check timeout for continuous mode
    if test_mode == "Continuous" and st.session_state.run_start:
        elapsed = (datetime.now() - st.session_state.run_start).total_seconds() / 60
        if elapsed >= duration_min:
            st.session_state.is_running = False
            st.success(f"✅ Monitoring completed after {duration_min} minutes.")
            st.rerun()

    # Execute JS and get result
    status = st.empty()
    status.info("⏳ Running speed test on your device...")
    
    result_str = streamlit_js_eval(js_expressions=JS_SPEEDTEST, key=f"speedtest_{time.time()}")
    
    if result_str:
        import json
        try:
            result = json.loads(result_str)
            if 'error' in result:
                st.error(f"Test failed: {result['error']}")
            else:
                new_row = {
                    'Timestamp': datetime.now().strftime("%H:%M:%S"),
                    'Ping (ms)': float(result['ping']),
                    'Jitter (ms)': float(result['jitter']),
                    'Download (Mbps)': float(result['download']),
                    'Upload (Mbps)': float(result['upload'])
                }
                st.session_state.history = pd.concat([st.session_state.history, pd.DataFrame([new_row])], ignore_index=True)
                status.success("✅ Test complete!")
                
                if test_mode == "Single Test":
                    st.session_state.is_running = False
                else:
                    time.sleep(freq_sec)
                st.rerun()
        except json.JSONDecodeError:
            st.warning("Waiting for test results...")
            time.sleep(2)
            st.rerun()
    else:
        time.sleep(2)
        st.rerun()

# Display Results
if not st.session_state.history.empty:
    latest = st.session_state.history.iloc[-1]
    
    st.divider()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("🏓 Ping", f"{latest['Ping (ms)']} ms")
    m2.metric("📊 Jitter", f"{latest['Jitter (ms)']} ms")
    m3.metric("⬇️ Download", f"{latest['Download (Mbps)']} Mbps")
    m4.metric("⬆️ Upload", f"{latest['Upload (Mbps)']} Mbps")
    
    st.divider()
    
    c1, c2 = st.columns(2)
    c3, c4 = st.columns(2)
    with c1: st.plotly_chart(create_chart(st.session_state.history, 'Ping (ms)', '#00BFFF'), use_container_width=True)
    with c2: st.plotly_chart(create_chart(st.session_state.history, 'Jitter (ms)', '#FF7F50'), use_container_width=True)
    with c3: st.plotly_chart(create_chart(st.session_state.history, 'Download (Mbps)', '#00FFCC'), use_container_width=True)
    with c4: st.plotly_chart(create_chart(st.session_state.history, 'Upload (Mbps)', '#FF69B4'), use_container_width=True)
    
    with st.expander("📋 Raw Data"):
        st.dataframe(st.session_state.history.sort_index(ascending=False), use_container_width=True)
        if st.button("🗑 Clear History"):
            st.session_state.history = pd.DataFrame(columns=['Timestamp', 'Ping (ms)', 'Jitter (ms)', 'Download (Mbps)', 'Upload (Mbps)'])
            st.rerun()
else:
    st.markdown("### 👆 Press **Start Test** to begin")

st.sidebar.divider()
st.sidebar.caption("Tests run in your browser to measure your device's actual connection speed.")
