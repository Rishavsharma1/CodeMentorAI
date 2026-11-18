
import streamlit as st

from modules.retriever import CodeRetriever


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Code Search | CodeMentor AI",
    page_icon="🔎",
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

st.title("🔎 Semantic Code Search")

st.write(
    "Search the programming dataset using natural language. "
    "CodeMentor AI retrieves relevant Python questions and "
    "their corresponding code examples."
)

st.info(
    "Search uses Sentence Transformers, FAISS and hybrid "
    "ranking with semantic similarity and keyword overlap."
)

st.divider()


# --------------------------------------------------
# SEARCH INPUT
# --------------------------------------------------

st.subheader("Search Programming Examples")

query = st.text_area(
    "Describe the code you are looking for:",
    height=110,
    placeholder=(
        "Example: Python function to check whether "
        "a number is prime."
    )
)

top_k = st.slider(
    "Number of results:",
    min_value=1,
    max_value=10,
    value=5
)


# --------------------------------------------------
# PERFORM SEARCH
# --------------------------------------------------

if st.button("Search Code Examples", type="primary"):

    if not query.strip():

        st.warning("Please enter a search query.")

    else:

        try:

            with st.spinner("Loading code retrieval system..."):
                retriever = load_retriever()

            with st.spinner("Searching the FAISS vector database..."):

                results = retriever.search(
                    query,
                    top_k=top_k
                )

            st.session_state["search_results"] = results
            st.session_state["search_query"] = query

        except Exception as error:

            st.error(
                f"Code search failed: {error}"
            )


# --------------------------------------------------
# DISPLAY SEARCH RESULTS
# --------------------------------------------------

if "search_results" in st.session_state:

    results = st.session_state["search_results"]

    st.divider()

    st.subheader("Search Results")

    st.write(
        f"Query: **{st.session_state['search_query']}**"
    )

    if not results:

        st.warning(
            "No matching code examples were found."
        )

    else:

        st.success(
            f"Found {len(results)} relevant code examples."
        )

        for index, result in enumerate(results, start=1):

            with st.expander(
                f"Result {index} | "
                f"Combined Score: "
                f"{result['combined_score']:.4f}",
                expanded=(index == 1)
            ):

                st.markdown("**Original Question**")

                st.write(result["question"])

                st.markdown("**Python Code**")

                st.code(
                    result["code"],
                    language="python"
                )

                st.markdown("**Relevance Scores**")

                col1, col2, col3 = st.columns(3)

                col1.metric(
                    "Semantic Similarity",
                    f"{result['similarity_score']:.4f}"
                )

                col2.metric(
                    "Keyword Score",
                    f"{result['keyword_score']:.4f}"
                )

                col3.metric(
                    "Combined Score",
                    f"{result['combined_score']:.4f}"
                )

        # --------------------------------------------------
        # DOWNLOAD RESULTS
        # --------------------------------------------------

        export_text = ""

        for index, result in enumerate(results, start=1):

            export_text += (
                f"RESULT {index}\n"
                f"{'=' * 50}\n"
                f"Question: {result['question']}\n\n"
                f"Code:\n{result['code']}\n\n"
                f"Semantic Score: {result['similarity_score']:.4f}\n"
                f"Keyword Score: {result['keyword_score']:.4f}\n"
                f"Combined Score: {result['combined_score']:.4f}\n\n"
            )

        st.download_button(
            label="Download Search Results",
            data=export_text,
            file_name="code_search_results.txt",
            mime="text/plain"
        )


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.divider()

st.caption(
    "CodeMentor AI | FAISS-powered Hybrid Code Search"
)
