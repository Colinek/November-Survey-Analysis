# --- HELPER FUNCTIONS ---
@st.cache_data
def load_data(file):
    try:
        # Try reading with different encodings to handle Excel weirdness
        try:
            df = pd.read_csv(file, encoding='utf-8-sig') # Handles BOM
        except:
            df = pd.read_csv(file, encoding='ISO-8859-1') # Fallback for Windows
            
        # Clean all column names (remove spaces, make lowercase for searching)
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        st.error(f"Error reading file: {e}")
        return None

def find_column(df, keywords):
    """Finds a column that contains any of the keywords."""
    for col in df.columns:
        if any(k in col.lower() for k in keywords):
            return col
    return None

# ... (Keep map_stage and calc_pos_rate functions as they are) ...

# --- MAIN APP ---
st.title("🏫 School Survey Analyzer")
st.write("Upload your **Form Responses** CSV file.")

uploaded_file = st.sidebar.file_uploader("Upload Survey Data (CSV)", type="csv")

if uploaded_file is not None:
    df = load_data(uploaded_file)
    
    if df is not None:
        # --- SMART COLUMN DETECTION ---
        # We look for columns containing specific words instead of exact matches
        year_col = find_column(df, ['year group', 'grade', 'stage'])
        subject_col = find_column(df, ['which subject', 'subject answering'])
        
        # Check if we found them
        if not year_col or not subject_col:
            st.error("❌ **Columns Not Found**")
            st.write("The script could not identify the 'Year Group' or 'Subject' columns.")
            st.write("Please check you uploaded the **Raw Responses** file, not the Summary/Percentages file.")
            st.write("Columns found in your file:", list(df.columns))
            st.stop()
            
        # Rename them to standard names so the rest of the script works
        df.rename(columns={year_col: 'Year Group', subject_col: 'Subject'}, inplace=True)
        
        # Clean the subject column data
        df['Subject'] = df['Subject'].astype(str).str.strip()
        
        # Create 'Stage' column safely
        df['Stage'] = df['Year Group'].apply(map_stage)
        
        # --- (The rest of the script remains exactly the same) ---
        # Get Lists for Dropdowns
        all_subjects = sorted(df['Subject'].unique())
        all_stages = ['All Years', 'S1 & S2', 'S3', 'Senior Phase']

        # --- SIDEBAR ---
        st.sidebar.header("⚙️ Configuration")
        target_subject = st.sidebar.selectbox("Select Subject to Analyze", all_subjects)
        target_stage = st.sidebar.selectbox("Select Year Group", all_stages)
        compare_mode = st.sidebar.radio("Compare Against:", ["Whole School Average", "Faculty Average"])
        
        faculty_subjects = []
        if compare_mode == "Faculty Average":
            faculty_subjects = st.sidebar.multiselect("Select Subjects in Faculty", all_subjects, default=[target_subject])
            if not faculty_subjects:
                st.sidebar.warning("Please select at least one subject.")

        # --- FILTERING ---
        if target_stage != "All Years":
            df_stage = df[df['Stage'] == target_stage]
        else:
            df_stage = df

        if df_stage.empty:
            st.warning(f"No data found for {target_stage}.")
            st.stop()

        # Define Benchmark
        if compare_mode == "Whole School Average":
            benchmark_df = df_stage
            bench_name = "Whole School"
        else:
            if not faculty_subjects: st.stop()
            benchmark_df = df_stage[df_stage['Subject'].isin(faculty_subjects)]
            bench_name = "Faculty Average"

        # Define Target Subject
        subject_df = df_stage[df_stage['Subject'] == target_subject]

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

        # --- GENERATE CARDS ---
        col_map = {}
        for cat, prefixes in CATEGORIES.items():
            col_map[cat] = [col for col in df.columns if any(col.startswith(p) for p in prefixes)]

        html_output = ""
        for cat, questions in col_map.items():
            if not questions: continue
            
            # Big Bar Maths
            subj_vals = subject_df[questions].values.flatten()
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
                q_s_score = calc_pos_rate(subject_df[q])
                q_b_score = calc_pos_rate(benchmark_df[q])
                q_text = q.strip('"') 
                
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

        st.markdown(html_output, unsafe_allow_html=True)
        
        st.info("""
        **Legend:**
        🟦 **Blue:** Broadly in line (+/- 5%) | 
        🟩 **Green:** Significant Strength (> +5%) | 
        🟥 **Red:** Significant Concern (< -5%)
        """)

else:
    st.info("Please upload your **Form Responses CSV** to begin.")
