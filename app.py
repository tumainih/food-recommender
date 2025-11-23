# app.py
import streamlit as st
import pandas as pd
import os
from datetime import datetime
from email.mime.text import MIMEText
import smtplib

# -------------------------
# CONFIG
# -------------------------
DATA_CSV = "VYAKULA.csv"
USERS_CSV = "users.csv"
GENERAL_DATASET = "general_dataset.csv"

# Prefer environment variables for credentials; fallback to hardcoded for compatibility
EMAIL_SENDER = os.environ.get("FR_ADMIN_EMAIL", "appsstudy767@gmail.com")
EMAIL_PASSWORD = os.environ.get("FR_ADMIN_PASSWORD", "3232Lhf@")

# -------------------------
# HELPER FUNCTIONS
# -------------------------
def ensure_csv(path, columns):
    if os.path.exists(path):
        df = pd.read_csv(path)
        for c in columns:
            if c not in df.columns:
                df[c] = pd.NA
        return df
    else:
        df = pd.DataFrame(columns=columns)
        df.to_csv(path, index=False)
        return df

def save_csv(df, path):
    df.to_csv(path, index=False)

def get_nutrient_value(row, col):
    if col in row and pd.notna(row[col]):
        try:
            return float(row[col])
        except:
            s = str(row[col])
            digits = ''.join(ch for ch in s if (ch.isdigit() or ch=='.' or ch=='-'))
            try:
                return float(digits) if digits else 0.0
            except:
                return 0.0
    return 0.0

def calculate_bmi(weight_kg, height_m):
    """Calculate BMI: weight(kg) / height(m)^2"""
    if height_m > 0:
        return round(weight_kg / (height_m ** 2), 2)
    return 0.0

def calculate_bmr(weight_kg, height_cm, age, sex):
    """Calculate Basal Metabolic Rate using Mifflin-St Jeor equation"""
    if sex.upper() == 'M':
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    else:  # Female
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161
    return round(bmr, 2)

def calculate_tdee(bmr, activity_level):
    """Calculate Total Daily Energy Expenditure based on activity level"""
    activity_factors = {
        "Sedentary": 1.2,
        "Light": 1.375,
        "Moderate": 1.55,
        "Very Active": 1.725,
        "Extra Active": 1.9
    }
    factor = activity_factors.get(activity_level, 1.55)
    return round(bmr * factor, 2)

def send_email(to, subject, body):
    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        # Use admin email as the visible sender
        msg['From'] = f"Admin <{EMAIL_SENDER}>"
        msg['Reply-To'] = EMAIL_SENDER
        msg['To'] = to
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        # allow `to` to be a list or a single email
        recipients = to if isinstance(to, (list, tuple)) else [to]
        server.sendmail(EMAIL_SENDER, recipients, msg.as_string())
        server.quit()
        return True
    except:
        return False

# -------------------------
# LOAD USERS
# -------------------------
user_cols = ["email", "name", "password"]
users_df = ensure_csv(USERS_CSV, user_cols)

# -------------------------
# LOAD GENERAL DATASET
# -------------------------
general_cols = ["Barua Pepe", "Jina", "Jinsia", "Urefu", "Uzito", "BMI", "TDEE", "Lengo la Afya", "Vyakula Vilivyopendekezwa", "Vyakula Vilivyotumika", "Ukadiriaji wa Maendeleo ya Lengo", "Maelezo ya Maendeleo (waweza kuelezea mabadiliko ya vipimo au hali ya mwili)", "Tarehe ya Pendekezo", "ReminderSent"]
general_df = ensure_csv(GENERAL_DATASET, general_cols)

# Email reminders on app load
now = pd.Timestamp.now()
reminder_candidates = general_df[(pd.to_datetime(general_df['Tarehe ya Pendekezo'], errors='coerce') + pd.Timedelta(days=14) <= now) & general_df['Vyakula Vilivyotumika'].isna() & (general_df['ReminderSent'].isna() | (general_df['ReminderSent'] == False))]
for idx, row in reminder_candidates.iterrows():
    email = row['Barua Pepe']
    subject = "Ukumbusho: Tafadhali toa mrejesho kwa mapendekezo yako ya vyakula"
    body = f"Habari,\n\nTafadhali ingia kwenye app na toa mrejesho kwa mapendekezo uliyopata tarehe {row['Tarehe ya Pendekezo']}.\n\nAsante."
    if send_email(email, subject, body):
        general_df.at[idx, 'ReminderSent'] = True
        save_csv(general_df, GENERAL_DATASET)

