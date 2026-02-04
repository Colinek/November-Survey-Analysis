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
    summary:hover { color: #2980b9; background: #f9f9f9; }
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

# --- CONFIGURATION: YOUR FACULTY DEFINITIONS ---
# This maps the "Official" names you gave me.
# The script will try to match the CSV subjects to these lists.
FACULTY_DEFS = {
    "English & Languages": ["English", "Media", "Gaelic", "French", "Gàidhlig", "Drama", "Literacy"],
    "Maths": ["Maths", "Mathematics", "Applications"],
    "Health & Wellbeing": ["PE", "Physical Education", "Sport", "Health", "Food", "Home Economics", "Cookery"],
    "Science": ["Physics", "Biology", "Chemistry", "Science"],
    "Music, Computing & Business": ["Business", "Admin", "IT", "Music", "Computing", "Computer"],
    "Social Subjects": ["Classical", "Geography", "History", "Politics", "Modern Studies"],
    "Technical": ["Woodwork", "Art", "Design", "Graphic", "Engineering", "Technical", "Textiles", "Fashion"],
    "PSE": ["PSE", "Personal"]
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
        try:
            df = pd.read_csv(file, encoding='utf-8-sig')
        except:
            df = pd.read_csv(file, encoding='ISO-8859-1')
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        st.error(f"Error reading file: {e}")
        return None

def find_column(df, keywords):
    for col in df.columns:
        if any(k in col.lower() for k in keywords):
            return col
    return None

def assign_faculty(subject_name):
    """Matches a subject string to your Faculty list."""
    s_clean = str(subject_name).lower()
    for faculty, keywords in FACULTY_DEFS.items():
        for k in keywords:
            if k.lower() in s_clean:
                return faculty
    return "Other / Unassigned"

def map_stage(year):
    y = str(year).strip().upper()
    if 'S1' in y or 'S2' in y: return 'S1 & S2'
    if 'S3' in y: return 'S3'
    if any(k in y for k in ['S4', 'S5', 'S6']): return 'Senior Phase'
    return 'Other'

def calc_pos_rate(series):
    valid = series.dropna().astype(str).str.lower().str.strip()
    if valid.empty: return 0.0
    pos_count = valid.isin(['agree', 'strongly agree']).sum()
    return (pos_count / len(valid)) * 100

# --- MAIN APP ---
st.title("🏫 Faculty Analyzer")
st.write("Upload your **Form Responses** CSV file.")

uploaded_file = st.sidebar.file_uploader("Upload Survey Data (CSV)", type="csv")

if uploaded_file is not None:
    df = load_data(uploaded_file)
    
    if df is not None:
        # 1. Identify Columns
        year_col = find_column(df, ['year group', 'grade', 'stage'])
        subject_col = find_column(df, ['which subject', 'subject answering'])
        
        if not year_col or not subject_col:
            st.error("❌ Columns Not Found. Please upload the raw responses file.")
            st.stop()
            
        df.rename(columns={year_col: 'Year Group', subject_col: 'Subject'}, inplace=True)
        df['Subject'] = df['Subject'].astype(str).str.strip()
        df['Stage'] = df['Year Group'].apply(map_stage)
        
        # 2. Assign Faculties
        df['Faculty'] = df['Subject'].apply(assign_faculty)

        # --- SIDEBAR CONFIG ---
        st.sidebar.header("1. Select Group")
        
        # A. Select Faculty
        all_faculties = sorted([f for f in df['Faculty'].unique() if f != "Other / Unassigned"])
        # Add 'Other' to the end if it exists
        if "Other / Unassigned" in df['Faculty'].unique():
            all_faculties.append("Other / Unassigned")
            
        selected_faculty = st.sidebar.selectbox("Choose Faculty", all_faculties)
        
        # Filter to just this faculty for the next steps
        faculty_df = df[df['Faculty'] == selected_faculty]
        available_subjects = sorted(faculty_df['Subject'].unique())
        
        # B. Select Target (The "Checkboxes" request)
        st.sidebar.header("2. Analysis Focus")
        st.sidebar.info(f"Select which subjects in **{selected_faculty}** you want to analyze.")
        
        target_subjects = st.sidebar.multiselect(
            "Select Subjects:",
            options=available_subjects,
            default=available_subjects # Default to "Whole Faculty"
        )
        
        if not target_subjects:
            st.warning("Please select at least one subject.")
            st.stop()
            
        # C. Select Stage
        all_stages = ['All Years', 'S1 & S2', 'S3', 'Senior Phase']
        selected_stage = st.sidebar.selectbox("Year Group Filter", all_stages)
        
        # D. Benchmark
        st.sidebar.header("3. Benchmark")
        # Logic: If they selected ALL subjects in faculty, compare to school.
        # If they selected a SUBSET (e.g. just Physics), allow comparing to Faculty Average.
        
        is_whole_faculty = set(target_subjects) == set(available_subjects)
        
        bench_options = ["Whole School Average"]
        if not is_whole_faculty:
            bench_options.append("Whole Faculty Average")
            
        compare_mode = st.sidebar.radio("Compare against:", bench_options)

        # --- FILTER DATA ---
        
        # 1. Filter by Stage (applies to everything)
        if selected_stage != "All Years":
            active_df = df[df['Stage'] == selected_stage]
        else:
            active_df = df

        if active_df.empty:
            st.warning(f"No data found for {selected_stage}.")
            st.stop()

        # 2. Define Target Data (The subjects selected in the checkbox)
        target_df = active_df[active_df['Subject'].isin(target_subjects)]
        
        if target_df.empty:
            st.error("No responses found for this selection in this Year Group.")
            st.stop()

        # 3. Define Benchmark Data
        if compare_mode == "Whole School Average":
            benchmark_df = active_df
            bench_label = "Whole School"
        else:
            # Benchmark is the WHOLE faculty (all available subjects)
            benchmark_df = active_df[active_df['Subject'].isin(available_subjects)]
            bench_label = f"{selected_faculty} Average"

        # --- DASHBOARD ---
        
        # Dynamic Title
        if is_whole_faculty:
            display_title = f"{selected_faculty} (Whole Faculty)"
        elif len(target_subjects) == 1:
            display_title = target_subjects[0]
        else:
            display_title = "Selected Subjects (Custom Group)"

        col1, col2, col3 = st.columns(3)
        col1.metric("Analysis Target", display_title)
        col2.metric("Year Group", selected_stage)
        col3.metric("Responses", len(target_df))
        
        st.markdown(f"**Comparing against:** {bench_label} ({len(benchmark_df)} responses)")
        st.markdown("---")

        # --- GENERATE CARDS ---
        col_map = {}
        for cat, prefixes in CATEGORIES.items():
            col_map[cat] = [col for col in df.columns if any(col.startswith(p) for p in prefixes)]

        html_output = ""
        for cat, questions in col_map.items():
            if not questions: continue
            
            # Calculations
            subj_vals = target_df[questions].values.flatten()
            bench_vals = benchmark_df[questions].values.flatten()
            s_score = calc_pos_rate(pd.Series(subj_vals))
            b_score = calc_pos_rate(pd.Series(bench_vals))
            diff = s_score - b_score
            
            color = "#2980b9" # Blue
            diff_html = ""
            if diff > 5:
                color = "#27ae60" # Green
                diff_html = f"<span class='diff-badge diff-green'>+{int(diff)}%</span>"
            elif diff < -5:
                color = "#c0392b" # Red
                diff_html = f"<span class='diff-badge diff-red'>{int(diff)}%</span>"

            html_output += f"""
            <div class="card">
                <h3>{cat}</h3>
                <div class="bar-container">
                    <div class="label"><span>Category Score {diff_html}</span><span>{int(s_score)}%</span></div>
                    <div class="track">
                        <div class="bar bar-school" style="width: {b_score}%"></div>
                        <div class="bar bar-subject" style="width: {s_score}%; background: {color};"></div>
                    </div>
                </div>
                <details><summary>▼ Breakdown by Question</summary>
            """
            
            for q in questions:
                q_s_score = calc_pos_rate(target_df[q])
                q_b_score = calc_pos_rate(benchmark_df[q])
                q_text = q.strip('"') 
                
                html_output += f"""
                <div class="q-container">
                    <span class="q-text">{q_text}</span>
                    <div class="q-track">
                        <div class="q-bar-school" style="width: {q_b_score}%"></div>
                        <div class="q-bar-subject" style="width: {q_s_score}%"></div>
                    </div>
                    <div class="q-stats">You: {int(q_s_score)}% | {bench_label}: {int(q_b_score)}%</div>
                </div>
                """
            html_output += "</details></div>"

        st.markdown(html_output, unsafe_allow_html=True)
        
        st.info("""
        **Legend:**
        🟦 **Blue:** Broadly in line (+/- 5%) | 
        🟩 **Green:** Significant Strength (> +5%) | 
        🟥 **Red:** Significant Concern (< -5%)
        """)

else:
    st.info("Please upload your **Form Responses CSV** to begin.")
