
# import streamlit as st

# from modules.test_generator import generate_and_run_tests


# st.set_page_config(
#     page_title="Test Generator | CodeMentor AI",
#     page_icon="🧪",
#     layout="wide"
# )

# st.title("🧪 AI Test Case Generator")

# st.write(
#     "Generate Python test cases automatically using Ollama "
#     "and execute them inside an isolated Docker container."
# )

# st.info(
#     "Generated tests are executed using Docker with networking disabled "
#     "and resource limits enabled."
# )

# st.divider()

# st.subheader("Enter Your Python Code")

# code = st.text_area(
#     "Paste your Python function or program below:",
#     height=250,
#     placeholder="def add_numbers(a, b):\n    return a + b"
# )

# if st.button("Generate and Run Tests", type="primary"):

#     if not code.strip():

#         st.warning("Please enter some Python code first.")

#     else:

#         try:

#             with st.spinner(
#                 "Ollama is generating tests and Docker is executing them..."
#             ):

#                 result = generate_and_run_tests(code)

#             if result is None:

#                 st.error(
#                     "Test generation failed. "
#                     "Check the terminal for more details."
#                 )

#             else:

#                 st.divider()

#                 st.subheader("Test Execution Results")

#                 if result["success"]:

#                     st.success("All generated tests passed!")

#                 else:

#                     st.error(
#                         "Some generated tests failed "
#                         "or Docker execution was unsuccessful."
#                     )

#                 if result.get("output"):

#                     st.markdown("### Pytest Output")

#                     st.code(
#                         result["output"],
#                         language="text"
#                     )

#                 if result.get("error"):

#                     st.markdown("### Additional Error Information")

#                     st.code(
#                         result["error"],
#                         language="text"
#                     )

#         except Exception as error:

#             st.error(f"An unexpected error occurred: {error}")

# st.divider()

# st.caption(
#     "CodeMentor AI | AI-powered Python Test Generator | Docker Sandbox"
# )



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

                # --------------------------------------
                # 1. Display originally generated tests
                # --------------------------------------

                st.subheader("📝 Generated Test Cases")

                generated_code = result.get("generated_test_code", "")

                if generated_code:

                    st.code(
                        generated_code,
                        language="python"
                    )

                    st.download_button(
                        "Download Generated Tests",
                        data=generated_code,
                        file_name="generated_tests.py",
                        mime="text/x-python"
                    )

                else:

                    st.warning("Generated test code is unavailable.")

                # --------------------------------------
                # 2. Display repaired tests if available
                # --------------------------------------

                if result.get("was_repaired"):

                    st.divider()

                    st.subheader("🔧 Repaired Test Cases")

                    repaired_code = result.get(
                        "repaired_test_code",
                        ""
                    )

                    if repaired_code:

                        st.code(
                            repaired_code,
                            language="python"
                        )

                    else:

                        st.warning("Repaired test code is unavailable.")

                # --------------------------------------
                # 3. Display final execution status
                # --------------------------------------

                st.divider()

                st.subheader("🧪 Test Execution Results")

                if result["success"]:

                    st.success("All executed tests passed!")

                else:

                    st.error(
                        "Some tests failed or Docker execution "
                        "was unsuccessful."
                    )

                # --------------------------------------
                # 4. Display pytest output
                # --------------------------------------

                if result.get("output"):

                    st.markdown("### Pytest Output")

                    st.code(
                        result["output"],
                        language="text"
                    )

                # --------------------------------------
                # 5. Display additional errors
                # --------------------------------------

                if result.get("error"):

                    st.markdown("### Additional Error Information")

                    st.code(
                        result["error"],
                        language="text"
                    )

                # --------------------------------------
                # 6. Display repair error if applicable
                # --------------------------------------

                if result.get("repair_error"):

                    st.warning("Automatic test repair was unsuccessful.")

                    st.code(
                        result["repair_error"],
                        language="text"
                    )

        except Exception as error:

            st.error(f"An unexpected error occurred: {error}")

st.divider()

st.caption(
    "CodeMentor AI | AI-powered Python Test Generator | Docker Sandbox"
)
