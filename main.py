import streamlit as st
import sqlite3
import random
import time
import feedparser

# --- 1. DATABASE SETUP ---
def init_db():
    try:
        conn = sqlite3.connect('rank1_otp.db', check_same_thread=False)
        c = conn.cursor()
        
        c.execute('''CREATE TABLE IF NOT EXISTS users
                     (username TEXT PRIMARY KEY, password TEXT, role TEXT, 
                      board TEXT, state TEXT)''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS subjects
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, class TEXT, icon TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS chapters
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, subject_id INTEGER, name TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS materials
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, chapter_id INTEGER, type TEXT, title TEXT, link TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS tests
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, class TEXT, subject TEXT, price INTEGER)''')

        # App Config for Dynamic Updates
        c.execute('''CREATE TABLE IF NOT EXISTS app_config
                     (key TEXT PRIMARY KEY, value TEXT)''')
        
        # Set Defaults
        defaults = {
            "app_name": "Rank1 Academy",
            "welcome_msg": "Your Gateway to Success",
            "banner_url": "https://via.placeholder.com/800x200.png?text=Welcome+to+Rank1",
            "notice_text": "📢 New Batch starting soon!",
            "show_notice": "True"
        }
        for key, val in defaults.items():
            try:
                c.execute("INSERT INTO app_config (key, value) VALUES (?,?)", (key, val))
            except: pass
            
        conn.commit()
    except Exception as e:
        pass # Handle db lock gracefully
    finally:
        try: conn.close()
        except: pass

# --- DB HELPER FUNCTIONS ---
def run_query(query, params=(), fetch=False):
    conn = sqlite3.connect('rank1_otp.db', check_same_thread=False)
    c = conn.cursor()
    try:
        c.execute(query, params)
        if fetch:
            return c.fetchall()
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

def get_config(key):
    res = run_query("SELECT value FROM app_config WHERE key=?", (key,), fetch=True)
    return res[0][0] if res else ""

def get_user(username):
    return run_query("SELECT * FROM users WHERE username=?", (username,), fetch=True)

# --- OTP GENERATOR ---
def generate_otp():
    return str(random.randint(1000, 9999))

# --- APP CONFIG ---
st.set_page_config(page_title="Rank1", page_icon="🎓", layout="wide")
init_db()

