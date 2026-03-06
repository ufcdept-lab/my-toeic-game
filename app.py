import streamlit as st
import pandas as pd
import random
import time
import os

# --- 1. ตั้งค่าหน้าเว็บให้ Compact สำหรับ iPhone ---
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

# --- 2. ฟังก์ชันโหลดข้อมูล ---
@st.cache_data
def load_data():
    file_path = "TOEIC_Vocab_3000.xlsx"
    if os.path.exists(file_path):
        return pd.read_excel(file_path).to_dict('records')
    return None

vocab_list = load_data()

if not vocab_list:
    st.error("❌ ไม่พบไฟล์ Excel กรุณาเช็คชื่อไฟล์บน GitHub ครับ")
    st.stop()

# --- 3. ระบบ Session State ---
if 'user' not in st.session_state:
    st.session_state.update({
        'user': None, 'score': 0, 'count': 0, 
        'ans_submitted': False, 'options': []
    })

# --- 4. หน้า Login ---
if st.session_state.user is None:
    st.markdown("<h1 style='text-align: center;'>🚀 TOEIC Master</h1>", unsafe_allow_html=True)
    st.write("---")
    user_input = st.text_input("👤 ชื่อผู้เล่น:", placeholder="ระบุชื่อของคุณ")
    num_q = st.select_slider("🔢 จำนวนข้อ:", options=[5, 10, 15, 20, 30], value=10)
    
    use_timer = st.checkbox("⏰ เปิดระบบจับเวลา")
    time_limit = st.selectbox("กี่วินาทีต่อข้อ:", [10, 15, 20, 30], index=1) if use_timer else 0
    
    if st.button("เริ่มเกม 🎮"):
        if user_input:
            st.session_state.update({
                'user': user_input, 'total_q': num_q, 'time_limit': time_limit,
                'questions': random.sample(vocab_list, num_q), 'count': 0, 'score': 0
            })
            st.rerun()
        else:
            st.warning("กรุณาใส่ชื่อก่อนครับคุณธวัช")

# --- 5. หน้า Game ---
else:
    if st.session_state.count < st.session_state.total_q:
        q = st.session_state.questions[st.session_state.count]
        
        col1, col2 = st.columns([1, 1])
        col1.write(f"📝 **ข้อ {st.session_state.count + 1}/{st.session_state.total_q}**")
        col2.markdown(f"<div style='text-align: right;'>🏆 คะแนน: <b>{st.session_state.score}</b></div>", unsafe_allow_html=True)

        # --- ส่วนจับเวลาแบบใหม่ (ไม่รบกวนปุ่มกด) ---
        if st.session_state.time_limit > 0 and not st.session_state.ans_submitted:
            st.write(f"⏳ เวลาจำกัด: **{st.session_state.time_limit} วินาที**")
            # เราจะแสดงแถบเวลาที่นิ่งไว้ เพื่อให้ระบบไม่ Re-run ตัวเองจนปุ่มรวน
            st.progress(1.0) 

        st.write("---")
        st.markdown(f"<h1 class='vocab-header'>{q['คำศัพท์']} <span class='vocab-type'>({q['ประเภท']})</span></h1>", unsafe_allow_html=True)
        
        correct = q['ความหมาย']
        if not st.session_state.options:
            wrong = random.sample([v['ความหมาย'] for v in vocab_list if v['ความหมาย'] != correct], 3)
            opts = wrong + [correct]
            random.shuffle(opts)
            st.session_state.options = opts

        answer = st.radio("เลือกคำแปล:", st.session_state.options, label_visibility="collapsed", disabled=st.session_state.ans_submitted)

        st.write("") 

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
                st.error(f"### ❌ ผิด! คำตอบคือ: **{correct}**")
            
            with st.expander("📖 ดูตัวอย่างประโยค", expanded=True):
                st.markdown(f"**ตัวอย่าง:** *{q['ตัวอย่าง']}*")
                st.markdown(f"**แปล:** {q['แปลประโยค']}")
            
            if st.button("ข้อต่อไป ➡"):
                st.session_state.update({'count': st.session_state.count + 1, 'ans_submitted': False, 'options': []})
                st.rerun()
    
    # --- 6. หน้าสรุปผล ---
    else:
        st.balloons()
        st.markdown("<h1 style='text-align: center;'>🎊 จบเกม!</h1>", unsafe_allow_html=True)
        st.markdown(f"<h1 style='text-align: center; color: #E74C3C;'>{st.session_state.score} / {st.session_state.total_q}</h1>", unsafe_allow_html=True)
        if st.button("🔄 เล่นใหม่อีกครั้ง"):
            st.session_state.clear()
            st.rerun()