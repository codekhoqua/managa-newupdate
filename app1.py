import json
import streamlit as st
from openai import OpenAI
import streamlit.components.v1 as components

# ================== 1. CẤU HÌNH TRANG & GIAO DIỆN ==================
st.set_page_config(page_title="LSA Translator | Groq", page_icon="⚡", layout="centered")

st.markdown("""
    <style>
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    .groq-title-container { text-align: center; margin-bottom: 30px; padding-bottom: 20px; border-bottom: 1px solid #333; }
    .groq-title {
        font-size: 2.8rem; font-weight: 900;
        background: linear-gradient(90deg, #f55036, #ff8c00);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-bottom: 5px; letter-spacing: -1px;
    }
    .groq-subtitle { color: #888; font-size: 1.1rem; font-weight: 400; }
    
    /* Style nút Submit */
    div[data-testid="stFormSubmitButton"] > button {
        background: linear-gradient(90deg, #f55036, #e03a20) !important;
        color: white !important; border: none !important; border-radius: 8px !important;
        font-weight: bold !important; font-size: 16px !important; transition: all 0.3s ease !important;
    }
    div[data-testid="stFormSubmitButton"] > button:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(245, 80, 54, 0.5) !important; }
    
    /* Style nút Xóa Text (Nút Copy cũng sẽ làm y hệt thế này) */
    .btn-clear > button {
        background-color: transparent !important; color: #ff4b4b !important; 
        border: 1px solid #ff4b4b !important; border-radius: 8px !important;
    }
    .btn-clear > button:hover { background-color: #ff4b4b !important; color: white !important; }

    /* Khung hiển thị lúc đang stream */
    .result-box {
        background: rgba(30, 30, 30, 0.6); backdrop-filter: blur(10px); color: #f0f0f0;
        padding: 24px; border-radius: 12px; border-left: 4px solid #f55036;
        border-top: 1px solid #333; border-right: 1px solid #333; border-bottom: 1px solid #333;
        font-size: 16.5px; line-height: 1.8; white-space: pre-wrap; min-height: 120px; margin-top: 10px; margin-bottom: 15px;
    }
    .result-header { font-size: 18px; font-weight: bold; color: #f55036; display: flex; align-items: center; gap: 8px; margin-top: 10px;}
    
    footer {visibility: hidden;}
    .stTextArea textarea { font-size: 15.5px !important; border-radius: 8px; }
    </style>
""", unsafe_allow_html=True)

