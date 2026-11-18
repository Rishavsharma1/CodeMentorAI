
import streamlit as st

from modules.test_generator import generate_and_run_tests


st.set_page_config(
    page_title="Test Generator | CodeMentor AI",
    page_icon="🧪",
    layout="wide"
)

st.title("🧪 AI Test Case Generator")

st.write(
    "Generate Python test cases automatically using Ollama "
    "and execute them inside an isolated Docker container."
)

st.info(
    "Generated tests are executed using Docker with networking disabled "
    "and resource limits enabled."
)

st.divider()

st.subheader("Enter Your Python Code")

code = st.text_area(
    "Paste your Python function or program below:",
    height=250,
    placeholder="def add_numbers(a, b):\n    return a + b"
)

if st.button("Generate and Run Tests", type="primary"):

    if not code.strip():

        st.warning("Please enter some Python code first.")

    else:

        try:

            with st.spinner(
                "Ollama is generating tests and Docker is executing them..."
            ):

                result = generate_and_run_tests(code)

            if result is None:

                st.error(
                    "Test generation failed. "
                    "Check the terminal for more details."
                )

            else:

                st.divider()

                st.subheader("Test Execution Results")

                if result["success"]:

                    st.success("All generated tests passed!")

                else:

                    st.error(
                        "Some generated tests failed "
                        "or Docker execution was unsuccessful."
                    )

                if result.get("output"):

                    st.markdown("### Pytest Output")

                    st.code(
                        result["output"],
                        language="text"
                    )

                if result.get("error"):

                    st.markdown("### Additional Error Information")

                    st.code(
                        result["error"],
                        language="text"
                    )

        except Exception as error:

            st.error(f"An unexpected error occurred: {error}")

st.divider()

st.caption(
    "CodeMentor AI | AI-powered Python Test Generator | Docker Sandbox"
)