# Ensure admin exists
admin_email = "appsstudy767@gmail.com"
admin_password = "3232Lhf@"
if admin_email not in users_df['email'].values:
    users_df = pd.concat([users_df, pd.DataFrame([{"email":admin_email,"name":"Admin","password":admin_password}])], ignore_index=True)
    save_csv(users_df, USERS_CSV)

# -------------------------
# LOAD FOOD DATASET
# -------------------------
try:
    food_df = pd.read_csv(DATA_CSV)
except Exception as e:
    st.error(f"Could not load dataset '{DATA_CSV}': {e}")
    st.stop()

if "code" not in food_df.columns or "Chakula" not in food_df.columns:
    st.error("Dataset MUST contain columns: 'code' and 'Chakula'.")
    st.stop()

# -------------------------
# FOOD GROUPS
# -------------------------
food_groups_sw = {
    "A1": "Nafaka na bidhaa za nafaka",
    "A2": "Vyakula vyenye asili ya nafaka",
    "B1": "Mizizi, Viazi na Ndizi",
    "B2": "Asili ya Mizizi, Viazi na Ndizi",
    "C1": "Maharage, Njugu, Mbegu",
    "C2": "Asili ya maharage na mbegu",
    "D1": "Nyama, Kuku, Samaki",
    "D2": "Asili ya wanyama/ndege",
    "D3": "Maziwa na Bidhaa",
    "E": "Mafuta",
    "F1": "Matunda & Juisi",
    "F2": "Juisi za Matunda",
    "F3": "Mboga",
    "F4": "Asili ya mboga"
}
sw_to_key = {v:k for k,v in food_groups_sw.items()}

# Food-specific color mapping (realistic food colors)
food_group_colors = {
    "A1": {"bg": "linear-gradient(135deg, #FCE38A 0%, #F38181 100%)", "emoji": "🌾", "name": "Nafaka"},  # Bright yellow-orange grains
    "A2": {"bg": "linear-gradient(135deg, #FFDFBA 0%, #FFABAB 100%)", "emoji": "🍞", "name": "Bidhaa za Nafaka"},  # Soft wheat tones
    "B1": {"bg": "linear-gradient(135deg, #FF9A8B 0%, #FF6A88 100%)", "emoji": "🥔", "name": "Mizizi/Viazi"},  # Warm potatoes orange
    "B2": {"bg": "linear-gradient(135deg, #FFD3B6 0%, #FFAAA5 100%)", "emoji": "🍠", "name": "Mizizi Asili"},  # Sweet potato pastel orange
    "C1": {"bg": "linear-gradient(135deg, #FFF59D 0%, #FFE082 100%)", "emoji": "🌽", "name": "Mahabage"},  # Yellow corn
    "C2": {"bg": "linear-gradient(135deg, #FFE0B2 0%, #FFB74D 100%)", "emoji": "🥜", "name": "Njugu"},  # Legumes brown-gold
    "D1": {"bg": "linear-gradient(135deg, #FF6F61 0%, #D84315 100%)", "emoji": "🥩", "name": "Nyama"},  # Red meat
    "D2": {"bg": "linear-gradient(135deg, #FFECB3 0%, #FFD54F 100%)", "emoji": "🍗", "name": "Kuku"},  # Chicken light-golden
    "D3": {"bg": "linear-gradient(135deg, #E1F5FE 0%, #81D4FA 100%)", "emoji": "🥛", "name": "Maziwa"},  # Dairy light blue
    "E": {"bg": "linear-gradient(135deg, #FFF176 0%, #FFC107 100%)", "emoji": "🧈", "name": "Mafuta"},  # Bright oils
    "F1": {"bg": "linear-gradient(135deg, #FF8A80 0%, #D50000 100%)", "emoji": "🍎", "name": "Matunda Nyekundu"},  # Red fruits
    "F2": {"bg": "linear-gradient(135deg, #FFCC80 0%, #FF9800 100%)", "emoji": "🍊", "name": "Matunda Machungwa"},  # Orange fruits
    "F3": {"bg": "linear-gradient(135deg, #A5D6A7 0%, #388E3C 100%)", "emoji": "🥬", "name": "Mboga Zaidi"},  # Green vegetables
    "F4": {"bg": "linear-gradient(135deg, #CE93D8 0%, #7B1FA2 100%)", "emoji": "🍆", "name": "Mboga Nyingi"}  # Purple veggies
}


