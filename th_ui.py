import streamlit as st
import requests
import threading
import time

# Inject custom CSS for your Angular-style UI and for a modal/popover.
st.markdown("""
<style>
.chat-container {
  text-align: center;
  font-family: 'Inter', sans-serif;
  margin-top: 50px;
  color: #082c54;
}
.input-box, .stTextInput>div>div>input {
  width: 60%;
  padding: 12px;
  margin: 10px auto;
  border-radius: 8px;
  border: 1px solid #082c54;
  font-size: 16px;
  display: block;
  color: #082c54;
}
.checkbox-container {
  margin-top: 20px;
  text-align: left;
  display: inline-block;
  color: #082c54;
}
.checkbox-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}
.checkbox-grid label {
  display: flex;
  align-items: center;
  color: #082c54;
}
input[type="checkbox"] {
  margin-right: 8px;
  accent-color: #082c54;
}
.submit-button {
  margin-top: 20px;
  background-color: #082c54;
  color: white;
  padding: 12px 20px;
  font-size: 16px;
  border: none;
  border-radius: 10px;
  cursor: pointer;
}
.submit-button:hover {
  background-color: #001f3f;
}
</style>
""", unsafe_allow_html=True)

# Wrap all content in a container div
st.markdown('<div class="chat-container">', unsafe_allow_html=True)
st.markdown("<h1>Company Analysis</h1>", unsafe_allow_html=True)

# -------------------------------
# User Inputs
# -------------------------------
company_name = st.text_input("", placeholder="Enter company name(s)", key="company_name")
industry = ""
if company_name:
    industry = st.text_input("", placeholder="Enter the industry", key="industry")

promptOptions = [
    'Operations and Management',
    'Market Risks',
    'Competitor Analysis',
    'Potential Concerns',
    'Industry Benchmarks',
    'Legal Standing'
]

selectedPrompts = []
if industry:
    st.markdown('<div class="checkbox-container">', unsafe_allow_html=True)
    st.markdown("<h2>Select Analysis Topics:</h2>", unsafe_allow_html=True)
    cols = st.columns(2)
    for i, prompt in enumerate(promptOptions):
        col = cols[i % 2]
        if col.checkbox(prompt, key=f"checkbox_{i}"):
            selectedPrompts.append(prompt)
    st.markdown('</div>', unsafe_allow_html=True)

submit_clicked = False
if industry:
    submit_clicked = st.button("Submit", key="submit", help="Submit Analysis")

# -------------------------------
# Helper function to display questions
# -------------------------------
def display_questions(questions, depth=1, parent_key=""):
    for i, q in enumerate(questions):
        unique_key = f"{parent_key}_{i}" if parent_key else str(i)
        # For main questions, use an expander.
        if depth == 1:
            with st.expander(q.get("question", "Question"), expanded=False):
                st.markdown(q.get("result", "No answer available."))
                if q.get("other_questions"):
                    st.markdown("**Subquestions:**")
                    for j, sub_q in enumerate(q["other_questions"]):
                        # Render each subquestion using st.popover.
                        with st.popover(sub_q.get("question", "Subquestion")):
                            st.markdown("**Question:**")
                            st.write(sub_q.get("question", "No question provided."))
                            st.markdown("**Answer:**")
                            st.write(sub_q.get("result", "No answer available."))
        # For nested subquestions (depth >= 2), also use st.popover.
        else:
            with st.popover(q.get("question", "Question")):
                st.markdown("**Question:**")
                st.write(q.get("question", "No question provided."))
                st.markdown("**Answer:**")
                st.write(q.get("result", "No answer available."))
                if q.get("other_questions"):
                    st.markdown("<div style='margin-left: 20px;'>", unsafe_allow_html=True)
                    display_questions(q["other_questions"], depth=depth+1, parent_key=unique_key)
                    st.markdown("</div>", unsafe_allow_html=True)

# -------------------------------
# Function to call the API in a separate thread.
# -------------------------------
def call_api(company, industry, prompts, result_container):
    api_url = "http://localhost:8007/analyze"
    payload = {
        "company_name": company,
        "industry": industry,
        "prompts": prompts
    }
    try:
        response = requests.post(api_url, json=payload)
        response.raise_for_status()
        result_container["data"] = response.json()
    except Exception as e:
        result_container["error"] = str(e)

# -------------------------------
# Process submission and display results
# -------------------------------
if submit_clicked:
    if not company_name:
        st.error("Please enter a company name.")
    else:
        result_container = {"data": None, "error": None}
        thread = threading.Thread(target=call_api, args=(company_name, industry, selectedPrompts, result_container))
        thread.start()

        # Dynamic loading message with rotating phrases.
        loading_placeholder = st.empty()
        loading_phrases = [
            "Analyzing company data...",
            "Crunching numbers...",
            "Gathering insights...",
            "Almost done..."
        ]
        i = 0
        while thread.is_alive():
            loading_placeholder.text(loading_phrases[i % len(loading_phrases)])
            time.sleep(0.5)
            i += 1
        thread.join()
        loading_placeholder.empty()

        if result_container.get("error"):
            st.error(f"Error calling API: {result_container['error']}")
        else:
            result = result_container.get("data", {})
            full_report = result.get("full report", "No report available.")
            lines = full_report.split("\n")
            if lines:
                title_line = lines[0]
                abstract_text = "\n".join(lines[1:]).strip()
            else:
                title_line = "Report"
                abstract_text = full_report

            st.header(title_line)
            st.subheader(f"Analysis for {company_name}")
            st.markdown("### Abstract Summary")
            st.write(abstract_text)

            subquestions = result.get("subquestions", [])
            if subquestions:
                st.markdown("## Due Diligence Questions")
                display_questions(subquestions)
            else:
                st.info("No subquestions returned.")

# (The previous modal popup code based on st.session_state has been removed.)

# End the container div.
st.markdown('</div>', unsafe_allow_html=True)
