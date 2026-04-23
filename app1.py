import json
import streamlit as st
from openai import OpenAI
import streamlit.components.v1 as components

# ================== 1. CẤU HÌNH TRANG & GIAO DIỆN ==================
st.set_page_config(page_title="LSA Translator | Groq", page_icon="⚡", layout="centered")

# Nhúng Font Awesome và CSS tùy chỉnh
st.markdown("""
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    .groq-title-container { text-align: center; margin-bottom: 30px; padding-bottom: 20px; border-bottom: 1px solid #333; }
    .groq-title {
        font-size: 2.8rem; font-weight: 900;
        background: linear-gradient(90deg, #f55036, #ff8c00);
        -webkit-background-clip: text; -webkit-fill-color: transparent;
        margin-bottom: 5px; letter-spacing: -1px;
    }
    .groq-subtitle { color: #888; font-size: 1.1rem; font-weight: 400; }
    
    /* Nút Submit chính */
    div[data-testid="stFormSubmitButton"] > button {
        background: linear-gradient(90deg, #f55036, #e03a20) !important;
        color: white !important; border: none !important; border-radius: 8px !important;
        font-weight: bold !important; font-size: 16px !important; transition: all 0.3s ease !important;
        height: 45px;
    }
    div[data-testid="stFormSubmitButton"] > button:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(245, 80, 54, 0.5) !important; }

    /* Nút Clear (Thùng rác) */
    button[kind="secondary"] {
        border-radius: 8px !important;
        border: 1px solid rgba(250, 250, 250, 0.2) !important;
        transition: all 0.2s ease !important;
    }
    button[kind="secondary"]:hover {
        border-color: #f55036 !important;
        color: #f55036 !important;
    }

    /* Khung kết quả */
    .result-box {
        background: rgba(30, 30, 30, 0.6); backdrop-filter: blur(10px); color: #f0f0f0;
        padding: 18px 20px; border-radius: 12px; border-left: 4px solid #f55036;
        border-top: 1px solid #333; border-right: 1px solid #333; border-bottom: 1px solid #333;
        font-size: 16px; line-height: 1.5; white-space: pre-wrap; min-height: 100px; margin-top: 10px;
    }
    .result-header { font-size: 18px; font-weight: bold; color: #f55036; display: flex; align-items: center; gap: 8px; margin-top: 10px;}
    
    footer {visibility: hidden;}
    .stTextArea textarea { font-size: 15.5px !important; border-radius: 8px; }
    </style>
""", unsafe_allow_html=True)

# Hàm Render nút Copy bằng Font Awesome
def render_custom_copy_button(text_to_copy):
    js_text = json.dumps(text_to_copy)
    html_code = f"""
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        body {{ margin: 0; background: transparent; overflow: hidden; }}
        .st-copy-btn {{
            background-color: #262730; border: 1px solid rgba(250, 250, 250, 0.2);
            color: white; border-radius: 8px; width: 100%; height: 40px;
            display: flex; align-items: center; justify-content: center;
            cursor: pointer; transition: all 0.2s; font-size: 18px;
        }}
        .st-copy-btn:hover {{ border-color: #f55036; color: #f55036; }}
        .success {{ color: #00cc00 !important; border-color: #00cc00 !important; }}
    </style>
    <button class="st-copy-btn" id="copyBtn" onclick='copy()'><i class="fa-solid fa-copy"></i></button>
    <script>
    function copy() {{
        navigator.clipboard.writeText({js_text}).then(function() {{
            var btn = document.getElementById('copyBtn');
            btn.innerHTML = '<i class="fa-solid fa-check"></i>';
            btn.classList.add('success');
            setTimeout(function() {{ 
                btn.innerHTML = '<i class="fa-solid fa-copy"></i>'; 
                btn.classList.remove('success');
            }}, 2000);
        }});
    }}
    </script>
    """
    components.html(html_code, height=45)

# ================== 2. CẤU HÌNH API GROQ ==================
API_KEY = st.secrets["API_KEY"]
client = OpenAI(api_key=API_KEY, base_url="https://api.groq.com/openai/v1")
MODEL_NAME = "llama-3.3-70b-versatile" 

# ================== 3. TỪ ĐIỂN CHUYÊN NGÀNH ==================
DICT_JP_VI = {
    "レタッチ": "Retouch",
    "加筆する": "Vẽ bù / Vẽ thêm",
    "写植": "Lettering (Shashoku)",
    "ゴミ取り": "Làm sạch (Gomitori)",
    "非表示レイヤー": "Layer ẩn",
    "フォルダ": "Folder",
    "インペイント": "Inpainting",
    "パツパツ": "Quá tải"
}
dict_prompt_str = "\n".join([f"- {k} -> {v}" for k, v in DICT_JP_VI.items()])

# ================== 4. QUẢN LÝ TRẠNG THÁI ==================
if "is_jp_to_vi" not in st.session_state:
    st.session_state.is_jp_to_vi = True
if "main_input" not in st.session_state:
    st.session_state["main_input"] = ""

def clear_text():
    st.session_state["main_input"] = ""

