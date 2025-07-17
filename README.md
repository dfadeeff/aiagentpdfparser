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

## Project Structure

The project is organized around the core concepts of LangGraph: state, nodes, and edges.

*   **`main.py`**: The main entry point. It defines the graph structure, wires the nodes together, compiles the graph, and runs the extraction process.
*   **`requirements.txt`**: Lists the necessary Python libraries.
*   **`graph/`**: This directory contains the core logic of our extraction graph.
    *   **`state.py`**: Defines the `GraphState` object, a typed dictionary that holds all the data passed between nodes (e.g., PDF content, raw extraction, final JSON).
    *   **`nodes.py`**: Contains the primary functions that act as nodes in our graph: one for extraction and one for formatting.
    *   **`conditional_edges.py`**: Holds the logic for any conditional paths in our graph (e.g., deciding whether the extraction was successful enough to proceed to formatting).
*   **`tools/`**: Contains standalone utility functions, like the `pdf_parser`.
*   **`output/`**: The destination for the final `extracted_data.json` file.

## How It Works

The framework operates as a state machine, moving through a series of defined steps:

1.  **Initialization**: The `main.py` script initializes the graph with a starting state containing the path to the PDF.
2.  **PDF Parsing (Tool)**: The first node, `extract_table`, is called. It uses the `pdf_parser` tool to read the text from the PDF file.
3.  **Extraction Node**: The `extract_table` node sends the parsed text to an LLM with a specialized prompt, asking it to identify and extract the complex table structure as a raw string or preliminary JSON. The result is saved back to our graph's state.
4.  **Conditional Edge (Quality Gate)**: After extraction, a conditional edge checks the state. Did the extraction produce any output? If yes, proceed to the formatting node. If no, route to an error-handling or end state.
5.  **Formatting Node**: The `format_json` node takes the raw extraction from the state, sends it to a different LLM with a prompt focused on structuring the data into the final, detailed JSON format, and saves this back to the state.
6.  **End**: The graph reaches its end state, and the final JSON from the state is saved to a file.

This explicit, step-by-step process ensures a highly reliable and auditable extraction pipeline.




## Setup and Usage

1.  **Install Dependencies**:
    ```bash
    pip install -r "langchain[llms]" langgraph pypdf python-dotenv
    ```

2.  **Run the Framework**:
    ```bash
    python main.py --pdf_path "path/to/your/document.pdf"
    ```


Explicit, Deterministic Control is Paramount: This problem is not a negotiation or a conversation. It is a data processing pipeline that demands a specific, correct output. LangGraph, at its core, is a state machine. We define the exact states and the explicit transitions (edges) between them. The final reconstruct_structure node, which is pure Python code, is the perfect example of a reliable, deterministic step that would be awkward to implement in a conversational framework. AutoGen, being conversation-driven, is fundamentally probabilistic. You can't tell two agents to "talk" and guarantee they produce a bit-for-bit perfect JSON structure every time.
Error Handling and State Management: The entire challenge we faced was handling failures. Our final LangGraph solution has an explicit fixer node and a validate_and_fix_json edge that manages a retry_count in a shared state object. This level of granular control over error handling and retries is native to LangGraph's design. Implementing a similar robust retry loop in AutoGen would be much more complex, requiring you to manage the conversational state and explicitly prompt an agent to "try again" based on the output of another agent, which is less reliable.
Separation of AI and Algorithmic Logic: Our final solution proves that the optimal approach is a hybrid one: use AI for perception and deterministic algorithms for logic. LangGraph excels at this. Each node can be a different tool—one can be an LLM, the next can be a Pydantic validator, and the final one can be a complex Python algorithm. It is a framework for orchestrating heterogenous tasks. AutoGen is primarily designed to orchestrate LLM-based agents, making the integration of pure, complex Python logic less natural.
In conclusion, our journey has proven that for tasks requiring high reliability, auditable steps, and the integration of deterministic code, LangGraph is unquestionably the superior framework. It provides the control and robustness necessary for a production-grade data processing pipeline, while AutoGen is better suited for more open-ended, creative, or conversational tasks.