# --- CSS ---
st.markdown("""
<style>
    [data-testid="stSidebarNav"] {display: none;}
    .stButton>button { width: 100%; border-radius: 8px; }
    .notice-bar {
        background-color: #ff4b4b; color: white; padding: 10px; text-align: center; font-weight: bold; margin-bottom: 10px; border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user_id' not in st.session_state: st.session_state.user_id = None
if 'current_view' not in st.session_state: st.session_state.current_view = "Home"
if 'selected_subject_id' not in st.session_state: st.session_state.selected_subject_id = None
if 'generated_otp' not in st.session_state: st.session_state.generated_otp = None
if 'otp_verified' not in st.session_state: st.session_state.otp_verified = False

# ==========================================
# 🛑 PART 1: LOGIN / SIGNUP (WITH OTP)
# ==========================================
if not st.session_state.logged_in:
    app_name = get_config("app_name")
    st.title(f"🎓 {app_name}")
    
    tab1, tab2, tab3 = st.tabs(["🔐 Login", "📝 Sign Up (OTP)", "🛠 Admin"])

    # --- LOGIN ---
    with tab1:
        l_user = st.text_input("Mobile / Email", key="l_u")
        l_pass = st.text_input("Password", type="password", key="l_p")
        if st.button("Login Now"):
            user_data = get_user(l_user)
            if user_data and user_data[0][1] == l_pass:
                st.session_state.logged_in = True
                st.session_state.user_id = l_user
                st.rerun()
            else:
                st.error("Incorrect Mobile or Password.")

    # --- SIGNUP WITH OTP ---
    with tab2:
        st.subheader("Create New Account")
        
        # Step 1: Enter Details
        s_user = st.text_input("Mobile Number", key="s_u", placeholder="Enter 10 digit number")
        
        # Step 2: Send OTP Button
        col_otp1, col_otp2 = st.columns([2,1])
        if col_otp2.button("Send OTP"):
            if len(s_user) >= 10:
                otp = generate_otp()
                st.session_state.generated_otp = otp
                # SIMULATING SMS SENDING
                with st.spinner("Sending OTP..."):
                    time.sleep(1.5)
                st.toast(f"🔔 SMS Sent! Your OTP is: {otp}", icon="📩")
                st.info(f"DEMO MODE: Your OTP is **{otp}**") 
            else:
                st.warning("Please enter valid mobile number.")
        
        # Step 3: Verify OTP
        entered_otp = col_otp1.text_input("Enter OTP", key="otp_in")
        
        s_pass = st.text_input("Create Password", type="password", key="s_p")
        
        if st.button("Verify & Create Account"):
            # Check if OTP matches
            if st.session_state.generated_otp and entered_otp == st.session_state.generated_otp:
                if s_user and s_pass:
                    if run_query("INSERT INTO users (username, password) VALUES (?,?)", (s_user, s_pass)):
                        st.balloons()
                        st.success("✅ Verification Successful! Account Created.")
                        st.session_state.generated_otp = None # Reset
                        time.sleep(2)
                    else:
                        st.error("User already registered.")
                else:
                    st.warning("Enter password.")
            else:
                st.error("❌ Invalid OTP! Try again.")

    # --- ADMIN ---
    with tab3:
        if st.button("Admin Login"):
            st.session_state.logged_in = True
            st.session_state.user_id = "ADMIN"
            st.rerun()

# ==========================================
# 🚀 PART 2: INSIDE APP (SAME AS BEFORE)
# ==========================================
else:
    if st.session_state.user_id == "ADMIN":
        st.sidebar.title("🛠 Admin")
        if st.sidebar.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()
        st.title("Admin Panel")
        choice = st.radio("Manage:", ["App Settings", "Subjects", "Chapters", "PDFs"], horizontal=True)
        
        if choice == "App Settings":
            with st.form("set"):
                n = st.text_input("App Name", value=get_config("app_name"))
                nt = st.text_input("Notice", value=get_config("notice_text"))
                if st.form_submit_button("Update"):
                    run_query("REPLACE INTO app_config (key, value) VALUES ('app_name', ?)", (n,))
                    run_query("REPLACE INTO app_config (key, value) VALUES ('notice_text', ?)", (nt,))
                    st.success("Updated")

        elif choice == "Subjects":
            with st.form("sub"):
                n = st.text_input("Name"); i = st.selectbox("Icon", ["📐","🔬","🌍"]); c = st.selectbox("Class", [f"Class {x}" for x in range(6,13)])
                if st.form_submit_button("Add"): 
                    run_query("INSERT INTO subjects (name, class, icon) VALUES (?,?,?)", (n,c,i))
                    st.success("Added")
                    
        elif choice == "Chapters":
            subs = run_query("SELECT id, name FROM subjects", fetch=True)
            if subs:
                sid = st.selectbox("Subject", [s[0] for s in subs], format_func=lambda x: next(y[1] for y in subs if y[0]==x))
                cn = st.text_input("Chapter")
                if st.button("Add"): run_query("INSERT INTO chapters (subject_id, name) VALUES (?,?)", (sid, cn)); st.success("Added")

    else:
        # STUDENT VIEW
        user_row = get_user(st.session_state.user_id)[0]
        if user_row[3] is None:
            st.title("⚙️ Setup Profile")
            r = st.radio("Role", ["Student", "Teacher"])
            b = st.selectbox("Board", ["CBSE", "State Board"])
            s = st.selectbox("State", ["Bihar", "Jharkhand"]) if b == "State Board" else "N/A"
            if st.button("Save"):
                run_query("UPDATE users SET role=?, board=?, state=? WHERE username=?", (r,b,s,st.session_state.user_id))
                st.rerun()
        else:
            # NAVBAR
            c1, c2, c3, c4 = st.columns(4)
            if c1.button("🏠 Home"): st.session_state.current_view="Home"; st.session_state.selected_subject_id=None
            if c2.button("🏆 Tests"): st.session_state.current_view="Tests"
            if c3.button("📰 News"): st.session_state.current_view="News"
            if c4.button("🚪 Exit"): st.session_state.logged_in=False; st.rerun()
            st.divider()
            
            # NOTICE BAR
            if get_config("show_notice") == "True":
                st.markdown(f'<div class="notice-bar">📢 {get_config("notice_text")}</div>', unsafe_allow_html=True)

            if st.session_state.current_view == "Home":
                if st.session_state.selected_subject_id is None:
                    st.subheader("Select Class")
                    cls = st.selectbox("", [f"Class {i}" for i in range(6,13)])
                    subs = run_query("SELECT id, name, icon FROM subjects WHERE class=?", (cls,), fetch=True)
                    if subs:
                        cols = st.columns(3)
                        for i, s in enumerate(subs):
                            if cols[i%3].button(f"{s[2]}\n{s[1]}", key=s[0]):
                                st.session_state.selected_subject_id = s[0]
                                st.rerun()
                    else: st.info("No subjects.")
                else:
                    if st.button("⬅️ Back"): st.session_state.selected_subject_id=None; st.rerun()
                    chaps = run_query("SELECT name FROM chapters WHERE subject_id=?", (st.session_state.selected_subject_id,), fetch=True)
                    if chaps:
                        sc = st.selectbox("Chapter", [c[0] for c in chaps])
                        st.write(f"Content for {sc}")
                        st.info("Notes and PDFs will appear here.")
                    else: st.warning("No chapters.")

            elif st.session_state.current_view == "Tests": st.write("Weekly Tests")
            elif st.session_state.current_view == "News":
                try:
                    feed = feedparser.parse("https://news.google.com/rss/search?q=education+india")
                    for e in feed.entries[:5]: st.write(f"- {e.title}")
                except: st.error("Offline")
