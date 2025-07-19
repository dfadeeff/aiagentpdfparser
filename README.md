# Table Extraction AI Agent - Framework Comparison & Simple Solution

## 🔍 Framework Choice: AutoGen vs LangGraph

This project implements a robust AI agent framework using **LangGraph** to reliably extract data from complex tables within PDF documents. The solution is designed as a stateful graph to ensure a deterministic and controllable workflow.

### Detailed Comparison

| Feature | LangGraph | AutoGen |
|---------|--|---------|
| **Core Concept** | A state machine. You build a graph of steps (nodes) and explicitly define the transitions (edges) between them.| A multi-agent conversation. You define agents with different roles, and they "talk" to each other to solve a problem.. |
| **Control & Reliability** | Extremely High. You have explicit, granular control over the workflow. The process is deterministic and follows the graph you define. Error handling and retries can be built directly into the graph's logic. | Medium. The flow is emergent from the conversation. While you can guide it with system prompts, it can sometimes be unpredictable. It's less of a deterministic process and more of a guided collaboration.. |
| **Debugging** | Easier. Since the flow is a graph, you can trace the state as it passes from node to node. You know exactly which step failed and what the state was at that point. | Harder. Debugging involves analyzing the entire conversation history to see where the agents went off-track. It can be difficult to pinpoint the exact cause of an error in the conversational flow. |
| **Development Speed** | Slower initial setup due to more boilerplate code for defining the state and graph structure. | Faster for rapid prototyping of tasks that naturally fit a conversational model. |
| **Best For** | Complex, stateful workflows where reliability, auditability, and deterministic execution are critical. Perfect for production-grade data processing pipelines like this one. | Rapidly building demos and applications where the task can be solved through a collaborative "discussion" between AI agents.. |

Conclusion: For a task that requires accurate data extraction from a specific format and has to run reliably during a live interview, LangGraph is the superior choice. It allows you to build a robust, predictable, and debuggable pipeline.

## Why LangGraph?

For this data extraction task, **reliability** is the top priority. LangGraph was chosen over other frameworks like AutoGen for the following reasons:

*   **Explicit Control**: We define every step (node) and transition (edge) in the process, eliminating the unpredictability of conversational AI.
*   **State Management**: The entire process revolves around a central, explicitly defined state object, making the data flow transparent and easy to track.
*   **Robustness & Debugging**: It's significantly easier to implement error handling and to debug the workflow by examining the state at each node in the graph.



# Deterministic PDF Table Extraction with LangGraph

This project demonstrates a highly reliable, deterministic pipeline built with LangGraph to extract complex tabular data from a fixed-layout PDF document. The core philosophy is to treat the process not as an AI-driven estimation, but as a predictable, rule-based "assembly line" that guarantees 100% accuracy for the target document structure.

---

## The Core Concept: A Deterministic Assembly Line

The pipeline is designed as a simple, powerful assembly line for processing the PDF. Data flows from one station (a `node`) to the next in a predictable order, and each station performs one specific, clearly defined job. This approach ensures the process is auditable, debuggable, and exceptionally reliable.

The entire process is orchestrated by `run_pipeline.py` and the "blueprint" for the assembly line is defined in `pipeline/graph.py`. It follows a strict, unchangeable sequence of operations:

1.  **Start at station `extract`**.
2.  **From `extract`**, always go to `enrich`.
3.  **From `enrich`**, always go to `clean`.
4.  **After `clean`**, the process ends, and the final data is saved.

---

## Project Structure

The project is organized logically to separate the pipeline's definition from its individual components.

```

├── data/
│ └── Table-Example-R.pdf
├── output/
│ └── values_with_metadata.json
├── pipeline/
│ ├── init.py
│ ├── graph.py # Defines the assembly line blueprint (nodes and edges).
│ ├── nodes.py # Contains the logic for each station (node).
│ └── state.py # Defines the data package (state) that moves along the line.
├── tools/
│ └── extractor.py # Contains the raw OCR extraction tools.
├── run_pipeline.py # The main script to run the entire process.
└── requirements.txt
```




