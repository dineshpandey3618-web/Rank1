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
        
        # Users Table
        c.execute('''CREATE TABLE IF NOT EXISTS users
                     (username TEXT PRIMARY KEY, password TEXT, role TEXT, 
                      board TEXT, state TEXT)''')
        
        # Content Tables
        c.execute('''CREATE TABLE IF NOT EXISTS subjects
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, class TEXT, icon TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS chapters
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, subject_id INTEGER, name TEXT)''')
        
        # App Config
        c.execute('''CREATE TABLE IF NOT EXISTS app_config
                     (key TEXT PRIMARY KEY, value TEXT)''')
        
        # Defaults
        defaults = {
            "app_name": "Rank1 Academy",
            "notice_text": "📢 Welcome to New Session!",
            "show_notice": "True"
        }
        for key, val in defaults.items():
            try: c.execute("INSERT INTO app_config (key, value) VALUES (?,?)", (key, val))
            except: pass
            
        conn.commit()
    except: pass
    finally:
        try: conn.close()
        except: pass

# --- HELPER FUNCTIONS ---
def run_query(query, params=(), fetch=False):
    conn = sqlite3.connect('rank1_otp.db', check_same_thread=False)
    c = conn.cursor()
    try:
        c.execute(query, params)
        if fetch: return c.fetchall()
        conn.commit()
        return True
    except: return False
    finally: conn.close()

def get_config(key):
    res = run_query("SELECT value FROM app_config WHERE key=?", (key,), fetch=True)
    return res[0][0] if res else ""

