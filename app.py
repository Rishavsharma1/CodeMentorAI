
import streamlit as st

from modules.retriever import CodeRetriever
from modules.llm import generate_response
from modules.code_analyzer import analyze_code
from modules.sandbox import execute_code


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="CodeMentor AI",
    page_icon="💻",
    layout="wide"
)


# --------------------------------------------------
# INITIALIZE APPLICATION
# --------------------------------------------------

st.title("💻 CodeMentor AI")

st.subheader("Natural-Language Coding Assistant")

st.write(
    "Generate code, understand programming concepts, "
    "debug errors, and search for relevant code examples."
)


# --------------------------------------------------
# LOAD RETRIEVER
# --------------------------------------------------

@st.cache_resource
def load_retriever():
    return CodeRetriever()


try:
    retriever = load_retriever()
    st.success("Code retrieval system loaded successfully!")
except Exception as error:
    retriever = None
    st.error(f"Could not load code retrieval system: {error}")


# --------------------------------------------------
# USER INPUT
# --------------------------------------------------

st.divider()

st.header("Ask CodeMentor AI")

question = st.text_area(
    "Enter your programming question:",
    placeholder="Example: Write Python code to read a CSV file.",
    height=120
)

generate_button = st.button(
    "Generate Code",
    type="primary"
)


# --------------------------------------------------
# CODE GENERATION
# --------------------------------------------------

if generate_button:

    if not question.strip():
        st.warning("Please enter a programming question.")

    elif retriever is None:
        st.error("The code retrieval system is unavailable.")

    else:

        with st.spinner("Searching for relevant code examples..."):

            try:
                retrieved_examples = retriever.search(
                    question,
                    top_k=3
                )

                st.subheader("Retrieved Code Examples")

                for index, example in enumerate(retrieved_examples, 1):

                    with st.expander(f"Example {index}"):

                        st.write(
                            example.get("question", "No question available")
                        )

                        st.code(
                            example.get("snippet", example.get("code", "")),
                            language="python"
                        )

                with st.spinner("Generating code using Qwen..."):

                    response = generate_response(
                        question,
                        retrieved_examples
                    )

                st.session_state["generated_response"] = response

                st.subheader("Generated Response")

                st.markdown(response)

            except Exception as error:
                st.error(f"Code generation failed: {error}")


# --------------------------------------------------
# CODE ANALYSIS AND EXECUTION
# --------------------------------------------------

st.divider()

st.header("Code Analyzer and Docker Executor")

code_input = st.text_area(
    "Paste Python code to analyze or execute:",
    height=220,
    placeholder="def add(a, b):\n    return a + b"
)

col1, col2 = st.columns(2)

with col1:
    analyze_button = st.button("Analyze Code")

with col2:
    execute_button = st.button("Execute in Docker")


if analyze_button:

    if not code_input.strip():
        st.warning("Please enter Python code.")

    else:

        analysis_result = analyze_code(code_input)

        st.subheader("Code Analysis Results")

        if analysis_result["valid"]:
            st.success("Python syntax is valid!")
        else:
            st.error("Syntax error detected.")

        if analysis_result["syntax_error"]:
            st.code(str(analysis_result["syntax_error"]))

        if analysis_result["issues"]:
            st.warning("Potential code quality or security issues:")

            for issue in analysis_result["issues"]:
                st.write(f"- {issue}")

        elif analysis_result["valid"]:
            st.info("No issues detected by the current static checks.")


if execute_button:

    if not code_input.strip():
        st.warning("Please enter Python code.")

    else:

        with st.spinner("Executing code inside Docker sandbox..."):

            execution_result = execute_code(code_input)

        st.subheader("Execution Results")

        if execution_result["success"]:
            st.success("Code executed successfully!")
        else:
            st.error("Code execution failed.")

        st.write("**Output:**")

        st.code(
            execution_result["output"] or "No output produced.",
            language="text"
        )

        if execution_result["error"]:
            st.write("**Error:**")

            st.code(
                execution_result["error"],
                language="text"
            )

        st.write(
            f"**Return Code:** {execution_result['return_code']}"
        )


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.divider()

st.caption(
    "CodeMentor AI | RAG-powered Natural-Language Coding Assistant"
)
