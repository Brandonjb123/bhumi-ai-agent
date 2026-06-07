# ============================================================
# 1. IMPORT LIBRARY
# ============================================================
import streamlit as st
import json
from datetime import datetime
from openai import OpenAI
import os
from dotenv import load_dotenv

# ============================================================
# 2. KONFIGURASI HALAMAN (Favicon, Judul, Layout)
# ============================================================
st.set_page_config(
    page_title="Bhumi AI Agent",
    page_icon="🤖",                # emoji sebagai favicon
    layout="wide",                 # pakai lebar penuh
    initial_sidebar_state="expanded"
)

# ============================================================
# 3. CUSTOM CSS SEDERHANA (Background halus, chat bubble)
# ============================================================
st.markdown("""
<style>
    /* Background halus abu-abu muda */
    .stApp {
        background-color: #f8f9fa;
    }
    
    /* Chat bubble untuk user (rata kanan, abu-abu) */
    .user-bubble {
        background-color: #e9ecef;
        padding: 15px;
        border-radius: 15px;
        margin: 10px 0;
        text-align: right;
        max-width: 80%;
        float: right;
        clear: both;
    }
    
    /* Chat bubble untuk AI (rata kiri, biru muda) */
    .ai-bubble {
        background-color: #d1ecf1;
        padding: 15px;
        border-radius: 15px;
        margin: 10px 0;
        text-align: left;
        max-width: 80%;
        float: left;
        clear: both;
    }
    
    /* Footer styling */
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
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# 4. API KEY & CLIENT
# ============================================================
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")   # Ganti dengan API key lo
client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")

# ============================================================
# 5. INISIALISASI HISTORY
# ============================================================
if "history" not in st.session_state:
    st.session_state.history = [
        {"role": "system", "content": "Kamu adalah asisten AI yang membantu. Jawab dalam Bahasa Indonesia."}
    ]

# ============================================================
# 6. SIDEBAR (DENGAN EXPANDER)
# ============================================================
with st.sidebar:
    st.title("🤖 Bhumi AI Agent")
    st.caption("v5.0 — Your Personal Assistant")

    # --- Personality ---
    with st.expander("🎭 Personality", expanded=False):
        personality = st.selectbox(
            "Pilih kepribadian",
            ["Asisten Umum", "AI Trading Advisor", "Guru Python", "Customer Service", "Custom"],
            label_visibility="collapsed"
        )

        system_prompts = {
            "Asisten Umum": "Kamu adalah asisten AI yang membantu. Jawab dalam Bahasa Indonesia.",
            "AI Trading Advisor": "Kamu adalah AI trading advisor profesional. Bantu analisis market, beri saran trading, dan jelaskan konsep keuangan dengan Bahasa Indonesia. Disclaimer: semua saran tidak menjamin keuntungan.",
            "Guru Python": "Kamu adalah guru Python yang sabar. Jelaskan konsep programming dengan sederhana, beri contoh kode, dan dorong siswa untuk mencoba sendiri. Jangan kasih jawaban langsung — bimbing step by step.",
            "Customer Service": "Kamu adalah customer service profesional untuk perusahaan teknologi. Gunakan bahasa sopan, empatik, dan solutif. Prioritaskan kepuasan pelanggan.",
            "Custom": "Kamu adalah asisten AI. Jawab dalam Bahasa Indonesia."
        }

        if personality == "Custom":
            custom_prompt = st.text_area(
                "Tulis system prompt lo sendiri",
                value="Kamu adalah asisten AI. Jawab dalam Bahasa Indonesia.",
                height=100
            )
            system_prompt = custom_prompt
        else:
            system_prompt = system_prompts[personality]

        if st.session_state.history[0]["content"] != system_prompt:
            st.session_state.history[0] = {"role": "system", "content": system_prompt}

    # --- Tools ---
    with st.expander("🔧 Tools", expanded=False):
        use_tools = st.checkbox("Aktifkan Tools (Kalkulator + Jam)", value=True)

    # --- Model & Temperature ---
    with st.expander("🧠 Model & Kreativitas", expanded=False):
        model = st.selectbox(
            "Model AI",
            ["llama-3.3-70b-versatile", "gemma2-9b-it", "deepseek-r1-distill-llama-70b"],
            label_visibility="collapsed"
        )
        temperature = st.slider("Temperature", 0.0, 1.0, 0.7, 0.1)

    # --- Upload File ---
    with st.expander("📎 Upload File", expanded=False):
        uploaded_file = st.file_uploader("Pilih file", type=["txt", "py", "js", "html", "css", "md"], label_visibility="collapsed")

    st.divider()

    # --- Kontrol Chat ---
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Reset", use_container_width=True):
            st.session_state.history = [{"role": "system", "content": system_prompt}]
            st.rerun()
    with col2:
        if st.button("💾 Simpan", use_container_width=True):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"chat_history_{timestamp}.json"
            with open(filename, "w") as f:
                json.dump(st.session_state.history, f, indent=2, ensure_ascii=False)
            st.success(f"✅ {filename}")

    st.divider()

    # --- Info Sesi ---
    total_msg = len([m for m in st.session_state.history if m["role"] != "system"])
    st.metric("Total Pesan", total_msg)
    st.caption(f"🧠 {model}")
    st.caption(f"🎨 Temperature: {temperature:.1f}")

# ============================================================
# 7. HEADER HALAMAN UTAMA
# ============================================================
st.title("🤖 Bhumi AI Agent")
st.caption(f"Personality: {personality} | Model: {model} | Tools: {'ON' if use_tools else 'OFF'}")

# ============================================================
# 8. TAMPILKAN HISTORY DENGAN CHAT BUBBLE KUSTOM
# ============================================================
for msg in st.session_state.history:
    if msg["role"] == "user":
        st.markdown(f'<div class="user-bubble">{msg["content"]}</div>', unsafe_allow_html=True)
    elif msg["role"] == "assistant":
        st.markdown(f'<div class="ai-bubble">{msg["content"]}</div>', unsafe_allow_html=True)

# ============================================================
# 9. TOOLS: KALKULATOR & JAM
# ============================================================
def process_tools(user_input):
    user_lower = user_input.lower()

    if any(word in user_lower for word in ["hitung", "kalkulator", "berapa", "+", "-", "*", "/"]):
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
# 10. PROSES FILE UPLOAD
# ============================================================
if uploaded_file:
    file_content = uploaded_file.read()
    try:
        file_text = file_content.decode("utf-8")
        st.markdown(f'<div class="user-bubble">📎 Upload: {uploaded_file.name}</div>', unsafe_allow_html=True)
        st.session_state.history.append({
            "role": "user",
            "content": f"[Upload file: {uploaded_file.name}]\n\n{file_text[:2000]}"
        })
        st.rerun()
    except:
        st.warning("⚠️ File tidak bisa dibaca.")

# ============================================================
# 11. INPUT USER & RESPONS AI
# ============================================================
user_input = st.chat_input("Ketik pesan lo...")

if user_input:
    # Tampilkan input user
    st.markdown(f'<div class="user-bubble">{user_input}</div>', unsafe_allow_html=True)
    st.session_state.history.append({"role": "user", "content": user_input})

    # Cek tools lokal
    tool_result = None
    if use_tools:
        tool_result = process_tools(user_input)

    if tool_result:
        ai_reply = tool_result
    else: 
        # Tampilkan placeholder untuk teks yang akan diketik
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""

        # Streaming response
        with st.spinner("🤔 Berpikir..."):
            response = client.chat.completions.create(
                model=model,
                messages=st.session_state.history,
                temperature=temperature,
                stream=True     #<--- AKTIFKAN STREAMING
            )

            # Terima potongan-potongan teks
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    full_response += chunk.choices[0].delta.content
                    # Update teks di placeholder
                    message_placeholder.markdown(full_response + "▌")

        # Setelah selesai, tampilkan teks final tanpa kursor
        message_placeholder.markdown(full_response)            
        ai_reply = full_response

    st.session_state.history.append({"role": "assistant", "content": ai_reply})
    st.markdown(f'<div class="ai-bubble">{ai_reply}</div>', unsafe_allow_html=True)
    st.rerun()

# ============================================================
# 12. FOOTER
# ============================================================
st.markdown("""
<div class="footer">
    🚀 Dibuat oleh Brandon &copy; 2025 | Portfolio AI Engineer
</div>
""", unsafe_allow_html=True)