# Hàm tạo nút Copy Custom bằng HTML/JS (CSS giống hệt nút Xóa)
def render_custom_copy_button(text_to_copy):
    js_text = json.dumps(text_to_copy)
    html_code = f"""
    <style>
        body {{ margin: 0; padding: 0; background-color: transparent; }}
        .copy-btn {{
            background-color: transparent; 
            color: #ff4b4b; 
            border: 1px solid #ff4b4b; 
            border-radius: 8px;
            padding: 8px 10px;
            font-size: 15px;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            cursor: pointer;
            width: 100%;
            text-align: center;
            transition: all 0.3s ease;
            box-sizing: border-box;
            display: inline-block;
        }}
        .copy-btn:hover {{
            background-color: #ff4b4b;
            color: white;
        }}
    </style>
    <button class="copy-btn" id="copyBtn" onclick='copyToClipboard()'>📋 Copy Text</button>
    
    <script>
    function copyToClipboard() {{
        navigator.clipboard.writeText({js_text}).then(function() {{
            var btn = document.getElementById('copyBtn');
            btn.innerHTML = '✅ Đã copy!';
            setTimeout(function() {{ btn.innerHTML = '📋 Copy Text'; }}, 2000);
        }}).catch(function(err) {{
            console.error('Lỗi copy: ', err);
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
    "グループ": "Group",
    "インペイント": "Inpainting",
    "削除補完": "Inpainting",
    "スクリプト": "Script",
    "パツンパツン": "Quá tải / Bận kẹt lịch",
    "パツパツ": "Quá tải / Bận kẹt lịch"
}
dict_prompt_str = "\n".join([f"   - {k} -> {v}" for k, v in DICT_JP_VI.items()])

# ================== 4. QUẢN LÝ TRẠNG THÁI ==================
if "is_jp_to_vi" not in st.session_state:
    st.session_state.is_jp_to_vi = False
if "main_input" not in st.session_state:
    st.session_state["main_input"] = ""

def clear_text():
    st.session_state["main_input"] = ""

# ================== 5. CẤU HÌNH NGÔN NGỮ UI ==================
UI_TEXT = {
    "vi_to_jp": {
        "title": "LSA TRANSLATOR", "subtitle": "Powered by Groq Engine ⚡",
        "placeholder": "Nhập nội dung cần dịch vào đây... (Ctrl + Enter để dịch)",
        "button": "⚡ Dịch Tốc Độ Cao", "toast": "Đã dịch xong trong chớp mắt!",
        "label_context": "Ngữ cảnh:", "label_input": "Văn bản nguồn:", "result_title": "BẢN DỊCH TIẾNG NHẬT",
        "warning": "Vui lòng nhập nội dung cần dịch.", "footer": "© 2026 LinkStoryAsia | Design Team Internal Tool Ver 4.5",
        "lang_left": "Tiếng Việt 🇻🇳", "lang_right": "Tiếng Nhật 🇯🇵"
    },
    "jp_to_vi": {
        "title": "LSA TRANSLATOR", "subtitle": "Powered by Groq Engine ⚡",
        "placeholder": "翻訳する内容を入力してください... (Ctrl + Enter)",
        "button": "⚡ 超高速翻訳", "toast": "翻訳が完了しました！",
        "label_context": "文脈:", "label_input": "原文:", "result_title": "ベトナム語訳",
        "warning": "内容を入力してください。", "footer": "© 2026 LinkStoryAsia | デザインチーム翻訳ツール Ver 4.5",
        "lang_left": "日本語 🇯🇵", "lang_right": "ベトナム語 🇻🇳"
    }
}

current_lang_key = "jp_to_vi" if st.session_state.is_jp_to_vi else "vi_to_jp"
ui = UI_TEXT[current_lang_key]

# ================== 6. SYSTEM INSTRUCTION (SIÊU PROMPT) ==================
if st.session_state.is_jp_to_vi:
    sys_msg = f"""Bạn là một chuyên gia dịch thuật tiếng Nhật sang tiếng Việt, làm việc tại bộ phận Design, Manga, Webtoon.
Đặc thù văn bản: Bao gồm thuật ngữ kỹ thuật (Photoshop) VÀ giao tiếp văn phòng, chỉ thị công việc hàng ngày, tiếng lóng công sở.

[NHIỆM VỤ TỐI THƯỢNG]
Chỉ trả về bản dịch cuối cùng. Tuyệt đối KHÔNG giải thích, KHÔNG chào hỏi, KHÔNG thêm '作業指示'.

[QUY TẮC DỊCH THUẬT & NGỮ CẢNH]
1. Xác định đúng hướng hành động: Tiếng Nhật thường ẩn chủ ngữ, phải phân tích kỹ động từ.
2. Từ lóng và ngữ cảnh: Chú ý các từ lóng văn phòng. Chú ý dịch chính xác tên riêng.
3. Từ điển thuật ngữ BẮT BUỘC:
{dict_prompt_str}
4. Ghép cặp thuật ngữ: Giữ kèm từ gốc/tiếng Anh trong ngoặc.
5. QUY TẮC DỰ PHÒNG: Nếu gặp thuật ngữ lạ KHÔNG CÓ trong từ điển, GIỮ NGUYÊN TIẾNG ANH.
6. Văn phong: Tự nhiên, ngắn gọn."""
else:
    sys_msg = f"""Bạn là một chuyên gia dịch thuật tiếng Việt sang tiếng Nhật, làm việc tại bộ phận Design, Manga, Webtoon.
Đặc thù văn bản: Bao gồm thuật ngữ kỹ thuật (Photoshop) VÀ giao tiếp văn phòng, chỉ thị công việc hàng ngày.

[NHIỆM VỤ TỐI THƯỢNG]
Chỉ trả về bản dịch cuối cùng. Tuyệt đối KHÔNG giải thích, KHÔNG chào hỏi, KHÔNG thêm '作業指示'.

