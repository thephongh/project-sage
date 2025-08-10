-----

### **Product Requirements Document: "Project Sage"**

  * **Document Version:** 1.1
  * **Status:** Final Draft
  * **Author:** Brainstormer & User
  * **Date:** August 10, 2025

-----

### **1. Introduction & Overview**

"Project Sage" is a command-line interface (CLI) application supplemented by a graphical setup utility, designed to act as a personal, intelligent AI assistant for complex project management. For every project folder it's placed in, Sage creates a self-contained knowledge base, scanning all documentation—including scanned PDFs—to provide context-aware answers, summaries, and insights. It addresses the critical pain point of information overload and time-consuming manual document searches for project managers dealing with vast, multilingual, and multi-format documentation. By leveraging the power of Retrieval-Augmented Generation (RAG) and leading LLMs, Sage allows users to "talk" to their project documents.

### **2. Target User & Persona**

**Persona:** "Philippe," The Renewable Energy Project Manager

  * **Role:** Manages large-scale investment projects with multi-year timelines, often based in locations like Hanoi and Hưng Yên.
  * **Responsibilities:** Oversees legal, financial, technical, and commercial aspects of a project. Manages contracts, studies, and internal reporting.
  * **Pain Points:**
      * Spends hours searching through thousands of documents across different formats (PDFs, DOCX, XLSX, PPTX), many of which are scanned copies.
      * Needs to quickly synthesize information from multiple sources to answer urgent questions from stakeholders.
      * Deals with documents in Vietnamese but needs to report and communicate in English.
      * Current note-taking tools are useful but require significant manual effort to keep updated with project documentation.
  * **Technical Skills:** Comfortable using the command line and understands basic scripting concepts. Is not a full-time developer but can manage API keys and configurations.

### **3. Goals & Objectives**

  * **Goal 1: Accelerate Information Retrieval.** Drastically reduce the time it takes for a project manager to find specific information within project documents.
  * **Goal 2: Enhance Decision Making.** Provide quick, synthesized summaries and data points to enable faster, more informed decisions.
  * **Goal 3: Overcome Language & Format Barriers.** Seamlessly bridge the gap between source documents in Vietnamese (including scanned files) and the user's working language (English).
  * **Goal 4: Maintain Project Context & Simplicity.** Ensure the AI's knowledge is strictly confined to its project folder and that the initial setup is intuitive via a simple GUI.

### **4. Core Features & Functionality (V1.1)**

| Command | Arguments | Description |
| :--- | :--- | :--- |
| **`sage setup`** | (none) | Launches a simple graphical user interface (GUI) window for first-time project initialization. This GUI will guide the user to: \<br\> 1. Confirm the project directory. \<br\> 2. Enter and save their LLM API key. \<br\> 3. Select the primary language of the documents (e.g., Vietnamese) to ensure optimal OCR performance. |
| **`sage update`** | `[-f, --force]` | Scans the project directory for supported files. It intelligently detects **new** and **modified** files, using OCR to process text from scanned PDFs. It chunks, embeds, and stores the knowledge in the local vector database. The `--force` flag forces a full re-scan. |
| **`sage ask`** | `"<QUERY>"` | The main interaction command. The user asks a question in English. The app performs the RAG process: retrieves relevant Vietnamese text chunks, packages them with the English question and a translation instruction, sends them to the LLM API, and prints the generated English answer, citing its sources. |
| **`sage status`** | (none) | Provides a quick summary of the knowledge base, including the number of files indexed, the date of the last update, and the configured LLM model. |

**Supported File Types for Ingestion:**

  * **.pdf** (including **scanned image-based documents**, handled via Optical Character Recognition - OCR)
  * `.docx`, `.pptx`, `.xlsx`
  * `.txt`, `.md`

### **5. Technical Stack & Architecture**

  * **Language:** Python 3.9+
  * **CLI Framework:** Typer or Click
  * **GUI Toolkit:** A simple, cross-platform library like **Tkinter** or **CustomTkinter**.
  * **Core AI/RAG Framework:** LangChain or LlamaIndex
  * **File Loaders:** Unstructured.io library
  * **OCR Engine:** **Tesseract-OCR** (requiring appropriate language packs, e.g., for Vietnamese).
  * **Embedding Model:** A high-quality, multilingual model (e.g., `text-embedding-004`).
  * **Vector Database:** A local, file-based database like ChromaDB or FAISS.
  * **LLM Integration:** API calls to a user-selected provider (e.g., Google Gemini, Anthropic Claude, OpenAI GPT).

### **6. User Flow / Workflow**

1.  **Installation:** The user installs Sage as a Python package.
2.  **GUI-based Setup:** The user navigates to their project root folder in the terminal and runs `sage setup`.
3.  **Onboarding Window:** A small, clean window appears. The user confirms the project path, pastes their API key, selects "Vietnamese" from a language dropdown, and clicks "Initialize Project."
4.  **First Index:** Back in the terminal, the user runs `sage update`. A progress bar shows the files being indexed, including the OCR process for scanned documents.
5.  **Interaction:** The user asks a question: `sage ask "What was the agreed upon price for the turbine supply in the scanned contract?"`
6.  **Receiving Answer:** Sage returns a synthesized answer in English, followed by a list of source files: `[Sources: /Contracts/Scanned_Turbine_Agreement_2024.pdf]`.

### **7. Requirements & Constraints**

  * **Cross-Platform:** Must run on Windows, macOS, and Linux.
  * **Dependencies:** The setup process must provide clear instructions for installing Tesseract-OCR and required language packs.
  * **Performance:** `ask` queries should return answers within seconds. Incremental updates should be reasonably fast.
  * **Security:** API keys must be stored locally and not be tracked in version control.
  * **Internet:** The `setup` GUI and `status` command should work offline. `update` and `ask` require an internet connection for API calls.

### **8. Assumptions**

  * The user has Python installed on their system.
  * Scanned documents are of a reasonable quality (e.g., \>200 DPI) for OCR to be effective.
  * The user has an active API key for their chosen LLM provider.

### **9. Future Enhancements (V2.0 Ideas)**

  * **"Watch" Mode:** An optional `sage watch` command that runs in the background and automatically triggers an update when files are added or changed.
  * **Advanced Parsing:** Specialized parsers for accurately extracting data from complex tables and charts within documents.
  * **"Action" Commands:** Commands like `sage draft "an email to the EPC contractor about pending issue X"` that actively use the context to generate new documents.
  * **Full GUI:** Expanding the application into a full desktop app with a persistent chat window and file management view.

### **10. Success Metrics**

  * **Quantitative:** Reduction in time spent searching for information (measured by user survey), frequency of use of the `ask` command, number of projects where Sage is deployed.
  * **Qualitative:** User satisfaction feedback regarding the ease of setup, the accuracy and relevance of answers, and overall impact on productivity.