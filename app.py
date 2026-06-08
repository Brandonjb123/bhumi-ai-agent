# ============================================================
# 1. IMPORT LIBRARY
# ============================================================
from dotenv import load_dotenv
import os
import streamlit as st
import json
import requests
from datetime import datetime
from openai import OpenAI

# ============================================================
# 2. KONFIGURASI HALAMAN
# ============================================================
st.set_page_config(
    page_title="Bhumi AI Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# 3. CUSTOM CSS (HANYA CHAT BUBBLE & FOOTER)
# ============================================================
st.markdown("""
<style>
    .stApp {
        background-color: var(--background-color);
    }
    .user-bubble {
        background-color: #e9ecef;
        color: #000000;
        padding: 15px;
        border-radius: 15px;
        margin: 10px 0;
        text-align: right;
        max-width: 80%;
        float: right;
        clear: both;
    }
    .ai-bubble {
        background-color: #d1ecf1;
        color: #000000;
        padding: 15px;
        border-radius: 15px;
        margin: 10px 0;
        text-align: left;
        max-width: 80%;
        float: left;
        clear: both;
    }
    [data-theme="dark"] .user-bubble {
        background-color: #2b2b2b;
        color: #f0f0f0;
    }
    [data-theme="dark"] .ai-bubble {
        background-color: #1a3a4a;
        color: #f0f0f0;
    }
    .footer {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        background-color: #ffffff;
        text-align: center;
        padding: 10px;
        font-size: 0.85rem;
        color: #6c757d;
        border-top: 1px solid #dee2e6;
        z-index: 1000;
    }
    [data-theme="dark"] .footer {
        background-color: #1e1e1e;
        color: #aaaaaa;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# 4. API KEY & CLIENT
# ============================================================
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")

# ============================================================
# 5. SYSTEM PROMPTS
# ============================================================
system_prompts = {
    "Asisten Umum": """Kamu adalah asisten AI yang membantu. Kamu punya akses ke tools berikut:
- cuaca: untuk mengecek cuaca terkini di suatu kota.
- kalkulator: untuk menghitung ekspresi matematika.
- konversi_mata_uang: untuk mengonversi jumlah uang antar mata uang.

Jika pengguna meminta sesuatu yang memerlukan tools, JAWAB HANYA dengan format ini (tanpa teks lain):
TOOL: nama_tool | INPUT: parameter

Contoh:
User: "Cuaca di Jakarta bagaimana?"
Kamu: TOOL: cuaca | INPUT: Jakarta

User: "Hitung 15 * 23"
Kamu: TOOL: kalkulator | INPUT: 15*23

User: "Konversi 100 USD ke IDR"
Kamu: TOOL: konversi_mata_uang | INPUT: 100 USD IDR

Jika tidak perlu tools, jawab seperti biasa dengan Bahasa Indonesia yang ramah.""",
    "Guru Python": "Kamu adalah guru Python yang sabar. Jelaskan konsep programming dengan sederhana, beri contoh kode, dan dorong siswa untuk mencoba sendiri. Jangan kasih jawaban langsung — bimbing step by step.",
    "AI Trading Advisor": "Kamu adalah AI trading advisor profesional. Bantu analisis market, beri saran trading, dan jelaskan konsep keuangan dengan Bahasa Indonesia. Disclaimer: semua saran tidak menjamin keuntungan.",
    "AI Sarcastic": "Kamu adalah AI dengan selera humor satir yang tinggi. Jawab pertanyaan dengan sarkasme cerdas, sindiran halus, dan lelucon kering. Tetap gunakan Bahasa Indonesia, dan jangan terlalu kasar.",
    "AI Motivator": "Kamu adalah motivator profesional ala Tony Robbins. Setiap jawaban harus membakar semangat, memberikan dorongan positif, dan membuat orang merasa bisa menaklukkan dunia. Gunakan Bahasa Indonesia.",
    "Customer Service": "Kamu adalah customer service profesional untuk perusahaan teknologi. Gunakan bahasa sopan, empatik, dan solutif. Prioritaskan kepuasan pelanggan.",
    "Custom": "Kamu adalah asisten AI. Jawab dalam Bahasa Indonesia."
}

# Mapping model: label deskriptif -> nama teknis
model_mapping = {
    "⚡ Si Cepat & Serbaguna": "llama-3.3-70b-versatile",
    "⚡ Si Kilat & Ringan": "llama-3.1-8b-instant",
    "🧠 Si Multibahasa": "qwen/qwen3-32b"
}

# Mapping temperature: label -> nilai
temp_options = {
    "🎯 Presisi (0.2)": 0.2,
    "⚖️ Seimbang (0.7)": 0.7,
    "🎨 Kreatif (1.0)": 1.0
}

# ============================================================
# 6. INISIALISASI SESSION STATE
# ============================================================
if "history" not in st.session_state:
    st.session_state.history = [
        {"role": "system", "content": "Kamu adalah asisten AI yang membantu. Jawab dalam Bahasa Indonesia."}
    ]
if "total_tokens" not in st.session_state:
    st.session_state.total_tokens = 0
if "total_cost" not in st.session_state:
    st.session_state.total_cost = 0.0
if "model" not in st.session_state:
    st.session_state.model = "llama-3.3-70b-versatile"
if "temperature" not in st.session_state:
    st.session_state.temperature = 0.7
if "use_tools" not in st.session_state:
    st.session_state.use_tools = True
if "personality" not in st.session_state:
    st.session_state.personality = "Asisten Umum"
if "model_label" not in st.session_state:
    st.session_state.model_label = "⚡ Si Cepat & Serbaguna"
if "temp_label" not in st.session_state:
    st.session_state.temp_label = "⚖️ Seimbang (0.7)"

# ============================================================
# 7. SIDEBAR (MINIMALIS)
# ============================================================
with st.sidebar:
    st.title("🤖 Bhumi AI")

    with st.expander("⚙️ Settings", expanded=False):
        st.subheader("🎭 Personality")
        personality = st.selectbox(
            "Pilih kepribadian",
            list(system_prompts.keys()),
            key="personality"
        )
        if personality == "Custom":
            custom_prompt = st.text_area(
                "Tulis system prompt",
                value="Kamu adalah asisten AI. Jawab dalam Bahasa Indonesia.",
                height=100
            )
            system_prompt = custom_prompt
        else:
            system_prompt = system_prompts[personality]

        if st.session_state.history[0]["content"] != system_prompt:
            st.session_state.history[0] = {"role": "system", "content": system_prompt}

        st.divider()
        st.subheader("🧠 Model & Kreativitas")
        model_label = st.selectbox(
            "Model AI",
            list(model_mapping.keys()),
            key="model_label"
        )
        st.session_state.model = model_mapping[st.session_state.model_label]

        temp_label = st.radio(
            "🎨 Kreativitas",
            list(temp_options.keys()),
            key="temp_label"
        )
        st.session_state.temperature = temp_options[st.session_state.temp_label]

        st.divider()
        st.subheader("🔧 Tools")
        use_tools = st.checkbox(
            "Aktifkan tools (cuaca, kalkulator, konversi)",
            value=st.session_state.use_tools,
            key="use_tools"
        )

        st.divider()
        if st.button("🧹 New Chat", use_container_width=True):
            st.session_state.history = [{"role": "system", "content": system_prompt}]
            st.rerun()

    st.divider()
    with st.expander("📝 Riwayat Percakapan", expanded=False):
        chat_msgs = [m for m in st.session_state.history if m["role"] != "system"]
        for msg in chat_msgs[-10:]:
            if msg["role"] == "user":
                st.caption(f"👤 {msg['content'][:60]}...")
            elif msg["role"] == "assistant":
                st.caption(f"🤖 {msg['content'][:60]}...")

    st.divider()
    with st.expander("📎 Lampiran", expanded=False):
        uploaded_file = st.file_uploader(
            "Upload file",
            type=["txt", "py", "md", "jpg", "jpeg", "png"],
            label_visibility="collapsed",
            key="sidebar_file_uploader"
        )

# ============================================================
# 8. HEADER UTAMA
# ============================================================
st.title("🤖 Bhumi AI Agent")
st.caption(
    f"Personality: {st.session_state.personality} | "
    f"Model: {st.session_state.model_label} | "
    f"Tools: {'ON' if st.session_state.use_tools else 'OFF'} | "
    f"Kreativitas: {st.session_state.temp_label.split(' ')[0]}"
)

# ============================================================
# 9. TAMPILKAN HISTORY
# ============================================================
for msg in st.session_state.history:
    if msg["role"] == "user":
        st.markdown(f'<div class="user-bubble">{msg["content"]}</div>', unsafe_allow_html=True)
    elif msg["role"] == "assistant":
        st.markdown(f'<div class="ai-bubble">{msg["content"]}</div>', unsafe_allow_html=True)

# ============================================================
# 10. TOOLS: CUACA, KALKULATOR, KONVERSI MATA UANG
# ============================================================
def get_weather(location):
    try:
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={location}&count=1"
        geo_res = requests.get(geo_url).json()
        if not geo_res.get("results"):
            return f"❌ Kota '{location}' tidak ditemukan."
        lat = geo_res["results"][0]["latitude"]
        lon = geo_res["results"][0]["longitude"]
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        weather_res = requests.get(weather_url).json()
        current = weather_res["current_weather"]
        return f"🌤️ Cuaca di {location}: {current['temperature']}°C, angin {current['windspeed']} km/jam."
    except Exception as e:
        return f"❌ Gagal ambil cuaca: {e}"

def convert_currency(amount, from_curr, to_curr):
    rates = {
        "USD": 1.0, "EUR": 0.92, "IDR": 15700,
        "JPY": 149.5, "GBP": 0.79
    }
    if from_curr.upper() not in rates or to_curr.upper() not in rates:
        return f"❌ Mata uang tidak didukung. Supported: {list(rates.keys())}"
    usd_amount = amount / rates[from_curr.upper()]
    converted = usd_amount * rates[to_curr.upper()]
    return f"💱 {amount} {from_curr.upper()} = {converted:.2f} {to_curr.upper()}"

def calculator(expression):
    try:
        allowed = set("0123456789+-*/.() ")
        if not all(c in allowed for c in expression):
            return "❌ Ekspresi tidak valid."
        result = eval(expression)
        return f"🧮 {expression} = {result}"
    except Exception as e:
        return f"❌ Gagal menghitung: {e}"

# ============================================================
# 11. INPUT CHAT (STICKY OTOMATIS)
# ============================================================
user_input = st.chat_input("Ketik pesan lo...")

# ============================================================
# 12. PROSES FILE UPLOAD (JIKA ADA)
# ============================================================
if uploaded_file:
    if uploaded_file.type in ["image/jpeg", "image/png"]:
        st.image(uploaded_file, caption=f"📷 {uploaded_file.name}", width=300)
        st.session_state.history.append({
            "role": "user",
            "content": f"[Mengirim gambar: {uploaded_file.name}]"
        })
    else:
        try:
            file_text = uploaded_file.read().decode("utf-8")
            st.markdown(f'<div class="user-bubble">📎 Upload: {uploaded_file.name}</div>', unsafe_allow_html=True)
            st.session_state.history.append({
                "role": "user",
                "content": f"[Upload file: {uploaded_file.name}]\n\n{file_text[:2000]}"
            })
        except:
            st.warning("⚠️ File tidak bisa dibaca.")
    st.session_state.sidebar_file_uploader = None
    st.rerun()

# ============================================================
# 13. PROSES INPUT & KIRIM PESAN
# ============================================================
if user_input:
    st.markdown(f'<div class="user-bubble">{user_input}</div>', unsafe_allow_html=True)
    st.session_state.history.append({"role": "user", "content": user_input})

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

    with st.spinner("🤔 Berpikir..."):
        stream = client.chat.completions.create(
            model=st.session_state.model,
            messages=st.session_state.history,
            temperature=st.session_state.temperature,
            stream=True,
            stream_options={"include_usage": True}
        )

        for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            if delta and delta.content is not None:
                full_response += delta.content
                message_placeholder.markdown(full_response + "▌")
            if hasattr(chunk, "usage") and chunk.usage is not None:
                input_tokens = chunk.usage.prompt_tokens
                output_tokens = chunk.usage.completion_tokens
                st.session_state.total_tokens += (input_tokens + output_tokens)
                cost = (input_tokens * 0.00000059) + (output_tokens * 0.00000079)
                st.session_state.total_cost += cost

    # ==== CEK APAKAH AI MEMINTA TOOLS ====
    if full_response.startswith("TOOL:"):
        try:
            tool_part = full_response.replace("TOOL:", "").strip()
            tool_name = tool_part.split("|")[0].strip()
            tool_input = tool_part.split("INPUT:")[1].strip()

            if tool_name == "cuaca":
                tool_result = get_weather(tool_input)
            elif tool_name == "kalkulator":
                tool_result = calculator(tool_input)
            elif tool_name == "konversi_mata_uang":
                parts = tool_input.split()
                amount = float(parts[0])
                from_curr = parts[1]
                to_curr = parts[2]
                tool_result = convert_currency(amount, from_curr, to_curr)
            else:
                tool_result = f"❌ Tool '{tool_name}' tidak dikenal."

            ai_reply = tool_result

        except Exception as e:
            ai_reply = f"❌ Gagal menjalankan tools: {e}"
    else:
        ai_reply = full_response

    # Tampilkan jawaban akhir
    message_placeholder.markdown(ai_reply)
    st.session_state.history.append({"role": "assistant", "content": ai_reply})

# ============================================================
# 14. FOOTER
# ============================================================
st.markdown("""
<div class="footer">
    🚀 Dibuat oleh Brandon &copy; 2026 | Portfolio AI Engineer
</div>
""", unsafe_allow_html=True)