[QUY TẮC DỊCH THUẬT & NGỮ CẢNH]
1. Tự nhiên theo giao tiếp Nhật Bản: Chuyển đổi linh hoạt văn phong.
2. Từ điển thuật ngữ BẮT BUỘC:
   - Retouch -> レタッチ
   - Vẽ bù / Vẽ thêm -> 描き込み / 加筆する
   - Lettering -> 写植
   - Làm sạch -> ゴミ取り
   - Layer ẩn -> 非表示レイヤー
   - Folder / Group -> フォルダ / グループ
   - Inpainting -> インペイント
   - Script -> スクリプト
3. Ghép cặp thuật ngữ: Định dạng 'Tiếng Nhật (Tiếng Anh)'.
4. Văn phong: Chuyên nghiệp, chuẩn xác."""

# ================== 7. HIỂN THỊ GIAO DIỆN CHÍNH ==================
st.markdown(f'<div class="groq-title-container"><div class="groq-title">{ui["title"]}</div><div class="groq-subtitle">{ui["subtitle"]}</div></div>', unsafe_allow_html=True)

col_l, col_btn, col_r = st.columns([2, 1, 2])
with col_l: st.markdown(f"<h4 style='text-align: right; color: #a0a0a0;'>{ui['lang_left']}</h4>", unsafe_allow_html=True)
with col_btn:
    if st.button("⇄", use_container_width=True, help="Đảo chiều dịch"):
        st.session_state.is_jp_to_vi = not st.session_state.is_jp_to_vi
        st.rerun()
with col_r: st.markdown(f"<h4 style='text-align: left; color: #f55036;'>{ui['lang_right']}</h4>", unsafe_allow_html=True)

st.write("")

# Nút xóa text ở khung Input
col_spacer1, col_clear = st.columns([5, 1])
with col_clear:
    st.markdown('<div class="btn-clear">', unsafe_allow_html=True)
    st.button("🗑️ Xóa Text", on_click=clear_text, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with st.form(key='translation_form', clear_on_submit=False):
    source_text = st.text_area(ui["label_input"], height=160, placeholder=ui["placeholder"], key="main_input", label_visibility="collapsed")
    
    col1, col2 = st.columns([2, 1]) 
    with col1:
        contexts = ["Văn phòng", "Kính ngữ", "Thân mật"] if not st.session_state.is_jp_to_vi else ["ビジネス", "丁寧語", "カジュアル"]
        mode = st.selectbox(ui["label_context"], contexts, label_visibility="collapsed")
    with col2:
        submit_button = st.form_submit_button(ui["button"], use_container_width=True)

# ================== 8. XỬ LÝ DỊCH VÀ HIỂN THỊ ==================
if submit_button:
    if source_text.strip():
        # Tạo Layout 2 cột: Tiêu đề kết quả (trái) và Nút Copy (phải)
        col_res_title, col_res_copy = st.columns([5, 1])
        with col_res_title:
            st.markdown(f'<div class="result-header"><span style="font-size: 22px;">⚡</span> {ui["result_title"]}</div>', unsafe_allow_html=True)
        with col_res_copy:
            copy_placeholder = st.empty() # Giữ chỗ chờ AI gõ xong mới hiện nút Copy
            
        result_placeholder = st.empty()
        full_response = ""
        
        with st.spinner("Processing..."):
            try:
                target_lang = "Vietnamese" if st.session_state.is_jp_to_vi else "Japanese"
                prompt = f"Dịch văn bản sau sang {target_lang} với phong cách {mode}: {source_text}"
                
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
                
                # Gõ xong -> Chèn Nút Copy vào vị trí góc phải bên trên
                with copy_placeholder:
                    render_custom_copy_button(full_response)

                st.toast(ui["toast"], icon="✅")
            except Exception as e:
                st.error(f"Lỗi hệ thống: {str(e)}")
    else:
        st.warning(ui["warning"])

st.markdown(f'<div style="text-align: center; color: #555; font-size: 12px; margin-top: 50px; font-weight: 500;">{ui["footer"]}</div>', unsafe_allow_html=True)
