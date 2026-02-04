import streamlit as st
import pandas as pd

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="School Survey Analyzer", layout="wide", page_icon="📊")

# --- CSS STYLING (The same style you liked) ---
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
    
    /* Collapsible Styles */
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

# --- CATEGORY DEFINITIONS ---
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
        df = pd.read_csv(file, encoding='ISO-8859-1')
        df.columns = df.columns.str.strip()
        subj_col = 'Which subject are you answering these questions about today?'
        df[subj_col] = df[subj_col].astype(str).str.strip()
        return df
    except Exception as e:
        st.error(f"Error reading file: {e}")
        return None

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

st.title("🏫 School Survey Analyzer")
st.write("Upload your CSV file to generate interactive reports.")

# 1. FILE UPLOAD
uploaded_file = st.sidebar.file_uploader("Upload Survey Data (CSV)", type="csv")

if uploaded_file is not None:
    df = load_data(uploaded_file)
    
    if df is not None:
        # Preprocessing
        subj_col = 'Which subject are you answering these questions about today?'
        df['Stage'] = df['Which Year Group are you in?'].apply(map_stage)
        
        # Get Lists for Dropdowns
        all_subjects = sorted(df[subj_col].unique())
        all_stages = ['All Years', 'S1 & S2', 'S3', 'Senior Phase']

        # --- SIDEBAR CONTROLS ---
        st.sidebar.header("⚙️ Configuration")
        
        # Select Subject
        target_subject = st.sidebar.selectbox("Select Subject to Analyze", all_subjects)
        
        # Select Year Group
        target_stage = st.sidebar.selectbox("Select Year Group", all_stages)
        
        # Comparison Mode
        compare_mode = st.sidebar.radio("Compare Against:", ["Whole School Average", "Faculty Average"])
        
        faculty_subjects = []
        if compare_mode == "Faculty Average":
            faculty_subjects = st.sidebar.multiselect(
                "Select Subjects in Faculty", 
                all_subjects, 
                default=[target_subject]
            )
            if not faculty_subjects:
                st.sidebar.warning("Please select at least one subject for the Faculty.")

        # --- DATA FILTERING ---
        
        # 1. Filter by Stage (for both Subject and Benchmark)
        if target_stage != "All Years":
            df_stage = df[df['Stage'] == target_stage]
        else:
            df_stage = df # Use full dataset

        if df_stage.empty:
            st.warning(f"No data found for {target_stage}.")
            st.stop()

        # 2. Define the Benchmark Data
        if compare_mode == "Whole School Average":
            benchmark_df = df_stage # Benchmark is everyone
            bench_name = "Whole School"
        else:
            # Benchmark is only the selected faculty subjects
            if not faculty_subjects:
                st.stop()
            benchmark_df = df_stage[df_stage[subj_col].isin(faculty_subjects)]
            bench_name = "Faculty Average"

        # 3. Define the Target Subject Data
        subject_df = df_stage[df_stage[subj_col] == target_subject]

        if subject_df.empty:
            st.error(f"No responses found for **{target_subject}** in **{target_stage}**.")
            st.stop()

        # --- DASHBOARD HEADER ---
        col1, col2, col3 = st.columns(3)
        col1.metric("Target Subject", target_subject)
        col2.metric("Year Group", target_stage)
        col3.metric("Responses", len(subject_df))

        st.markdown(f"**Comparing against:** {bench_name} ({len(benchmark_df)} responses)")
        st.markdown("---")

        # --- GENERATE REPORT CARDS ---
        
        # Map Columns
        col_map = {}
        for cat, prefixes in CATEGORIES.items():
            col_map[cat] = [col for col in df.columns if any(col.startswith(p) for p in prefixes)]

        # Generate HTML for each Category
        html_output = ""
        
        for cat, questions in col_map.items():
            # Calculate Category Averages
            # Note: We flatten all question answers into one big series for the category average
            subj_vals = subject_df[questions].values.flatten()
            bench_vals = benchmark_df[questions].values.flatten()
            
            # Convert back to Series to use our calc function
            s_score = calc_pos_rate(pd.Series(subj_vals))
            b_score = calc_pos_rate(pd.Series(bench_vals))
            
            diff = s_score - b_score
            
            # Colors & Badges
            color = "#2980b9" # Blue
            diff_html = ""
            if diff > 5:
                color = "#27ae60" # Green
                diff_html = f"<span class='diff-badge diff-green'>+{int(diff)}%</span>"
            elif diff < -5:
                color = "#c0392b" # Red
                diff_html = f"<span class='diff-badge diff-red'>{int(diff)}%</span>"

            # Start Card
            html_output += f"""
            <div class="card">
                <h3>{cat}</h3>
                
                <div class="bar-container">
                    <div class="label">
                        <span>Category Score {diff_html}</span>
                        <span>{int(s_score)}%</span>
                    </div>
                    <div class="track">
                        <div class="bar bar-school" style="width: {b_score}%"></div>
                        <div class="bar bar-subject" style="width: {s_score}%; background: {color};"></div>
                    </div>
                </div>
                
                <details>
                    <summary>▼ Breakdown by Question</summary>
            """
            
            # Loop individual questions
            for q in questions:
                q_s_score = calc_pos_rate(subject_df[q])
                q_b_score = calc_pos_rate(benchmark_df[q])
                q_text = q.strip('"') # Clean quotes
                
                html_output += f"""
                <div class="q-container">
                    <span class="q-text">{q_text}</span>
                    <div class="q-track">
                        <div class="q-bar-school" style="width: {q_b_score}%"></div>
                        <div class="q-bar-subject" style="width: {q_s_score}%"></div>
                    </div>
                    <div class="q-stats">You: {int(q_s_score)}% | {bench_name}: {int(q_b_score)}%</div>
                </div>
                """
            
            html_output += "</details></div>"

        # Render the HTML
        st.markdown(html_output, unsafe_allow_html=True)
        
        # Legend
        st.info("""
        **Legend:**
        🟦 **Blue:** Broadly in line (+/- 5%) | 
        🟩 **Green:** Significant Strength (> +5%) | 
        🟥 **Red:** Significant Concern (< -5%)
        """)

else:
    st.info("Please upload a CSV file to begin.")