food_groups_ranges = {
    "A1": [(1,100)], "A2": [(501,550)], "B1": [(351,400)], "B2": [(951,1000)],
    "C1": [(151,200)], "C2": [(651,700)], "D1": [(201,250),(301,350)],
    "D2": [(551,600)], "D3": [(251,300)], "E": [(1101,1150)], "F1": [(101,150)],
    "F2": [(601,650)], "F3": [(401,450)], "F4": [(751,800)]
}

# -------------------------
# HEALTH GOALS
# -------------------------
goal_to_columns = {
    "Kudhibiti Kolesteroli": ["FASAT","FAMS","FAPU","CHOLE","FAT"],
    "Kudhibiti Sukari": ["CHOCDF","SUCS","FIB"],
    "Kupunguza Uzito": ["ENERGY_KC","PROCNT","FAT","CHOCDF","FIB"],
    "Kuongeza Misuli": ["PROCNT","A_PROTEI","MFP_PROT","LEU","ILE","LYS","VAL","ARG"],
    "Kuongeza Stamina": ["ENERGY_KC","PROCNT","FAT","CHOCDF","VIT B6","MG","K"],
    "Usagaji Bora": ["FIB","PHYTAC","NA","K","MG"],
    "Kuongeza Kinga": ["VITC","VITA","A_VITA","VITD","ZN","CU","FE","MFP_FE"],
    "Afya ya Mifupa": ["CA","P","MG","VITD"],
    "Afya ya Moyo": ["FASAT","FAMS","FAPU","NA","K","CHOLE","PROCNT"],
    "Afya ya Ubongo": ["FE","VIT B12","FOL","VIT B6","ILE","LEU","LYS","TYR","PHE","ENERGY_KC"]
}
health_goals = list(goal_to_columns.keys())

# -------------------------
# RECOMMENDATION FUNCTION
# -------------------------
def recommend(goal, selected_group_keys, top_n):
    cols_needed = goal_to_columns.get(goal,[])
    cols_exist = [c for c in cols_needed if c in food_df.columns]
    results={}
    for grp_key in selected_group_keys:
        temp_df=pd.DataFrame()
        for start,end in food_groups_ranges.get(grp_key,[]):
            temp_df=pd.concat([temp_df, food_df[(food_df["code"]>=start) & (food_df["code"]<=end)]], ignore_index=True)
        if temp_df.empty:
            results[grp_key]=pd.DataFrame(columns=["Chakula","score"])
            continue
        if cols_exist:
            temp_df[cols_exist] = temp_df[cols_exist].apply(pd.to_numeric, errors="coerce").fillna(0)
            temp_df["score"] = temp_df[cols_exist].sum(axis=1)
        else:
            temp_df["score"]=0
        ranked = temp_df.sort_values("score",ascending=False)["Chakula"].head(top_n)
        results[grp_key] = ranked.reset_index(drop=True)
    return results

# -------------------------
# STREAMLIT CONFIG
# -------------------------
st.set_page_config(page_title="Food Recommender System", page_icon="🍽️", layout="wide")
if "user" not in st.session_state:
    st.session_state["user"] = None
if "admin" not in st.session_state:
    st.session_state["admin"] = False
if "confirm_logout" not in st.session_state:
    st.session_state["confirm_logout"] = False

st.markdown("""
<style>
/* Background */
body, .stApp {
    background: linear-gradient(135deg, rgba(232,245,233,0.9) 0%, rgba(200,230,201,0.9) 100%);
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #2e7d32 0%, #43a047 100%);
    color: white;
    height: 3em;
    width: 100%;
    border-radius: 15px;
    border: none;
    font-weight: bold;
    box-shadow: 0 4px 12px rgba(46, 125, 50, 0.3);
    transition: all 0.3s ease;
}
.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(46, 125, 50, 0.5);
}

/* Inputs and selects */
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stSelectbox > div > div > div > select {
    height: 2.5em;
    border-radius: 10px;
    border: 2px solid #2e7d32 !important;
    background-color: rgba(255,255,255,0.1) !important;
    color: inherit !important;
    padding: 8px !important;
}

/* Input labels (works in dark mode for all inputs) */
div[class*="stTextInput"] label,
div[class*="stNumberInput"] label,
div[class*="stSelectbox"] label,
div[class*="stMultiSelect"] label {
    color: #2e7d32 !important; /* green visible in dark mode */
    font-weight: bold;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: linear-gradient(90deg, #2e7d32 0%, #43a047 100%);
    border-radius: 12px;
    padding: 5px;
}
.stTabs [data-baseweb="tab"] {
    color: #2e7d32;
    font-weight: bold;
}
.stTabs [data-baseweb="tab"][aria-selected="true"] {
    background: rgba(255,255,255,0.2);
    color: #2e7d32;
}

/* Expander */
.stExpander {
    background: rgba(255,255,255,0.1);
    border: 2px solid #43a047;
    border-radius: 10px;
}

/* Alerts */
.stWarning {background: rgba(255,248,220,0.4) !important; border-left: 5px solid #ff6f61;}
.stSuccess {background: rgba(212,237,218,0.4) !important; border-left: 5px solid #28a745;}
.stInfo {background: rgba(209,236,241,0.4) !important; border-left: 5px solid #17a2b8;}
.stError {background: rgba(248,215,218,0.4) !important; border-left: 5px solid #dc3545;}

/* Checkbox */
.stCheckbox > label {color: #2e7d32; font-weight: bold;}

/* Headers */
h1, h2, h3 {color: #2e7d32 !important; font-weight: bold;}
</style>
""", unsafe_allow_html=True)
# MENU
# -------------------------
menu_options = ["📊 Nyumbani","📜 Historia Yangu","📝 Mrejesho","🚪 Ondoka"]
menu_choice = st.sidebar.selectbox(" Menu/Maorodhesho", menu_options)

