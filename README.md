
# CodeMentor AI
### Natural-Language Coding Assistant with Retrieval-Augmented Generation

CodeMentor AI is an AI-powered programming assistant that helps users generate Python code, understand programming examples, debug syntax errors, automatically generate test cases, and search for relevant code snippets using natural language.

The project combines Retrieval-Augmented Generation (RAG), FAISS vector search, Sentence Transformers, Qwen2.5 through Ollama, Python AST analysis, pytest, Docker, and Streamlit.

---

## 1. Project Objectives

- Generate Python code from natural-language programming questions.
- Retrieve relevant programming examples using semantic search.
- Improve code generation using retrieved examples through RAG.
- Identify Python syntax errors and potential code-quality issues.
- Generate and execute automated test cases.
- Execute Python code inside a restricted Docker environment.
- Search programming examples using natural-language queries.

---

## 2. Features

### 2.1 AI Code Generator
- Accepts natural-language programming questions.
- Retrieves relevant code examples from the FAISS vector database.
- Generates Python code using Qwen2.5.
- Supports an optional required function name.
- Performs Python syntax validation.

### 2.2 AI Debugger
- Analyzes Python source code using the AST module.
- Identifies syntax errors and their locations.
- Detects selected code-quality issues.
- Uses Qwen2.5 to explain errors and suggest corrections.

### 2.3 Automated Test Generator
- Generates pytest test cases using an LLM.
- Executes generated tests inside Docker.
- Supports automatic repair and rerunning of failed tests.
- Displays test execution results.

### 2.4 Semantic Code Search
- Accepts natural-language search queries.
- Retrieves similar programming questions and code examples.
- Uses semantic similarity and keyword overlap.
- Ranks results using a hybrid scoring method.

### 2.5 Docker Code Execution
- Executes Python code inside Docker containers.
- Disables container networking.
- Applies memory, CPU and process limits.
- Uses read-only filesystem restrictions and reduced container privileges.
- Enforces execution timeouts.

---

## 3. Technology Stack

| Component | Technology |
|---|---|
| Programming Language | Python |
| Frontend | Streamlit |
| Large Language Model | Qwen2.5 1.5B |
| LLM Runtime | Ollama |
| Embedding Model | all-MiniLM-L6-v2 |
| Vector Database | FAISS |
| Semantic Search | Sentence Transformers |
| Code Analysis | Python AST |
| Automated Testing | pytest |
| Execution Environment | Docker |
| Data Processing | NumPy, Pandas |

---

## 4. System Architecture

```text
              USER
               |
               v
       STREAMLIT INTERFACE
               |
       +-------+--------+
       |       |        |
       v       v        v
   Code      Debugger  Code Search
 Generator      |        |
       |        v        |
       |     Python AST  |
       |        |        |
       v        v        v
  FAISS      Qwen2.5   FAISS
 Retrieval   Debugger  Retrieval
       |
       v
  Retrieved Examples
       |
       v
  Qwen2.5 via Ollama
       |
       v
  Generated Python Code
       |
       v
  Syntax Validation

  Test Generator
       |
       v
  Qwen2.5 Test Generation
       |
       v
  pytest inside Docker
       |
       v
  Test Results

  Code Execution
       |
       v
  Restricted Docker Container
       |
       v
  Execution Output
```

---

## 5. RAG Implementation

The system implements Retrieval-Augmented Generation using the following workflow:

1. The user submits a programming question.
2. Sentence Transformers converts the query into a numerical embedding.
3. FAISS retrieves semantically similar programming examples.
4. A hybrid ranking mechanism combines semantic similarity and keyword overlap.
5. The top retrieved examples are added to the LLM prompt.
6. Qwen2.5 generates Python code using the question and retrieved context.

### Hybrid Ranking

The retrieval system uses:

```text
Combined Score =
0.75 × Semantic Similarity
+
0.25 × Keyword Score
```

This combines semantic relevance with lexical keyword matching.

---

## 6. Dataset

The project uses the StaQC Python dataset from Hugging Face.

Dataset: `koutch/staqc`

Configuration: `sca_python`

Dataset license: CC BY 4.0

The collected dataset was processed to remove empty records, duplicates and code snippets identified as invalid or non-Python.

Additional manually prepared Python examples were included to improve coverage of common programming tasks.

### Dataset Statistics

| Stage | Records |
|---|---:|
| Collected raw records | 3,500 |
| Cleaned StaQC records | 1,900 |
| Additional examples | 30 |
| Combined dataset | 1,930 |

Note: Language filtering uses heuristics and syntax validation; it cannot guarantee that every retained example is valid Python.

---

## 7. Evaluation

The system was evaluated using an eight-case held-out benchmark.

The evaluation compared code generation without retrieval (No-RAG) against generation with retrieved examples (RAG).

### Prompt Version Comparison

