import streamlit as st
import pandas as pd

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Faculty Analyzer", layout="wide", page_icon="🏫")

# --- CSS STYLING ---
st.markdown("""
<style>
    /* Card Styling */
    .card-header { 
        background: white; 
        padding: 15px 20px; 
        border-radius: 10px; 
        border: 1px solid #e0e0e0; 
        box-shadow: 0 2px 4px rgba(0,0,0,0.05); 
        margin-bottom: 10px;
    }
    h3 { color: #2c3e50; font-size: 1.1rem; margin: 0 0 10px 0; padding-bottom: 5px; border-bottom: 2px solid #3498db; }
    
    /* Main Bar Charts */
    .bar-container { margin: 10px 0; }
    .label { display: flex; justify-content: space-between; font-weight: 700; font-size: 14px; color: #444; margin-bottom: 5px; }
    .track { background: #ecf0f1; height: 24px; border-radius: 6px; overflow: hidden; position: relative; }
    .bar { height: 100%; position: absolute; top: 0; left: 0; transition: width 0.5s; }
    .bar-school { background: #95a5a6; z-index: 1; opacity: 0.35; }
    .bar-subject { background: #2980b9; z-index: 2; }

    /* Question Drill Down Charts */
    .q-row { display: flex; align-items: center; margin-bottom: 8px; padding-bottom: 8px; border-bottom: 1px solid #f0f0f0; }
    .q-text { flex: 1; font-size: 0.85em; color: #555; padding-right: 15px; }
    .q-viz { flex: 1; max-width: 50%; }
    .q-track { background: #f0f0f0; height: 12px; border-radius: 4px; position: relative; width: 100%; overflow: hidden; }
    .q-bar-school { height: 100%; background: #bdc3c7; position: absolute; opacity: 0.5; }
    .q-bar-subject { height: 100%; background: #3498db; position: absolute; }
    .q-stats { font-size: 0.7em; color: #888; text-align: right; margin-top: 2px; }

    /* Badges */
    .diff-badge { font-size: 0.8em; padding: 2px 6px; border-radius: 4px; margin-left: 8px; color: white; font-weight: bold; }
    .diff-green { background: #27ae60; }
    .diff-red { background: #c0392b; }
</style>
""", unsafe_allow_html=True)

# --- FACULTY DEFINITIONS ---
FACULTY_DEFS = {
    "English & Languages": ["Media", "Gaelic", "French", "Gàidhlig", "Drama", "Literacy", "English"],
    "Maths": ["Applications of Maths", "Maths", "Mathematics"],
    "Health and Wellbeing": ["Physical Education", "PE", "Sport", "Health & Food", "Home Economics", "Cookery", "Health and Wellbeing"],
    "Science": ["Physics", "Biology", "Chemistry", "Science"],
    "Music, Computing and Business": ["Business", "Music", "Administration", "Computing", "Comp Sci"],
    "Social Subjects": ["Classical Studies", "Geography", "History", "Politics", "Modern Studies"],
    "Technical": ["Woodwork", "Art and Design", "Graphic Communication", "Engineering Science", "Technical", "Textiles", "Fashion"],
    "PSE": ["PSE", "Personal and Social Education"]
}

CATEGORIES = {
    "1. Climate & Mindset": ["1 ", "13 ", "14 "],
    "2. Pedagogy & Challenge": ["4 ", "5 ", "8 ", "9 "],
    "3. Clarity & Communication": ["2 ", "3 ", "11 "],
    "4. Support & Feedback": ["6 ", "7 ", "10 ", "12 "]
}

# --- HELPER FUNCTIONS ---
@st.cache_data
def load_data(file):
    try:
        df = pd.read_csv(file, encoding='utf-8-sig', sep=None, engine='python')
        df.columns = [str(c).strip().replace('\ufeff', '') for c in df.columns]
        return df
    except Exception as e:
        st.error(f"Error reading file: {e}")
        return None

def find_column(df, keywords):
    for col in df.columns:
        if any(k in col.lower() for k in keywords):
            return col
    return None

def assign_faculty(subj):
    s_clean = str(subj).lower()
    for fac, keywords in FACULTY_DEFS.items():
        if any(k.lower() in s_clean for k in keywords):
            return fac
    return "Other"

def calc_pos_rate(series):
    valid = series.dropna().astype(str).str.lower().str.strip()
    if valid.empty: return 0.0
    return (valid.isin(['agree', 'strongly agree']).sum() / len(valid)) * 100

# --- MAIN APP ---
st.title("🏫 Faculty Analyzer")
uploaded_file = st.sidebar.file_uploader("Upload Survey CSV", type="csv")

if uploaded_file:
    df = load_data(uploaded_file)
    if df is not None:
        
        # --- 1. DATA MAPPING (Hidden by default) ---
        with st.sidebar.expander("🔧 Data Mapping (Advanced)"):
            st.caption("If columns aren't finding automatically, fix them here.")
            
            auto_year = find_column(df, ['year group', 'group', 'stage']) or df.columns[0]
            auto_subj = find_column(df, ['which subject', 'subject answering', 'subject today']) or df.columns[1]
            
            year_col = st.selectbox("Year Group Column:", df.columns, index=list(df.columns).index(auto_year))
            subj_col = st.selectbox("Subject Column:", df.columns, index=list(df.columns).index(auto_subj))

        # Apply Mapping
        df['Mapped_Year'] = df[year_col]
        df['Mapped_Subj'] = df[subj_col].astype(str).str.strip()

        # Define Stages
        def get_stage(y):
            y = str(y).upper()
            if 'S1' in y or 'S2' in y: return 'S1 & S2'
            if 'S3'