# Logout confirmation UI (triggered from sidebar or menu)
if st.session_state.get("confirm_logout"):
    st.warning("⚠️ Una uhakika unataka kuondoka?")
    col_yes, col_no = st.columns(2)
    if col_yes.button("✅ Ndiyo, Ondoka", key="confirm_yes"):
        st.session_state['user'] = None
        st.session_state['confirm_logout'] = False
        st.success("✅ Umeonekana vizuri!")
        try:
            st.rerun()
        except Exception:
            pass
    if col_no.button("❌ Ghairi", key="confirm_no"):
        st.session_state['confirm_logout'] = False
        try:
            st.rerun()
        except Exception:
            pass

# If logged in, show basic account panel with logout
if st.session_state.get("user"):
    user_email = st.session_state.get("user")
    user_row = users_df[users_df['email'].str.strip().str.lower()==user_email.strip().lower()]
    user_name = user_row.iloc[0]['name'] if not user_row.empty else user_email
    with st.sidebar.expander("👤 Akaunti", expanded=True):
        st.markdown(f"👤 **{user_name}**\n\n📧 {user_email}")
        if st.button("🚪 Ondoka", key="sidebar_logout"):
            st.session_state['confirm_logout'] = True
            try:
                st.rerun()
            except Exception:
                pass

# Show login/register controls in the sidebar when no user is logged in
if not st.session_state["user"]:
    with st.sidebar.expander("🔑 Ingia / ✍️ Jisajili", expanded=True):
        tabs = st.tabs(["🔑Ingia", "✍️ Jisajili"])
        # --- Login tab ---
        with tabs[0]:
            login_email = st.text_input("📧 Barua Pepe", key="login_email")
            login_password = st.text_input("🔐 Nenosiri", type="password", key="login_password")
            if st.button("🔑 Bonyeza kungia", key="btn_login"):
                if not login_email or not login_password:
                    st.error("❌ Tafadhali ingiza barua pepe na nenosiri")
                else:
                    matched = users_df[(users_df['email'].str.strip().str.lower()==login_email.strip().lower()) & (users_df['password']==login_password)]
                    if not matched.empty:
                        st.session_state['user'] = login_email.strip().lower()
                        st.success("✅ Umeingia vizuri")
                        try:
                            st.rerun()
                        except Exception:
                            pass
                    else:
                        st.error("❌ Jina mtumiaji au nenosiri sio sahihi")

        # --- Register tab ---
        with tabs[1]:
            reg_name = st.text_input("👤 Jina", key="reg_name")
            reg_email = st.text_input("📧 Barua Pepe", key="reg_email")
            reg_password = st.text_input("🔐 Nenosiri", type="password", key="reg_password")
            if st.button("✍️ Jisajili", key="btn_register"):
                if not (reg_name and reg_email and reg_password):
                    st.error("❌ Tafadhali jaza sehemu zote")
                elif reg_email.strip().lower() in users_df['email'].str.lower().values:
                    st.warning("⚠️ Barua pepe hii tayari imesajiliwa")
                else:
                    new_row = pd.DataFrame([{"email": reg_email.strip().lower(), "name": reg_name.strip(), "password": reg_password}])
                    users_df = pd.concat([users_df, new_row], ignore_index=True)
                    save_csv(users_df, USERS_CSV)
                    # Auto-login after registration
                    st.session_state['user'] = reg_email.strip().lower()
                    st.success("✅ Umesajiliwa na kuingia vizuri")
                    try:
                        st.rerun()
                    except Exception:
                        pass