| Version | No-RAG Accuracy | RAG Accuracy |
|---|---:|---:|
| Original | 62.50% | 50.00% |
| Prompt v2 | 87.50% | 87.50% |
| Prompt v3 | 87.50% | 87.50% |
| Prompt v4 | 87.50% | 100.00% |

### Latest Results

- No-RAG: 7 out of 8 cases passed.
- RAG: 8 out of 8 cases passed.
- Observed improvement: 12.50 percentage points.
- Average retrieval keyword coverage: 34.38%.
- All eight saved RAG solutions independently passed Docker-based verification.

The benchmark is small and represents a single evaluation run. These results demonstrate the observed performance on the selected test cases, not a guarantee of general performance.

Comparison chart:

`evaluation/rag_vs_no_rag_comparison.png`

Detailed reports:

- `evaluation/consolidated_comparison.csv`
- `evaluation/results_held_out_prompt_v4.csv`
- `evaluation/verification_saved_rag_prompt_v4.txt`

---

## 8. Project Structure

```text
CodeMentorAI/
|
|-- app.py
|-- requirements.txt
|-- README.md
|-- Dockerfile.test
|-- .gitignore
|
|-- data/
|   |-- raw_dataset.json
|   |-- processed_dataset.json
|   |-- additional_python_examples.json
|   |-- combined_dataset.json
|   |-- combine_datasets.py
|
|-- modules/
|   |-- data_loader.py
|   |-- download_dataset.py
|   |-- preprocessor.py
|   |-- embedding.py
|   |-- vector_database.py
|   |-- retriever.py
|   |-- llm.py
|   |-- code_analyzer.py
|   |-- test_generator.py
|   |-- sandbox.py
|
|-- pages/
|   |-- 1_Code_Generator.py
|   |-- 2_Debugger.py
|   |-- 3_Test_Generator.py
|   |-- 4_Code_Search.py
|
|-- vector_store/
|   |-- embeddings.npy
|   |-- code_index.faiss
|   |-- metadata.json
|
|-- evaluation/
    |-- evaluate.py
    |-- test_cases.json
    |-- held_out_test_cases.json
    |-- compare_results.py
    |-- consolidated_comparison.csv
    |-- rag_vs_no_rag_comparison.png
```

Additional evaluation reports and baseline files are also stored in the evaluation directory.

---

## 9. Installation and Setup

### Prerequisites

- Python 3.12
- Ollama
- Docker Desktop
- Git (optional)

### Step 1: Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd CodeMentorAI
```

### Step 2: Create a virtual environment

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Install and start Ollama

Install Ollama from:

https://ollama.com/

Download the model:

```bash
ollama pull qwen2.5:1.5b
```

Make sure the Ollama service is running.

### Step 5: Prepare the Docker test image

Make sure Docker Desktop is running.

```bash
docker build -f Dockerfile.test -t codementor-test:latest .
```

### Step 6: Run the application

```bash
streamlit run app.py
```

Open:

```text
http://localhost:8501
```

---

## 10. Evaluation Commands

Run the default benchmark:

```bash
python -m evaluation.evaluate
```

Run the held-out benchmark:

```bash
python -m evaluation.evaluate evaluation/held_out_test_cases.json
```

Compare prompt versions:

```bash
python -m evaluation.compare_results
```

Independently verify saved RAG solutions:

```bash
python -m evaluation.verify_saved_rag
```

---

## 11. Security Considerations

Generated code and AI-generated tests are untrusted inputs.

The project uses Docker restrictions including:

- Disabled networking.
- Memory and CPU limits.
- Process limits.
- Read-only filesystem.
- Reduced Linux capabilities.
- Non-root execution.
- Execution timeouts.

These restrictions reduce execution risk but do not provide an absolute security guarantee. Docker is not a complete substitute for a hardened sandbox.

---

## 12. Current Limitations

- The dataset is relatively small compared with large public code datasets.
- Dataset language filtering is heuristic-based.
- The local 1.5B model may produce incorrect or incomplete code.
- Retrieval quality depends on dataset coverage and query similarity.
- The held-out benchmark contains only eight programming tasks.
- The debugger primarily performs syntax analysis and selected code-quality checks; it does not guarantee detection of all runtime or logical errors.
- Docker restrictions reduce risk but cannot guarantee complete isolation.

---

## 13. Future Enhancements

- Expand the programming dataset.
- Improve hybrid retrieval and reranking.
- Evaluate on a larger held-out benchmark.
- Support additional programming languages.
- Improve code-quality and runtime error detection.
- Add user authentication and saved coding sessions.
- Improve test generation and debugging accuracy.
- Explore stronger local code-generation models.

---

## 14. Conclusion

CodeMentor AI demonstrates how Retrieval-Augmented Generation can be integrated with a local Large Language Model to build a practical programming assistant.

By combining semantic code retrieval, AI-based generation, static code analysis, automated testing and restricted Docker execution, the project provides an integrated environment for assisting developers with common programming tasks.
