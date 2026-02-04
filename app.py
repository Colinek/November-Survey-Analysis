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
            if 'S3' in y: return 'S3'
            return 'Senior Phase' if any(s in y for s in ['S4','S5','S6']) else 'Other'
        
        df['Stage'] = df['Mapped_Year'].apply(get_stage)
        df['Faculty'] = df['Mapped_Subj'].apply(assign_faculty)

        # --- 2. FACULTY SELECTOR ---
        st.sidebar.divider()
        st.sidebar.header("1. Select Group")
        
        fac_list = sorted([f for f in df['Faculty'].unique() if f != "Other"])
        if "Other" in df['Faculty'].unique(): fac_list.append("Other")
        
        # Store selection in session state to handle resets
        if 'selected_faculty' not in st.session_state: st.session_state.selected_faculty = fac_list[0]
        
        sel_fac = st.sidebar.selectbox("Choose Faculty", fac_list, key='fac_select')
        
        # Get subjects in this faculty
        fac_subjects = sorted(df[df['Faculty'] == sel_fac]['Mapped_Subj'].unique())
        
        # --- 3. SUBJECT FILTER (With Reset) ---
        st.sidebar.header("2. Analysis Focus")
        
        # Reset Button Logic
        if st.sidebar.button("🔄 Reset to Whole Faculty"):
            st.session_state[f"subj_{sel_fac}"] = fac_subjects
            
        sel_subjects = st.sidebar.multiselect(
            "Select Subjects:", 
            fac_subjects, 
            default=fac_subjects,
            key=f"subj_{sel_fac}" # Unique key per faculty preserves state
        )
        
        if not sel_subjects:
            st.warning("Please select at least one subject.")
            st.stop()
            
        # --- 4. BENCHMARK & FILTERS ---
        sel_stage = st.sidebar.selectbox("3. Year Group Filter", ['All Years', 'S1 & S2', 'S3', 'Senior Phase'])
        
        st.sidebar.header("4. Benchmark")
        bench_opts = ["Whole School Average", "Faculty Average", "Department Average"]
        sel_bench = st.sidebar.selectbox("Compare Against:", bench_opts)

        # --- DATA PROCESSING ---
        # 1. Active Data (Stage Filter)
        active_df = df if sel_stage == 'All Years' else df[df['Stage'] == sel_stage]
        
        # 2. Target Data (User Selection)
        target_df = active_df[active_df['Mapped_Subj'].isin(sel_subjects)]
        
        # 3. Benchmark Data
        if sel_bench == "Whole School Average":
            bench_df = active_df # Everyone in that stage
            bench_label = "Whole School"
        elif sel_bench == "Faculty Average":
            # Everyone in the Faculty (regardless of user subject selection)
            bench_df = active_df[active_df['Faculty'] == sel_fac]
            bench_label = f"{sel_fac}"
        else: # Department Average
            # Everyone in the SELECTED subjects (e.g. just French)
            # Note: If looking at S3 French, this compares to S3 French (Self-comparison)
            # Unless we want Dept Average to always be ALL YEARS? 
            # Let's make Dept Average = The chosen subjects across ALL YEARS (if possible) 
            # to show how this year compares to the department norm.
            # actually, standard practice is usually comparing to the same cohort.
            # Let's keep it simple: Department Average = The average of the selected subjects in this stage.
            # If that's the same as target, it's 0 diff. 
            # BETTER: Department Average usually implies "The Subject Average"
            bench_df = df[df['Mapped_Subj'].isin(sel_subjects)] # All years for these subjects
            bench_label = "Dept (All Years)"

        if target_df.empty:
            st.warning("No data found for this selection.")
        else:
            # --- DASHBOARD ---
            c1, c2, c3 = st.columns(3)
            c1.metric("Target", f"{len(sel_subjects)} Subjects" if len(sel_subjects) > 1 else sel_subjects[0])
            c2.metric("Stage", sel_stage)
            c3.metric("Responses", len(target_df))
            st.caption(f"Comparing against: **{bench_label}** ({len(bench_df)} responses)")
            st.divider()

            for cat, prefixes in CATEGORIES.items():
                cat_cols = [c for c in df.columns if any(c.startswith(p) for p in prefixes)]
                if not cat_cols: continue
                
                # Big Bar Maths
                s_score = calc_pos_rate(pd.Series(target_df[cat_cols].values.flatten()))
                b_score = calc_pos_rate(pd.Series(bench_df[cat_cols].values.flatten()))
                diff = s_score - b_score
                
                color = "#2980b9"
                badge = ""
                if diff > 5: color, badge = "#27ae60", f"<span class='diff-badge diff-green'>+{int(diff)}%</span>"
                elif diff < -5: color, badge = "#c0392b", f"<span class='diff-badge diff-red'>{int(diff)}%</span>"

                # 1. RENDER MAIN CARD (HTML)
                st.markdown(f"""
                <div class="card-header">
                    <h3>{cat} {badge}</h3>
                    <div class="bar-container">
                        <div class="label"><span>Category Score</span><span>{int(s_score)}%</span></div>
                        <div class="track">
                            <div class="bar bar-school" style="width: {b_score}%"></div>
                            <div class="bar bar-subject" style="width: {s_score}%; background: {color};"></div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # 2. RENDER DRILL DOWN (Native Expander)
                # We separate this from the HTML block above to fix the rendering issue
                with st.expander(f"▼ Breakdown by Question ({cat})"):
                    q_html = ""
                    for q in cat_cols:
                        qs = calc_pos_rate(target_df[q])
                        qb = calc_pos_rate(bench_df[q])
                        q_text = q.strip('"')
                        
                        q_html += f"""
                        <div class="q-row">
                            <div class="q-text">{q_text}</div>
                            <div class="q-viz">
                                <div class="q-track">
                                    <div class="q-bar-school" style="width:{qb}%"></div>
                                    <div class="q-bar-subject" style="width:{qs}%"></div>
                                </div>
                                <div class="q-stats">You: {int(qs)}% | Bench: {int(qb)}%</div>
                            </div>
                        </div>
                        """
                    st.markdown(q_html, unsafe_allow_html=True)

else:
    st.info("Please upload your survey CSV to begin.")
