
import streamlit as st

from modules.code_analyzer import analyze_code, debug_code


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Debugger | CodeMentor AI",
    page_icon="🐛",
    layout="wide"
)


# --------------------------------------------------
# PAGE HEADER
# --------------------------------------------------

st.title("🐛 AI Python Debugger")

st.write(
    "Paste your Python code to identify syntax errors, "
    "potential code-quality issues and receive AI-assisted "
    "debugging suggestions."
)

st.info(
    "CodeMentor AI combines Python AST analysis with "
    "Qwen2.5 to explain errors and suggest corrections."
)

st.divider()


# --------------------------------------------------
# CODE INPUT
# --------------------------------------------------

st.subheader("Enter Python Code")

code = st.text_area(
    "Paste your Python code below:",
    height=280,
    placeholder=(
        "def add_numbers(a, b):\n"
        "    return a + b"
    )
)


# --------------------------------------------------
# DEBUG BUTTON
# --------------------------------------------------

if st.button("Analyze and Debug Code", type="primary"):

    if not code.strip():

        st.warning("Please enter Python code first.")

    else:

        # --------------------------------------------------
        # STATIC ANALYSIS
        # --------------------------------------------------

        with st.spinner("Analyzing Python syntax and code quality..."):

            analysis = analyze_code(code)

        st.session_state["debug_analysis"] = analysis

        st.divider()

        st.subheader("Static Analysis Results")

        if analysis["valid"]:

            st.success("Python syntax is valid.")

        else:

            st.error("Python syntax error detected.")

        if analysis["syntax_error"]:

            error = analysis["syntax_error"]

            st.write(f"**Error:** {error['message']}")
            st.write(f"**Line:** {error['line']}")
            st.write(f"**Column:** {error['column']}")

        if analysis["issues"]:

            st.warning("Potential code issues detected.")

            for issue in analysis["issues"]:

                st.write(
                    f"- **{issue['type']}**: "
                    f"{issue['message']} "
                    f"(Line {issue['line']})"
                )

        elif analysis["valid"]:

            st.info(
                "No issues detected by the current static checks."
            )

        # --------------------------------------------------
        # AI DEBUGGING
        # --------------------------------------------------

        with st.spinner(
            "Qwen is analyzing the code and suggesting corrections..."
        ):

            response = debug_code(code)

        if response.startswith("Error communicating with Ollama:"):

            st.error(response)

        else:

            st.session_state["debug_response"] = response

            st.success("AI debugging analysis completed!")


# --------------------------------------------------
# DISPLAY AI DEBUGGING RESPONSE
# --------------------------------------------------

if st.session_state.get("debug_response"):

    st.divider()

    st.subheader("AI Debugging Suggestions")

    st.markdown(
        st.session_state["debug_response"]
    )

    st.download_button(
        label="Download Debugging Report",
        data=st.session_state["debug_response"],
        file_name="debugging_report.txt",
        mime="text/plain"
    )


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.divider()

st.caption(
    "CodeMentor AI | Python AST Analysis and AI Debugging"
)
