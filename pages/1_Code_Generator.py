
import ast
import streamlit as st

from modules.retriever import CodeRetriever
from modules.llm import generate_code_only


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Code Generator | CodeMentor AI",
    page_icon="💻",
    layout="wide"
)


# --------------------------------------------------
# LOAD RETRIEVER
# --------------------------------------------------

@st.cache_resource
def load_retriever():
    return CodeRetriever()


# --------------------------------------------------
# PAGE HEADER
# --------------------------------------------------

st.title("💻 AI Code Generator")

st.write(
    "Describe your programming problem in natural language. "
    "CodeMentor AI retrieves relevant examples and generates "
    "Python code using Retrieval-Augmented Generation (RAG)."
)

st.info(
    "The system uses FAISS for code retrieval and Qwen2.5 "
    "through Ollama for Python code generation."
)

st.divider()


# --------------------------------------------------
# USER INPUT
# --------------------------------------------------

st.subheader("Describe Your Programming Problem")

question = st.text_area(
    "Enter your coding question:",
    height=130,
    placeholder=(
        "Example: Write a Python function to find "
        "the second largest number in a list."
    )
)

function_name = st.text_input(
    "Required function name (optional):",
    placeholder="Example: second_largest"
)

top_k = st.slider(
    "Number of relevant examples to retrieve:",
    min_value=1,
    max_value=5,
    value=3
)


# --------------------------------------------------
# GENERATE CODE
# --------------------------------------------------

if st.button("Generate Python Code", type="primary"):

    if not question.strip():

        st.warning("Please enter a programming question.")

    elif function_name and not function_name.isidentifier():

        st.warning(
            "Please enter a valid Python function name."
        )

    else:

        try:

            with st.spinner("Loading code retrieval system..."):
                retriever = load_retriever()

            with st.spinner("Searching for relevant code examples..."):

                examples = retriever.search(
                    question,
                    top_k=top_k
                )

            st.session_state["code_examples"] = examples

            st.subheader("Retrieved Code Examples")

            if examples:

                for index, example in enumerate(examples, start=1):

                    with st.expander(
                        f"Example {index} "
                        f"(Similarity: "
                        f"{example['similarity_score']:.3f})"
                    ):

                        st.write("**Question:**")
                        st.write(example["question"])

                        st.write("**Code:**")
                        st.code(
                            example["code"],
                            language="python"
                        )

            else:

                st.warning(
                    "No relevant examples were retrieved. "
                    "The model will generate code without examples."
                )

            with st.spinner(
                "Qwen is generating Python code..."
            ):

                generated_code = generate_code_only(
                    question,
                    examples,
                    function_name=function_name.strip() or None
                )

            if not generated_code:

                st.error("The model returned an empty response.")

            elif generated_code.startswith("Error:"):

                st.error(generated_code)

            else:

                st.session_state["generated_code"] = generated_code

                st.success("Code generation completed!")

        except Exception as error:

            st.error(
                f"Code generation failed: {error}"
            )


# --------------------------------------------------
# DISPLAY GENERATED CODE
# --------------------------------------------------

if st.session_state.get("generated_code"):

    st.divider()

    st.subheader("Generated Python Code")

    generated_code = st.session_state["generated_code"]

    st.code(
        generated_code,
        language="python"
    )

    st.download_button(
        label="Download Python Code",
        data=generated_code,
        file_name="generated_code.py",
        mime="text/x-python"
    )

    # --------------------------------------------------
    # BASIC SYNTAX VALIDATION
    # --------------------------------------------------

    st.subheader("Syntax Validation")

    try:

        ast.parse(generated_code)

        st.success(
            "Generated code has valid Python syntax."
        )

    except SyntaxError as error:

        st.error(
            f"Python syntax error: {error}"
        )


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.divider()

st.caption(
    "CodeMentor AI | RAG-powered Python Code Generator"
)