# -------------------------
# DASHBOARD
# -------------------------
if menu_choice=="📊 Nyumbani":
    if not st.session_state["user"]:
        st.markdown("""
        <div style='background: linear-gradient(135deg, rgba(46, 125, 50, 0.8), rgba(67, 160, 71, 0.8)), url("https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=800"); background-size: cover; background-position: center; padding: 40px; border-radius: 15px; text-align: center; margin-bottom: 20px; box-shadow: 0 8px 20px rgba(46, 125, 50, 0.3);'>
            <h1 style='color: white; margin: 0; text-shadow: 2px 2px 4px rgba(0,0,0,0.5);'>🥗 Karibu ndugu mgeni katika mfumo wa kupendekeza vyakula</h1>
            <p style='color: white; font-size: 18px; text-shadow: 1px 1px 3px rgba(0,0,0,0.5);'>Mfumo huu unahitaji baadhi ya taarifa zako za mwili na lengo pendwa la afya yako, kisha utapata vyakula vyanye virutubisho husika kwa wingi kwa lengo hilo</p>
            <p style='color: white; font-size: 18px; text-shadow: 1px 1px 3px rgba(0,0,0,0.5);'>Mfumo huu una malengo kumi ya kiafya, ambapo mapendekezo ya vyakula yameangalia kiasi cha virutubisho husika kwa ajili ya lengo na kuchukua  chakula chenye kiasi kingi </p>
            <p style='color: white; font-size: 18px; text-shadow: 1px 1px 3px rgba(0,0,0,0.5);'>Tafadhali bonyeza alama hii >> iliyopo hapo juu, ili uweze kuona sehemu ya usajili na huduma zingine</p>
            </div>
        """, unsafe_allow_html=True)
        # CSS for food card fade-in animation (dashboard decorations)
        st.markdown("""
        <style>
        .food-card{box-shadow:0 6px 16px rgba(46,125,50,0.25);border-radius:15px;padding:30px 10px;text-align:center;margin-bottom:10px;color:white;font-weight:bold;transition:opacity 0.6s ease, transform 0.6s ease;opacity:0;transform:translateY(12px);animation:fadeIn 0.6s forwards;}
        @keyframes fadeIn{from{opacity:0;transform:translateY(12px);}to{opacity:1;transform:translateY(0);}}
        .food-emoji{font-size:32px;margin-bottom:8px;display:block}
        </style>
        """, unsafe_allow_html=True)
        
    else:
        user_email = st.session_state["user"]
        user_row = users_df[users_df['email'].str.strip().str.lower()==user_email.strip().lower()]
        user_name = user_row.iloc[0]['name'] if not user_row.empty else user_email
        st.markdown(
            f"""
            <div style='background: linear-gradient(135deg, rgba(46, 125, 50, 0.85), rgba(67, 160, 71, 0.85)), url("https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=800"); background-size: cover; background-position: center; padding: 40px; border-radius: 15px; text-align: center; margin-bottom: 20px; box-shadow: 0 8px 20px rgba(46, 125, 50, 0.4);'>
                <h1 style='color: white; margin: 0; text-shadow: 2px 2px 4px rgba(0,0,0,0.5);'>🍽️ KARIBU,NDUGU {str.upper(user_name)}</h1>
                <p style='color: white; font-size: 16px; margin: 10px 0 0 0; text-shadow: 1px 1px 3px rgba(0,0,0,0.5);'>Tafadhali jaza taarifa zako ili upate mapendekezo ya vyakula</p>
            </div>
            """, unsafe_allow_html=True
        )
        # User Inputs
       
        st.markdown("<h3>Taarifa Zinazoonekana si halisi,tafadhali weka taarifa zako</h3>", unsafe_allow_html=True)
        weight = st.number_input("⚖️ Uzito (kg)",20.0,200.0,60.0)
        height_m = st.number_input("📏 Urefu (m)",1.0,2.5,1.7)
        age = st.number_input("🎂 Umri",5,120,25)
        sex = st.selectbox("🚻 Jinsia",["Me","Ke"])
        activity = st.selectbox("🏃 Kiwango cha Shughuli",["hamna kazi","Kidogo","Kawaida","kazi ya wakati wote","kazi ngumu sana"])
        goal = st.selectbox("🎯 Lengo la Afya",health_goals)
        groups_sw = st.multiselect("🥬 Makundi/Aina ya Vyakula", list(food_groups_sw.values()))
        top_n = st.number_input("🍽️ Idadi ya vyakula kwa kila kundi ulilochagua",1,50,5)

        colors = {
            "A1":"#FFE0B2","A2":"#FFD180","B1":"#FFCC80","B2":"#FFB74D",
            "C1":"#D1C4E9","C2":"#B39DDB","D1":"#C8E6C9","D2":"#A5D6A7",
            "D3":"#81C784","E":"#FF8A65","F1":"#FFF59D","F2":"#FFF176",
            "F3":"#AED581","F4":"#9CCC65"
        }

        if st.button("🥑 Bonyeza hapa kupata vyakula pendekezwa kwa ajili yako", use_container_width=True):
            if not groups_sw:
                st.warning("⚠️ Chagua angalau kikundi au vikundi vya vyakula!")
            else:
                selected_keys = [sw_to_key[s] for s in groups_sw if s in sw_to_key]
                results = recommend(goal, selected_keys, int(top_n))
                # Extract sex value from Swahili display
                sex_code = sex[0]  # "M - Mume" -> "M", "F - Mwanamke" -> "F"
                # Map Swahili activity to English
                activity_map = {"hamna kazi": "Sedentary", "Kidogo": "Light", "Kawaida": "Moderate", "kazi ya wakati wote": "Very Active", "Kazi ngumu zaidi": "Extra Active"}
                activity_eng = activity_map.get(activity, "Moderate")
                # Calculate metabolic metrics
                bmi = calculate_bmi(weight, height_m)
                bmr = calculate_bmr(weight, round(height_m*100), age, sex_code)
                tdee = calculate_tdee(bmr, activity_eng)
                new_rows=[]
                
                for grp_key, table in results.items():
                    color_info = food_group_colors.get(grp_key, {"bg": "linear-gradient(135deg, #81c784 0%, #66bb6a 100%)", "emoji": "🥘"})
                    st.markdown(f"### {color_info['emoji']} {grp_key} - {food_groups_sw.get(grp_key,'')}")
                    col1,col2,col3 = st.columns(3)
                    for i, food_name in enumerate(table.tolist()):
                        col = [col1,col2,col3][i%3]
                        img_path = f"images/{food_name}.jpg"
                        delay = round((i % 9) * 0.12, 2)
                        if os.path.exists(img_path):
                            col.markdown(
                                f"""
                                <div class='food-card' style="background-image: url('{img_path}'); background-size: cover; background-position: center; animation-delay: {delay}s;">
                                    <div style='background:rgba(0,0,0,0.25);padding:18px;border-radius:12px;'>✨ {food_name} ✨</div>
                                </div>
                                """, unsafe_allow_html=True
                            )
                        else:
                            bg_gradient = color_info["bg"]
                            emoji = color_info["emoji"]
                            col.markdown(
                                f"<div class='food-card' style='background: {bg_gradient}; animation-delay: {delay}s;'><span class=\"food-emoji\">{emoji}</span><div style=\"font-size:14px;margin-top:6px\">{food_name}</div></div>", unsafe_allow_html=True
                            )
                            # Save recommendation with new schema
                        row = food_df[food_df["Chakula"]==food_name].iloc[0]
                        protein = get_nutrient_value(row,"PROCNT")
                        fiber = get_nutrient_value(row,"FIB")
                        omega3 = get_nutrient_value(row,"FAPU") if "FAPU" in row else 0
                        vitc = get_nutrient_value(row,"VITC") if "VITC" in row else 0
                        calories = get_nutrient_value(row,"ENERGY_KC") if "ENERGY_KC" in row else 0
                        new_rows.append({
                            "email":user_email,"age":age,"sex":sex_code,"bmi":bmi,"bmr":bmr,
                            "tdee":tdee,"food":food_name,"rating":pd.NA,
                            "protein_g":protein,"fiber_g":fiber,"omega3_g":omega3,
                            "vitC_mg":vitc,"calories_kc":calories,"date":str(datetime.now())
                        })
                        
                
                if new_rows:
                    recommended_meals = ",".join([r["food"] for r in new_rows])
                    new_general_row = {
                        "Barua Pepe": user_email,
                        "Jina": user_name,
                        "Jinsia": sex_code,
                        "Urefu": height_m,
                        "Uzito": weight,
                        "BMI": bmi,
                        "TDEE": tdee,
                        "Lengo la Afya": goal,
                        "Vyakula Vilivyopendekezwa": recommended_meals,
                        "Vyakula Vilivyotumika": pd.NA,
                        "Ukadiriaji wa Maendeleo ya Lengo": pd.NA,
                        "Maelezo ya Maendeleo": pd.NA,
                        "Tarehe ya Pendekezo": str(datetime.now())
                    }
                    general_df = pd.concat([general_df, pd.DataFrame([new_general_row])], ignore_index=True)
                    save_csv(general_df, GENERAL_DATASET)
                    st.success(f"✅ Pendekezo limehifadhiwa kwa lengo: {goal}")
                    st.success(f"Tafadhali tunaomba mrejesho wako baada ya siku 14 kuhusu {goal}")

                    # Allow immediate forwarding of recommendations to user's email
                    foods_text = "\n".join([r["food"] for r in new_rows])
                    if st.button("📤 Tuma mapendekezo haya kwenda Barua Pepe yako", key=f"send_now_{goal}"):
                        if send_email(user_email,f"Mapendekezo ya Vyakula ({goal})",foods_text):
                            st.success("📧 Barua pepe imetumwa vizuri!")
                        else:
                            st.error("❌ Barua pepe haijatumwa. Jaribu tena.")

                    if st.checkbox("📧 Tuma mapendekezo kwa Barua Pepe"):
                        if send_email(user_email,f"Mapendekezo ya Vyakula ({goal})",foods_text):
                            st.success("📧 Barua pepe imetumwa vizuri!")
                        else:
                            st.error("❌ Barua pepe haijatumwa. Jaribu tena.")