# ================== 5. CẤU HÌNH NGÔN NGỮ UI ==================
UI_TEXT = {
    "vi_to_jp": {
        "title": "LSA TRANSLATOR", "subtitle": "Powered by Groq Engine ⚡",
        "placeholder": "Nhập nội dung cần dịch...", "button": "⚡ Dịch Tốc Độ Cao",
        "result_title": "BẢN DỊCH TIẾNG NHẬT", "lang_left": "Tiếng Việt 🇻🇳", "lang_right": "Tiếng Nhật 🇯🇵",
        "warning": "Vui lòng nhập nội dung.", "processing": "Đang dịch...", "toast": "Xong!"
    },
    "jp_to_vi": {
        "title": "LSA TRANSLATOR", "subtitle": "Powered by Groq Engine ⚡",
        "placeholder": "翻訳する内容を入力してください...", "button": "⚡ 超高速翻訳",
        "result_title": "BẢN DỊCH TIẾNG VIỆT", "lang_left": "日本語 🇯🇵", "lang_right": "ベトナム語 🇻🇳",
        "warning": "内容を入力してください。", "processing": "翻訳中...", "toast": "完了!"
    }
}
current_lang_key = "jp_to_vi" if st.session_state.is_jp_to_vi else "vi_to_jp"
ui = UI_TEXT[current_lang_key]

# ================== 6. SYSTEM INSTRUCTION (SIÊU PROMPT) ==================
if st.session_state.is_jp_to_vi:
    sys_msg = f"""You are an expert Japanese to Vietnamese translator for a Manga Retouching and Graphic Design team. 
    [CRITICAL RULES]
    1. "Inpainting" MUST be translated as Folder/Nhóm (NEVER Layer).
    2. Dates MUST be YYYY/MM/DD (e.g. 2026/03/31).
    3. MANDATORY GLOSSARY:
    - フキダシ -> Bóng thoại
    - 描き文字 -> Chữ hiệu ứng (SFX)
    - 描き足し -> Vẽ bù / Redraw
    - 白抜き -> Viền trắng
    {dict_prompt_str}
    Only return the final translation. No intro/outro."""
else:
    sys_msg = f"""Bạn là một chuyên gia dịch thuật Việt - Nhật ngành Retouch/Manga.
    Dịch tự nhiên, chuyên nghiệp. Giữ nguyên tên riêng (Vinh, LS...).
    Sử dụng thuật ngữ: Retouch -> レタッチ, Vẽ bù -> 描き込み, SFX -> 描き文字."""

# ================== 7. HIỂN THỊ GIAO DIỆN CHÍNH ==================
st.markdown(f'<div class="groq-title-container"><div class="groq-title">{ui["title"]}</div><div class="groq-subtitle">{ui["subtitle"]}</div></div>', unsafe_allow_html=True)

col_l, col_btn, col_r = st.columns([2, 1, 2])
with col_l: st.markdown(f"<h4 style='text-align: right; color: #a0a0a0;'>{ui['lang_left']}</h4>", unsafe_allow_html=True)
with col_btn:
    if st.button("⇄", use_container_width=True):
        st.session_state.is_jp_to_vi = not st.session_state.is_jp_to_vi
        st.rerun()
with col_r: st.markdown(f"<h4 style='text-align: left; color: #f55036;'>{ui['lang_right']}</h4>", unsafe_allow_html=True)

st.write("")

# Nút Clear dùng Font Awesome
col_spacer1, col_clear = st.columns([8, 1])
with col_clear:
    if st.button("", on_click=clear_text, use_container_width=True, help="Clear"):
        pass
    # Chèn icon thùng rác vào nút trống phía trên bằng CSS
    st.markdown('<style>button[kind="secondary"]::before { font-family: "Font Awesome 6 Free"; content: "\\f2ed"; font-weight: 900; }</style>', unsafe_allow_html=True)

with st.form(key='translation_form', clear_on_submit=False):
    source_text = st.text_area("Input", height=160, placeholder=ui["placeholder"], key="main_input", label_visibility="collapsed")
    submit_button = st.form_submit_button(ui["button"], use_container_width=True)

# ================== 8. XỬ LÝ DỊCH VÀ HIỂN THỊ ==================
if submit_button:
    if source_text.strip():
        col_res_title, col_res_copy = st.columns([8, 1])
        with col_res_title:
            st.markdown(f'<div class="result-header"><i class="fa-solid fa-bolt"></i> {ui["result_title"]}</div>', unsafe_allow_html=True)
        with col_res_copy:
            copy_placeholder = st.empty()
            
        result_placeholder = st.empty()
        full_response = ""
        
        with st.spinner(ui["processing"]):
            try:
                prompt = f"Translate to {'Vietnamese' if st.session_state.is_jp_to_vi else 'Japanese'}:\n\n{source_text}"
                response = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[{"role": "system", "content": sys_msg}, {"role": "user", "content": prompt}],
                    temperature=0.0,
                    stream=True
                )
                for chunk in response:
                    content = chunk.choices[0].delta.content
                    if content:
                        full_response += content
                        result_placeholder.markdown(f'<div class="result-box">{full_response.replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)
                
                with copy_placeholder:
                    render_custom_copy_button(full_response)
                st.toast(ui["toast"], icon="✅")
            except Exception as e:
                st.error(f"Error: {str(e)}")
    else:
        st.warning(ui["warning"])

st.markdown(f'<div style="text-align: center; color: #555; font-size: 12px; margin-top: 50px;">{ui["jp_to_vi" if st.session_state.is_jp_to_vi else "vi_to_jp"]["processing"].replace("...", "")} © 2026 LinkStoryAsia</div>', unsafe_allow_html=True)