def get_user(username):
    return run_query("SELECT * FROM users WHERE username=?", (username,), fetch=True)

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
    .notice-bar { background-color: #ff4b4b; color: white; padding: 10px; text-align: center; border-radius: 5px; margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user_id' not in st.session_state: st.session_state.user_id = None
if 'generated_otp' not in st.session_state: st.session_state.generated_otp = None
if 'current_view' not in st.session_state: st.session_state.current_view = "Home"
if 'selected_subject_id' not in st.session_state: st.session_state.selected_subject_id = None

# ==========================================
# 🛑 PART 1: LOGIN / SIGNUP
# ==========================================
if not st.session_state.logged_in:
    st.title(f"🎓 {get_config('app_name')}")
    
    tab1, tab2, tab3 = st.tabs(["🔐 Login", "📝 Sign Up", "🛠 Admin"])

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
                st.error("Wrong details.")

    # --- SIGNUP (Mobile + Email) ---
    with tab2:
        st.subheader("Create New Account")
        
        # Selection: Mobile or Email
        reg_type = st.radio("Register using:", ["Mobile Number", "Email ID"], horizontal=True)
        
        if reg_type == "Mobile Number":
            s_user = st.text_input("Enter Mobile Number", placeholder="9876543210")
            msg_type = "SMS"
        else:
            s_user = st.text_input("Enter Email ID", placeholder="student@gmail.com")
            msg_type = "Email"

        # OTP Logic
        col1, col2 = st.columns([2,1])
        if col2.button("Send OTP"):
            if len(s_user) > 4: # Basic validation
                otp = generate_otp()
                st.session_state.generated_otp = otp
                with st.spinner(f"Sending OTP to {msg_type}..."):
                    time.sleep(1)
                st.toast(f"✅ OTP Sent to {msg_type}: {otp}", icon="📩")
                st.info(f"DEMO OTP: **{otp}**")
            else:
                st.warning(f"Enter valid {reg_type}")
        
        entered_otp = col1.text_input("Enter OTP")
        s_pass = st.text_input("Create Password", type="password")
        
        if st.button("Verify & Create Account"):
            if st.session_state.generated_otp and entered_otp == st.session_state.generated_otp:
                if s_user and s_pass:
                    if run_query("INSERT INTO users (username, password) VALUES (?,?)", (s_user, s_pass)):
                        st.success("Account Created!")
                        # AUTO LOGIN CODE
                        st.session_state.logged_in = True
                        st.session_state.user_id = s_user
                        st.session_state.generated_otp = None
                        st.rerun() # Immediately open the App/Menu
                    else:
                        st.error("User already registered.")
                else:
                    st.warning("Fill password.")
            else:
                st.error("Invalid OTP.")

    # --- ADMIN ---
    with tab3:
        if st.button("Admin Panel"):
            st.session_state.logged_in = True
            st.session_state.user_id = "ADMIN"
            st.rerun()

# ==========================================
# 🚀 PART 2: INSIDE APP (AUTO MENU)
# ==========================================
else:
    if st.session_state.user_id == "ADMIN":
        st.sidebar.title("🛠 Admin")
        if st.sidebar.button("Logout"): st.session_state.logged_in=False; st.rerun()
        st.title("Admin Panel")
        
        with st.expander("Add Subject", expanded=True):
            with st.form("sub"):
                n = st.text_input("Name"); i = st.selectbox("Icon", ["📐","🔬","🌍"]); c = st.selectbox("Class", [f"Class {x}" for x in range(6,13)])
                if st.form_submit_button("Add"): run_query("INSERT INTO subjects (name, class, icon) VALUES (?,?,?)", (n,c,i)); st.success("Added")
        
        with st.expander("App Settings"):
             nt = st.text_input("Notice Text", value=get_config("notice_text"))
             if st.button("Update Notice"): run_query("REPLACE INTO app_config (key, value) VALUES ('notice_text', ?)", (nt,)); st.success("Updated")

    else:
        # STUDENT AREA
        user_row = get_user(st.session_state.user_id)[0]
        
        # ----------------------------------------
        # 🔥 THE MENU (Profile Setup) - Opens automatically if new
        # ----------------------------------------
        if user_row[3] is None: # If Board is not selected
            st.title("⚙️ Complete Your Profile")
            st.info("👋 Welcome! Please set up your class to continue.")
            
            with st.form("setup_form"):
                role = st.radio("I am a:", ["Student", "Teacher"], horizontal=True)
                st.write("---")
                board = st.selectbox("Select Board", ["CBSE", "ICSE", "State Board"])
                
                state_val = "N/A"
                if board == "State Board":
                    state_val = st.selectbox("Select State", ["Bihar Board", "Jharkhand Board", "UP Board"])
                
                if st.form_submit_button("Save & Start Learning 🚀"):
                    run_query("UPDATE users SET role=?, board=?, state=? WHERE username=?", 
                              (role, board, state_val, st.session_state.user_id))
                    st.rerun()

        # ----------------------------------------
        # 🏠 MAIN DASHBOARD (After Setup)
        # ----------------------------------------
        else:
            # Navbar
            c1, c2, c3, c4 = st.columns(4)
            if c1.button("🏠 Home"): st.session_state.current_view="Home"; st.session_state.selected_subject_id=None
            if c2.button("🏆 Tests"): st.session_state.current_view="Tests"
            if c3.button("📰 News"): st.session_state.current_view="News"
            if c4.button("🚪 Exit"): st.session_state.logged_in=False; st.rerun()
            st.divider()
            
            # Notice
            if get_config("show_notice") == "True":
                st.markdown(f'<div class="notice-bar">{get_config("notice_text")}</div>', unsafe_allow_html=True)

            if st.session_state.current_view == "Home":
                if st.session_state.selected_subject_id is None:
                    st.subheader("Select Class")
                    cls = st.selectbox("View Subjects for:", [f"Class {i}" for i in range(6,13)])
                    
                    subs = run_query("SELECT id, name, icon FROM subjects WHERE class=?", (cls,), fetch=True)
                    if subs:
                        cols = st.columns(3)
                        for i, s in enumerate(subs):
                            if cols[i%3].button(f"{s[2]}\n{s[1]}", key=s[0]):
                                st.session_state.selected_subject_id = s[0]
                                st.rerun()
                    else: st.info("No subjects added yet.")
                else:
                    if st.button("⬅️ Back"): st.session_state.selected_subject_id=None; st.rerun()
                    chaps = run_query("SELECT name FROM chapters WHERE subject_id=?", (st.session_state.selected_subject_id,), fetch=True)
                    if chaps:
                        st.selectbox("Select Chapter", [c[0] for c in chaps])
                        st.info("Chapter content will appear here.")
                    else: st.warning("No chapters in this subject.")

            elif st.session_state.current_view == "Tests": st.write("Weekly Test Series (Coming Soon)")
            elif st.session_state.current_view == "News":
                try:
                    feed = feedparser.parse("https://news.google.com/rss/search?q=education+india")
                    for e in feed.entries[:5]: st.write(f"🔹 {e.title}")
                except: st.write("News unavailable")