# -------------------------
# MY HISTORY
# -------------------------
elif menu_choice=="📜 Historia Yangu":
    if not st.session_state["user"]:
        st.warning("🔒 Tafadhali ingia kwanza!")
    else:
        user_email = st.session_state["user"]
        st.markdown(
            """
            <div style='background: linear-gradient(135deg, rgba(46, 125, 50, 0.85), rgba(67, 160, 71, 0.85)), url("https://images.unsplash.com/photo-1495521821757-a1efb6729352?w=800"); background-size: cover; background-position: center; padding: 40px; border-radius: 15px; text-align: center; margin-bottom: 20px; box-shadow: 0 8px 20px rgba(46, 125, 50, 0.4);'>
                <h1 style='color: white; margin: 0; text-shadow: 2px 2px 4px rgba(0,0,0,0.5);'>📜 Historia Yangu</h1>
                <p style='color: white; font-size: 16px; margin: 10px 0 0 0; text-shadow: 1px 1px 3px rgba(0,0,0,0.5);'>Tazama mapendekezo yako ya awali</p>
            </div>
            """, unsafe_allow_html=True
        )
        general_df = pd.read_csv(GENERAL_DATASET, dtype=str)

        # sanitize email column
        general_df["Barua Pepe"] = general_df["Barua Pepe"].str.strip().str.lower()

        # sanitize logged-in email
        user_email = user_email.strip().lower()

        user_history = general_df[general_df["Barua Pepe"]==user_email]
        if not user_history.empty:
            # Sort by date descending to show most recent first
            user_history = user_history.sort_values(by='Tarehe ya Pendekezo', ascending=False)
            st.markdown("<h3>🍽️ Vyakula Vya Hapo Awali</h3>", unsafe_allow_html=True)
            st.dataframe(user_history, use_container_width=True)
        else:
            st.info("💡 Bado hakuna historia. Tafadhali pata mapendekezo kwanza!")