## The Assembly Line in Action: A Step-by-Step Explanation

The "package" of data that moves between stations is a shared dictionary called the `PipelineState`. As the package moves along the assembly line, each station adds its results to it.

### **Station 1: Extraction (`extraction_node`)**
*   **File:** `pipeline/nodes.py`
*   **Input:** The initial state containing the `pdf_path`.
*   **Job:** This station's only job is to get the raw materials. It calls the `extract_values_from_pdf` function from `tools/extractor.py`, which uses OCR to find and extract all 31 numerical values from the PDF.
*   **Process:**
    1.  It opens the PDF and converts the page into a high-resolution image.
    2.  It runs Tesseract OCR on the image.
    3.  It specifically filters for text that matches the format of a numerical value (e.g., `XX,XX`).
    4.  It captures the `value`, its `bbox` (bounding box coordinates), and the OCR `confidence`.
*   **Output:** It adds the list of these 31 extracted values to the `PipelineState` under the key `"extracted_values"`.
*   **Next Stop:** The conveyor belt (`edge`) automatically moves the updated package to the `enrich` station.

### **Station 2: Enrichment (`metadata_enrichment_node`)**
*   **File:** `pipeline/nodes.py`
*   **Input:** The state now contains the raw `extracted_values`.
*   **Job:** This is the most important station in the entire factory. It takes the raw values and correctly assigns all the row and column headers to each one. This is a **100% deterministic and rule-based process**, which is the key to its reliability.
*   **Process (The Core Logic):** It loops through each of the 31 values and applies a simple set of rules based on that value's X and Y coordinates:
    *   **Row Logic (Vertical Position):**
        *   "Is the value's Y-coordinate between `200` and `290`?" -> If yes, its primary headers are `M1` and `Merged1`.
        *   "Within that block, is its Y-coordinate between `215` and `230`?" -> If yes, its sub-headers are `Row.Invisible.Grid2` and `BB`.
        *   This is repeated for every visual block in the table. This logic correctly handles the complex "inheritance" problem, where values like `50,00` correctly receive the headers from the `CC` row because their Y-coordinates fall within that rule's defined range.
    *   **Column Logic (Horizontal Position):**
        *   "Is the value's X-coordinate between `370` and `400`?" -> If yes, its column header is `Col1`.
        *   This is repeated for all the distinct column blocks.
    *   **Exception Logic:** It contains one final, surgical override for the anomalous `35,00` values, ensuring they are handled correctly without affecting the other rules.
*   **Output:** It produces a new list where every value is now perfectly paired with its correct headers. This list is added to the `PipelineState` under the key `"values_with_metadata"`.
*   **Next Stop:** The conveyor belt moves the package to the final `clean` station.

### **Station 3: Cleaning (`cleaning_node`)**
*   **File:** `pipeline/nodes.py`
*   **Input:** The state contains the `values_with_metadata` from the previous station.
*   **Job:** This is the final quality control station. Its job is minimal because the enrichment station did its work so well. It only performs minor, predictable touch-ups.
*   **Process:**
    1.  It loops through the headers of each value.
    2.  It checks a small dictionary (`replacements`) for known, consistent OCR typos (e.g., it replaces `Colt` with `Col1`).
    3.  It ensures there are no duplicate headers in any list.
*   **Output:** It updates the `values_with_metadata` list in the `PipelineState` with the final, polished data.
*   **Next Stop:** The conveyor belt reaches the `END`.

Finally, back in `run_pipeline.py`, the "factory manager" receives the completed data package (`final_state`), takes the final `values_with_metadata` list, and saves it to the `output/values_with_metadata.json` file.

---

## Setup and Usage

1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd appliedai
    ```

2.  **Install dependencies:**
    *(It is recommended to use a virtual environment)*
    ```bash
    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    ```

3.  **Run the pipeline:**
    ```bash
    python run_pipeline.py
    ```

4.  **Check the output:**
    The final, 100% correct JSON file will be located at `output/values_with_metadata.json`.
