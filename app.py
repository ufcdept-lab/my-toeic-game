import streamlit as st
import pandas as pd
import random
import os
import re
import requests
import streamlit.components.v1 as components

# --- 1. ตั้งค่าหน้าเว็บ ---
st.set_page_config(page_title="TOEIC Master", layout="centered")

st.markdown("""
    <style>
    .main .block-container { padding-top: 1rem; padding-bottom: 1rem; max-width: 500px; }
    .stRadio > label { font-size: 1.1rem !important; font-weight: 600; }
    div.stButton > button { width: 100%; border-radius: 12px; height: 3.5rem; font-weight: bold; }
    .vocab-header { text-align: center; color: #2E86C1; margin-top: 0; margin-bottom: 5px; }
    .vocab-type { color: #85929E; font-size: 1.2rem; font-weight: normal; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ฟังก์ชันโหลดคำศัพท์ และ ฐานข้อมูล Google Sheets ---
@st.cache_data
def load_vocab():
    file_path = "TOEIC_Vocab_3000.xlsx"
    if os.path.exists(file_path):
        return pd.read_excel(file_path).to_dict('records')
    return None

vocab_list = load_vocab()

if not vocab_list:
    st.error("❌ ไม่พบไฟล์ Excel คำศัพท์ บน GitHub ครับ")
    st.stop()

# ลิงก์ Web App จาก Google Sheets
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbytSH5n98Adeqp_v8wfKqH7vILIMPcd4-8nsDlN_0hikm9XmVtz9t6CJ0MDbuwTY3UuMw/exec"

def load_users():
    try:
        response = requests.get(WEB_APP_URL)
        data = response.json()
        if len(data) > 0:
            return pd.DataFrame(data)
        else:
            return pd.DataFrame(columns=["Username", "TOEIC_History", "Status"])
    except:
        return pd.DataFrame(columns=["Username", "TOEIC_History", "Status"])

def save_new_user(username, toeic_score):
    payload = {
        "Username": username,
        "TOEIC_History": toeic_score,
        "Status": "Free"
    }
    try:
        requests.post(WEB_APP_URL, json=payload)
    except:
        pass

# --- 3. ระบบ Session State ---
if 'logged_in' not in st.session_state:
    st.session_state.update({
        'logged_in': False, 'user': None, 'status': 'Free', 
        'score': 0, 'count': 0, 'ans_submitted': False, 'options': []
    })

# --- 4. หน้า Login & Registration ---
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center;'>🚀 TOEIC Master</h1>", unsafe_allow_html=True)
    st.write("---")
    
    st.info("💡 **รูปแบบการเข้าระบบ:** ชื่อเล่น + ตัวเลข 4 หลัก (เช่น Somchai1234)")
    username_input = st.text_input("👤 กรอกชื่อผู้เล่น:")
    
    if username_input:
        if re.match(r'^[^\d]+\d{4}$', username_input.strip()):
            username_clean = username_input.strip()
            df = load_users()
            
            # --- กรณีที่ 1: เคยลงทะเบียนแล้ว (Login) ---
            if not df.empty and username_clean in df['Username'].values:
                user_data = df[df['Username'] == username_clean].iloc[0]
                status = user_data.get('Status', 'Free')
                
                st.success(f"✅ ยินดีต้อนรับกลับมาครับคุณ {username_clean}")
                
                if status == 'Free':
                    st.info("📢 **สถานะบัญชี:** ใช้งานฟรี (สุ่มจาก 1,000 คำ)")
                    with st.expander("💎 ต้องการใช้งานเต็มรูปแบบ (3,000 คำ)?"):
                        st.warning("ระบบนี้เป็นเวอร์ชันฟรี 1,000 คำ\n\nหากต้องการใช้งานชุดข้อสอบเต็ม 3,000 คำ **ค่าสมัคร 99 บาท**")
                        # แสดง QR Code พร้อมเพย์อัตโนมัติ
                        st.image("https://promptpay.io/0800894787.png", caption="สแกนเพื่อชำระเงิน (พร้อมเพย์: 0800894787)", width=200)
                        st.success("📲 เมื่อโอนเงินแล้ว กรุณาแจ้ง Admin (สลิป) เพื่อทำการตรวจสอบและอนุมัติครับ")
                else:
                    st.success("💎 **สถานะบัญชี:** VIP (สุ่มจาก 3,000 คำเต็ม)")
                
                st.write("---")
                num_q = st.select_slider("🔢 จำนวนข้อ:", options=[5, 10, 15, 20, 30], value=10)
                use_timer = st.checkbox("⏰ เปิดระบบจับเวลา")
                time_limit = st.selectbox("วินาทีต่อข้อ:", [10, 15, 20, 30], index=1) if use_timer else 0
                
                if st.button("เริ่มเกม 🎮"):
                    if status == 'Free':
                        available_vocab = vocab_list[:1000] 
                    else:
                        available_vocab = vocab_list 
                        
                    st.session_state.update({
                        'logged_in': True, 'user': username_clean, 'status': status,
                        'total_q': num_q, 'time_limit': time_limit,
                        'questions': random.sample(available_vocab, num_q)
                    })
                    st.rerun()

            # --- กรณีที่ 2: ยังไม่เคยลงทะเบียน (Register) ---
            else:
                st.warning("📝 ไม่พบประวัติ กรุณาลงทะเบียนครั้งแรกก่อนเข้าใช้งาน")
                has_score = st.radio("คุณเคยสอบ TOEIC หรือไม่?", ["ไม่เคยสอบ", "เคยสอบแล้ว"], horizontal=True)
                toeic_history = "ไม่เคยสอบ"
                
                if has_score == "เคยสอบแล้ว":
                    toeic_history = st.number_input("โปรดระบุคะแนน TOEIC ล่าสุด:", min_value=10, max_value=990, step=5)
                
                if st.button("บันทึกข้อมูลและลงทะเบียน ✅"):
                    save_new_user(username_clean, toeic_history)
                    st.success("🎉 ลงทะเบียนสำเร็จ! ข้อมูลถูกบันทึกไปยังฐานข้อมูลแล้ว กรุณากดปุ่ม 'เข้าสู่ระบบ' ด้านล่าง")
                    if st.button("เข้าสู่ระบบ ➡"):
                        st.rerun()
        else:
            st.error("⚠️ รูปแบบชื่อไม่ถูกต้อง! ต้องเป็น ชื่อเล่น + ตัวเลข 4 หลัก (เช่น Somchai1234)")

# --- 5. หน้า Game ---
else:
    if st.session_state.count < st.session_state.total_q:
        q = st.session_state.questions[st.session_state.count]
        
        col1, col2 = st.columns([1, 1])
        col1.write(f"📝 **ข้อ {st.session_state.count + 1}/{st.session_state.total_q}**")
        col2.markdown(f"<div style='text-align: right;'>🏆 คะแนน: <b>{st.session_state.score}</b></div>", unsafe_allow_html=True)

        if st.session_state.time_limit > 0 and not st.session_state.ans_submitted:
            timer_html = f"""
                <style>
                #progress-container {{ width: 100%; background-color: #e0e0e0; border-radius: 10px; margin-bottom: 10px; height: 20px; overflow: hidden; border: 1px solid #ddd; }}
                #progress-bar {{ width: 100%; height: 100%; background-color: #4CAF50; transition: width 1s linear, background-color 0.5s; }}
                </style>
                <div id="progress-container"><div id="progress-bar"></div></div>
                <div style="text-align:center; font-family:sans-serif; font-weight:bold; font-size:1.2rem; color:#333;">⏳ <span id="time-text">{st.session_state.time_limit}</span> วินาที</div>
                <script>
                var total = {st.session_state.time_limit}; var current = total;
                var bar = document.getElementById("progress-bar"); var text = document.getElementById("time-text");
                var interval = setInterval(function() {{
                    current--; text.innerHTML = current;
                    var percent = (current / total) * 100; bar.style.width = percent + "%";
                    if (percent <= 30) bar.style.backgroundColor = "#FF5252"; else if (percent <= 60) bar.style.backgroundColor = "#FFC107"; else bar.style.backgroundColor = "#4CAF50";
                    if (current <= 0) {{ clearInterval(interval); var btn = window.parent.document.querySelector('.stButton button'); if(btn) btn.click(); }}
                }}, 1000);
                </script>
            """
            components.html(timer_html, height=85)

        st.write("---")
        st.markdown(f"<h1 class='vocab-header'>{q['คำศัพท์']} <span class='vocab-type'>({q['ประเภท']})</span></h1>", unsafe_allow_html=True)
        
        correct = q['ความหมาย']
        if not st.session_state.options:
            wrong = random.sample([v['ความหมาย'] for v in vocab_list if v['ความหมาย'] != correct], 3)
            opts = wrong + [correct]
            random.shuffle(opts)
            st.session_state.options = opts

        answer = st.radio("เลือกคำแปล:", st.session_state.options, label_visibility="collapsed", disabled=st.session_state.ans_submitted)

        if not st.session_state.ans_submitted:
            if st.button("ตกลง ✅"):
                st.session_state.ans_submitted = True
                if answer == correct:
                    st.session_state.score += 1
                    st.session_state.last_result = "correct"
                else:
                    st.session_state.last_result = "wrong"
                st.rerun()
        else:
            if st.session_state.last_result == "correct":
                st.success("### ✅ ถูกต้องครับ!")
            else:
                st.error(f"### ❌ ผิด! หรือหมดเวลา! คำตอบคือ: **{correct}**")
            
            with st.expander("📖 ดูคำอธิบาย", expanded=True):
                st.write(f"*{q['ตัวอย่าง']}*")
                st.caption(f"แปล: {q['แปลประโยค']}")
            
            if st.button("ข้อต่อไป ➡"):
                st.session_state.update({'count': st.session_state.count + 1, 'ans_submitted': False, 'options': []})
                st.rerun()
    
    else:
        st.balloons()
        st.markdown("<h1 style='text-align: center;'>🎊 จบเกม!</h1>", unsafe_allow_html=True)
        st.markdown(f"<h1 style='text-align: center; color: #E74C3C;'>{st.session_state.score} / {st.session_state.total_q}</h1>", unsafe_allow_html=True)
        if st.button("🔄 ออกจากระบบ / เล่นใหม่"):
            st.session_state.clear()
            st.rerun()