# -------------------------
# FEEDBACK
# -------------------------
elif menu_choice=="📝 Mrejesho":
    st.markdown(
        """
        <div style='background: linear-gradient(135deg, rgba(46, 125, 50, 0.85), rgba(67, 160, 71, 0.85)), url("https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=800"); background-size: cover; background-position: center; padding: 40px; border-radius: 15px; text-align: center; margin-bottom: 20px; box-shadow: 0 8px 20px rgba(46, 125, 50, 0.4);'>
            <h1 style='color: white; margin: 0; text-shadow: 2px 2px 4px rgba(0,0,0,0.5);'>📝 Toa Mrejesho</h1>
            <p style='color: white; font-size: 16px; margin: 10px 0 0 0; text-shadow: 1px 1px 3px rgba(0,0,0,0.5);'>Shiriki kutoa mrejesho</p>
        </div>
        """, unsafe_allow_html=True
    )
    if not st.session_state["user"]:
        st.warning("🔒 Tafadhali ingia kwanza!")
    else:
        user_email = st.session_state["user"]
        # Filter eligible recommendations: date >= 1 minute ago and foods_used is NA
        now = pd.Timestamp.now()
        eligible = general_df[(general_df['Barua Pepe'] == user_email) & (pd.to_datetime(general_df['Tarehe ya Pendekezo'], errors='coerce') + pd.Timedelta(minutes=1) <= now) & general_df['Vyakula Vilivyotumika'].isna()]
        if eligible.empty:
            st.info("💡subiri dakika 1 ziishe utoe mrejesho.")
        else:
            st.markdown("<h3>🍽️ Chagua Mapendekezo ya Kutoa Mrejesho</h3>", unsafe_allow_html=True)
            for idx, row in eligible.iterrows():
                with st.expander(f"Mapendekezo ya {row['Lengo la Afya']} - {row['Tarehe ya Pendekezo']}"):
                    recommended_foods = row['Vyakula Vilivyopendekezwa'].split(',')
                    eaten_foods = st.multiselect("🥘 Vyakula Uliyokula", recommended_foods, key=f"eaten_{idx}")
                    rating = st.selectbox("⭐ Toa ubora wa  maendeleo (0=Sio Sahihi ... 4=Nzuri Sana)", [0,1,2,3,4], key=f"rating_{idx}")
                    description = st.text_area("💬 Maelezo ya Maendeleo", key=f"desc_{idx}")
                    if st.button("✅ Tuma Maoni", key=f"submit_{idx}"):
                        if not eaten_foods:
                            st.warning("⚠️ Chagua angalau chakula kimoja ulichokula!")
                        else:
                            general_df.at[idx, 'Vyakula Vilivyotumika'] = ','.join(eaten_foods)
                            general_df.at[idx, 'Ukadiriaji wa Maendeleo ya Lengo'] = rating
                            general_df.at[idx, 'Maelezo ya Maendeleo'] = description
                            save_csv(general_df, GENERAL_DATASET)
                            st.success("✅ Maoni yamesave!")
                            st.rerun()

