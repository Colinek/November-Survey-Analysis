import streamlit as st
import pandas as pd

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Faculty Analyzer", layout="wide", page_icon="🏫")

# --- CSS STYLING ---
st.markdown("""
<style>
    .card { background: white; padding: 20px; margin-bottom: 20px; border-radius: 10px; border: 1px solid #e0e0e0; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    h3 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 5px; margin-top: 0; font-size: 1.2rem; }
    .bar-container { margin: 15px 0 5px 0; }
    .label { display: flex; justify-content: space-between; font-weight: 700; margin-bottom: 5px; font-size: 14px; color: #444; }
    .track { background: #ecf0f1; height: 25px; border-radius: 12px; overflow: hidden; position: relative; }
    .bar { height: 100%; position: absolute; top: 0; left: 0; border-radius: 12px; transition: width 0.5s; }
    .bar-school { background: #95a5a6; z-index: 1; opacity: 0.3; }
    .bar-subject { background: #2980b9; z-index: 2; }
    details { margin-bottom: 10px; border: 1px solid #eee; border-radius: 5px; padding: 5px; }
    summary { cursor: pointer; color: #555; font-weight: 600; padding: 5px; outline: none; }
    .q-container { margin: 10px 0 10px 10px; border-left: 3px solid #eee; padding-left: 10px; }
    .q-text { font-size: 0.85em; color: #666; margin-bottom: 3px; display: block; }
    .q-track { background: #f0f0f0; height: 8px; border-radius: 4px; width: 100%; position: relative; overflow: hidden; }
    .q-bar-school { height: 100%; background: #bdc3c7; position: absolute; opacity: 0.5; }
    .q-bar-subject { height: 100%; background: #3498db; position: absolute; }
    .q-stats { font-size: 0.75em; color: #888; margin-top: 2px; }
    .diff-badge { font-size: 0.8em; padding: 2px 6px; border-radius: 4px; margin-left: 8px; color: white; }
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

# --- FUNCTIONS ---
@st.cache_data
def load_data(file):
    # List of encodings to try in order of likelihood
    encodings = ['utf-8-sig', 'latin1', 'cp1252', 'utf-16']
    
    for enc in encodings:
        try:
            # Re-seek to the start of the file for each attempt
            file.seek(0)
            df = pd.read_csv(file, encoding=enc, sep=None, engine='python')
            
            # Clean up headers
            df.columns = [str(c).strip().replace('\ufeff', '') for c in df.columns]
            
            # If it loaded successfully, return it
            return df
        except (UnicodeDecodeError, Exception):
            continue # Try the next encoding
            
    # If all fail, show the error
    st.error("❌ Failed to read the file. It may be in an unsupported format or corrupted.")
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
        # --- COLUMN DETECTION & OVERRIDE ---
        st.sidebar.subheader("📍 Data Mapping")
        
        # Try auto-detecting first
        auto_year = find_column(df, ['year group', 'group', 'stage'])
        auto_subj = find_column(df, ['which subject', 'subject answering', 'subject today'])
        
        # UI for Column Selection (Pre-filled with auto-detection)
        year_col = st.sidebar.selectbox("Select Year Group Column:", df.columns, 
                                       index=list(df.columns).index(auto_year) if auto_year in df.columns else 0)
        
        subj_col = st.sidebar.selectbox("Select Subject Column:", df.columns, 
                                       index=list(df.columns).index(auto_subj) if auto_subj in df.columns else 0)

        # Apply mapping
        df['Mapped_Year'] = df[year_col]
        df['Mapped_Subj'] = df[subj_col].astype(str).str.strip()

        # Define Stages
        def get_stage(y):
            y = str(y).upper()
            if 'S1' in y or 'S2' in y: return 'S1 & S2'
            if 'S3' in y: return 'S3'
            return 'Senior Phase' if any(s in y for s in ['S4','S5','S6']) else 'Other'
        
        df['Stage'] = df['Mapped_Year'].apply(get_stage)
        df['Faculty'] = df['Mapped_Subj'].apply(assign_faculty)

        # --- SELECTION FILTERS ---
        st.sidebar.divider()
        fac_list = sorted(df['Faculty'].unique())
        sel_fac = st.sidebar.selectbox("1. Choose Faculty", fac_list)
        
        fac_subjects = sorted(df[df['Faculty'] == sel_fac]['Mapped_Subj'].unique())
        sel_subjects = st.sidebar.multiselect("2. Select Subjects (Checkboxes)", fac_subjects, default=fac_subjects)
        
        sel_stage = st.sidebar.selectbox("3. Year Group Filter", ['All Years', 'S1 & S2', 'S3', 'Senior Phase'])
        
        is_whole_fac = set(sel_subjects) == set(fac_subjects)
        bench_opts = ["Whole School"] + (["Faculty Average"] if not is_whole_fac else [])
        sel_bench = st.sidebar.radio("4. Compare Against", bench_opts)

        # --- DATA FILTERING ---
        active_df = df if sel_stage == 'All Years' else df[df['Stage'] == sel_stage]
        target_df = active_df[active_df['Mapped_Subj'].isin(sel_subjects)]
        
        if sel_bench == "Whole School":
            bench_df = active_df
        else:
            bench_df = active_df[active_df['Faculty'] == sel_fac]

        if target_df.empty:
            st.warning("No data found for this selection.")
        else:
            # --- DASHBOARD UI ---
            c1, c2, c3 = st.columns(3)
            c1.metric("Focus", sel_fac if is_whole_fac else "Selected Subjects")
            c2.metric("Year", sel_stage)
            c3.metric("Responses", len(target_df))
            st.write(f"**Benchmark:** {sel_bench} ({len(bench_df)} responses)")

            html_output = ""
            for cat, prefixes in CATEGORIES.items():
                cat_cols = [c for c in df.columns if any(c.startswith(p) for p in prefixes)]
                if not cat_cols: continue
                
                s_score = calc_pos_rate(pd.Series(target_df[cat_cols].values.flatten()))
                b_score = calc_pos_rate(pd.Series(bench_df[cat_cols].values.flatten()))
                diff = s_score - b_score
                
                color = "#2980b9"
                badge = ""
                if diff > 5: color, badge = "#27ae60", f"<span class='diff-badge diff-green'>+{int(diff)}%</span>"
                elif diff < -5: color, badge = "#c0392b", f"<span class='diff-badge diff-red'>{int(diff)}%</span>"

                html_output += f"""
                <div class="card">
                    <h3>{cat} {badge}</h3>
                    <div class="bar-container">
                        <div class="label"><span>Category Average</span><span>{int(s_score)}%</span></div>
                        <div class="track">
                            <div class="bar bar-school" style="width: {b_score}%"></div>
                            <div class="bar bar-subject" style="width: {s_score}%; background: {color};"></div>
                        </div>
                    </div>
                    <details><summary>▼ Breakdown by Question</summary>
                """
                for q in cat_cols:
                    qs, qb = calc_pos_rate(target_df[q]), calc_pos_rate(bench_df[q])
                    html_output += f"""
                    <div class="q-container">
                        <span class="q-text">{q}</span>
                        <div class="q-track"><div class="q-bar-school" style="width:{qb}%"></div><div class="q-bar-subject" style="width:{qs}%"></div></div>
                        <div class="q-stats">You: {int(qs)}% | Bench: {int(qb)}%</div>
                    </div>"""
                html_output += "</details></div>"
            
            st.markdown(html_output, unsafe_allow_html=True)
else:
    st.info("Please upload your survey CSV to begin.")
