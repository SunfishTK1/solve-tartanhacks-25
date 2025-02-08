import streamlit as st
import requests
import threading
import time

# -------------------------------
# Helper function: recursively display questions with a toggle.
# -------------------------------
def display_questions(questions, indent=0, parent_key=""):
    for i, q in enumerate(questions):
        # Create a unique key for each question.
        unique_key = f"{parent_key}_{i}" if parent_key else str(i)
        with st.expander(q.get("question", "Question"), expanded=False):
            st.markdown(q.get("result", "No answer available."))
            # If there are subquestions, show a checkbox to toggle their display.
            if q.get("other_questions"):
                toggle_key = f"toggle_{unique_key}"
                show_sub = st.checkbox("Show subquestions", key=toggle_key)
                if show_sub:
                    # Use HTML to add left margin for visual indentation.
                    st.markdown(f"<div style='margin-left: {indent * 20 + 20}px;'>", unsafe_allow_html=True)
                    display_questions(q["other_questions"], indent=indent+1, parent_key=unique_key)
                    st.markdown("</div>", unsafe_allow_html=True)

# -------------------------------
# Function to call the API in a thread.
# -------------------------------
def call_api(company, industry, result_container):
    """
    Call the /analyze endpoint with the provided company and industry.
    The JSON result is stored in the shared dictionary (result_container).
    """
    api_url = "http://localhost:8007/analyze"
    payload = {"company_name": company, "industry": industry}
    try:
        response = requests.post(api_url, json=payload)
        response.raise_for_status()
        result_container["data"] = response.json()
    except Exception as e:
        result_container["error"] = str(e)

# -------------------------------
# Main Streamlit App
# -------------------------------
st.set_page_config(page_title="Due Diligence Analysis", layout="wide")
st.title("Company Due Diligence Analysis")
st.markdown("Enter the details of the company you wish to analyze and click submit.")

# User inputs for company name and industry.
company_name = st.text_input("Company Name", placeholder="e.g., Millies Coffee and Creamery")
industry = st.text_input("Industry", placeholder="e.g., Food & Beverage")

# Button to trigger analysis.
if st.button("Submit Analysis"):
    if not company_name:
        st.error("Please enter a company name.")
    else:
        # Create a container for the API result.
        result_container = {"data": None, "error": None}
        
        # Start the API call in a separate thread.
        thread = threading.Thread(target=call_api, args=(company_name, industry, result_container))
        thread.start()

        # Display a dynamic loading message while the thread is running.
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

        # Check for any error from the API call.
        if result_container.get("error"):
            st.error(f"Error calling API: {result_container['error']}")
        else:
            result = result_container.get("data", {})
            full_report = result.get("full report", "No report available.")
            # Assume the first line is the title and the rest is the abstract.
            lines = full_report.split("\n")
            if lines:
                title_line = lines[0]
                abstract_text = "\n".join(lines[1:]).strip()
            else:
                title_line = "Report"
                abstract_text = full_report

            # Display company name, title, and abstract.
            st.header(title_line)
            st.subheader(f"Analysis for {company_name}")
            st.markdown("### Abstract Summary")
            st.write(abstract_text)

            # Display subquestions if available.
            subquestions = result.get("subquestions", [])
            if subquestions:
                st.markdown("## Due Diligence Questions")
                display_questions(subquestions)
            else:
                st.info("No subquestions returned.")

# Optional: display instructions if no submission yet.
if not company_name:
    st.info("Please enter the company details and click the submit button to begin analysis.")