# -------------------------
# LOGOUT
# -------------------------
elif menu_choice=="🚪 Ondoka":
    if not st.session_state.get("user"):
        st.info("ℹ️ Hujaingia kwa sasa.")
    else:
        # trigger the shared confirmation UI
        st.session_state['confirm_logout'] = True
        try:
            st.rerun()
        except Exception:
            pass

# -------------------------
# ADMIN SECTION
# -------------------------
if st.session_state["user"]==admin_email:
    st.sidebar.markdown("<h3 style='color: #ff6f61;'>👨‍💼 Admin Panel</h3>", unsafe_allow_html=True)
    with st.sidebar.expander("📊 Download Data", expanded=False):
        st.markdown("<h4>ML Datasets</h4>", unsafe_allow_html=True)
        st.download_button("📥 general_dataset.csv", general_df.to_csv(index=False), file_name="general_dataset.csv")
        st.download_button("📥 users.csv", users_df.to_csv(index=False), file_name="users.csv")
        st.download_button("📥 VYAKULA.csv", food_df.to_csv(index=False), file_name="VYAKULA.csv")

    with st.sidebar.expander("👥 Manage Users", expanded=False):
        st.markdown("### Users Data")
        edited_users = st.data_editor(users_df, num_rows="dynamic", use_container_width=True)
        if st.button("💾 Save Users Changes"):
            edited_users.to_csv(USERS_CSV, index=False)
            st.success("Users data saved successfully!")
            # Reload
            users_df = pd.read_csv(USERS_CSV)
            st.rerun()

    with st.sidebar.expander("📊 Manage General Data", expanded=False):
        st.markdown("### General Data")
        edited_general = st.data_editor(general_df, num_rows="dynamic", use_container_width=True)
        if st.button("💾 Save General Changes"):
            edited_general.to_csv(GENERAL_DATASET, index=False)
            st.success("General data saved successfully!")
            # Reload
            general_df = pd.read_csv(GENERAL_DATASET)
            st.rerun()

    with st.sidebar.expander("🥘 Manage Food Data", expanded=False):
        st.markdown("### Food Data (Caution: Main Dataset)")
        edited_food = st.data_editor(food_df, num_rows="dynamic", use_container_width=True)
        if st.button("💾 Save Food Changes"):
            edited_food.to_csv(DATA_CSV, index=False)
            st.success("Food data saved successfully!")
            # Reload
            food_df = pd.read_csv(DATA_CSV)
            st.rerun()














