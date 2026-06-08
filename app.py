# ============================================================
# 1. IMPORT LIBRARY
# ============================================================
from dotenv import load_dotenv
import os
import streamlit as st
import json
from datetime import datetime
from openai import OpenAI
MEMORY_FILE = "memory.json"

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
    /* Background */
    .stApp {
        background-color: var(--background-color);
    }

    /* Chat bubble user */
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

    /* Chat bubble AI */
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

    /* Dark mode */
    [data-theme="dark"] .user-bubble {
        background-color: #2b2b2b;
        color: #f0f0f0;
    }
    [data-theme="dark"] .ai-bubble {
        background-color: #1a3a4a;
        color: #f0f0f0;
    }

    /* Footer */
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
    "Asisten Umum": "Kamu adalah asisten AI yang membantu. Jawab dalam Bahasa Indonesia.",
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
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            st.session_state.history = json.load(f)
    except FileNotFoundError:        
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
        model = st.selectbox(
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
            "Aktifkan (Kalkulator & Jam)",
            value=st.session_state.use_tools,
            key="use_tools"
        )

        st.divider()
        if st.button("🔄 Reset Chat", use_container_width=True):
            st.session_state.history = [{"role": "system", "content": system_prompt}]
            if os.path.exists(MEMORY_FILE):
                os.remove(MEMORY_FILE)
            st.rerun()

    st.divider()
    with st.expander("📊 Usage", expanded=False):
        total_msg = len([m for m in st.session_state.history if m["role"] != "system"])
        st.metric("Total Pesan", total_msg)
        st.metric("Token Terpakai", st.session_state.total_tokens)
        st.metric("Estimasi Biaya", f"${st.session_state.total_cost:.4f}")

    st.divider()
    # ============================================================
    # UPLOAD FILE DIPINDAHKAN KE SIDEBAR
    # ============================================================
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
# 10. TOOLS: KALKULATOR & JAM
# ============================================================
def auto_save():
    """Simpan history ke file secara otomatis."""
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(st.session_state.history, f, indent=2, ensure_ascii=False)

def process_tools(user_input):
    user_lower = user_input.lower()
    if any(word in user_lower for word in ["hitung", "kalkulator", "berapa"]):
        try:
            expr = user_input.split(":")[-1] if ":" in user_input else user_input
            result = eval(expr)
            return f"🧮 Hasil: {result}"
        except:
            return None
    if any(word in user_lower for word in ["jam", "waktu", "sekarang", "tanggal", "hari ini"]):
        now = datetime.now()
        return f"🕐 Sekarang: {now.strftime('%A, %d %B %Y - %H:%M:%S WIB')}"
    return None

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
    # Setelah upload, reset widget dan rerun
    st.session_state.sidebar_file_uploader = None
    st.rerun()

# ============================================================
# 13. PROSES INPUT & KIRIM PESAN
# ============================================================
if user_input:
    st.markdown(f'<div class="user-bubble">{user_input}</div>', unsafe_allow_html=True)
    st.session_state.history.append({"role": "user", "content": user_input})
    auto_save()

    tool_result = None
    if st.session_state.use_tools:
        tool_result = process_tools(user_input)

    if tool_result:
        ai_reply = tool_result
        st.markdown(f'<div class="ai-bubble">{ai_reply}</div>', unsafe_allow_html=True)
        st.session_state.total_tokens += 0
    else:
        # --- STREAMING ---
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

            message_placeholder.markdown(full_response)
            ai_reply = full_response

    st.session_state.history.append({"role": "assistant", "content": ai_reply})
    auto_save()

# ============================================================
# 14. FOOTER
# ============================================================
st.markdown("""
<div class="footer">
    🚀 Dibuat oleh Brandon &copy; 2026 | Portfolio AI Engineer
</div>
""", unsafe_allow_html=True)