# Assignment 4: Build 4 – NFL Data Analysis Agent

| | |
|---|---|
| **Course** | QAC387 |
| **Students** | Jacob Poore and Arian Zarazua |
| ** Build 4 Test Results** | [**View Full Agent Test Log** →](docs/agent_test_log2.pdf) |
| ** Build 3 Test Results** | [**View Full Agent Test Log** →](docs/agent_test_log1.pdf) |


> [!WARNING]
> **IMPORTANT:** Do NOT commit or upload Langfuse logs.  
> These files may contain OpenAI API keys and will be blocked by GitHub push protection.
---


## Installation

Install dependencies from the root directory:
```bash
pip install -r requirements.txt
```

### Configuration

Set the required API keys:
```bash
export OPENAI_API_KEY=your_key
export LANGFUSE_PUBLIC_KEY=your_key
export LANGFUSE_SECRET_KEY=your_key
export LANGFUSE_BASE_URL=http://localhost:3000  # or your port
```

### Running the Agent

**Single file analysis:**
```bash
# Without RAG
python builds/build4_rag_router_agent.py --data data/Pro-Football-Reference/ExpectedPoints-2013.csv --report_dir reports --tags build3 --memory

# With RAG
python builds/build4_rag_router_agent.py --data data/Pro-Football-Reference/Stats --report_dir reports --knowledge_dir knowledge --session_id cli-session --memory

```

**Batch processing (directory of CSVs):**
```bash
# Without RAG
python builds/build4_rag_router_agent.py --data data/Pro-Football-Reference/Stats --report_dir reports --tags build3 --memory

# With RAG
python builds/build4_rag_router_agent.py --data data/Pro-Football-Reference/Stats --report_dir reports --knowledge_dir knowledge --session_id cli-session --memory

```


##  Agent Commands

| Command | Description |
|---------|-------------|
| `help` | Show available commands |
| `schema` | Display dataset schema (columns + data types) |
| `suggest <question>` | Get AI suggestions for analyses (prioritizes temporal trends) |
| `ask <request>` | Router decides: tool execution OR code generation (HITL) |
| `tool <request>` | Force tool execution: router selects best applicable tool |
| `code <request>` | Force code generation (HITL): review before approving |
| `run` | Execute last approved/generated script |
| `exit` | Quit the agent |

---

## Example Use Cases

**Time Series Analysis:**
```bash
ask plot average passing yards by season
ask show quarterback performance trends across years
```

---

##  Important Cautions & Limitations

###  Code Generation Risks
- Generated code may be incorrect or unintended—**always review manually before executing**
- LLM outputs are probabilistic and can contain logical errors
- Approve reviewed code before running

###  Tool Limitations
- Some Build0 tools work best with **single CSV files** (batch mode may use code gen instead)
- Large datasets may reduce performance (SQL integration planned for v2)
- Tool arguments are validated against schema, but edge cases may occur

###  Time Series Features
- Temporal analysis is prioritized when time-based columns detected
- Aggregation handles NULL values gracefully (drops before aggregation) 


##  Architecture

### Intelligent Routing
The LLM router evaluates user requests and decides between:
- **Tool Execution** → Dispatches to specialized tools (faster, deterministic)
- **Code Generation** → Creates custom Python scripts (flexible, custom logic)

### Human-In-The-Loop (HITL)
- Users review and approve generated code before execution
- Optional Langfuse logging for activity tracing

### Retrieval-Augmented Generation (RAG)
- This agent supports Retrieval-Augmented Generation (RAG), which allows it to incorporate external knowledge from a document corpus when generating responses. 
- RAG is used to improve reasoning in cases where dataset schema alone may be insufficient.

---

**Building the RAG Index**

Before using RAG, build a FAISS index from markdown documents stored in a knowledge directory:

```bash
python -m scripts.build_rag_index
```



##  Known Issues & Future Work

| Issue | Status | Notes |
|-------|--------|-------|
| **Tool Misselection** | Mitigated | Enhanced prompts reduce incorrect routing |
| **Stat-Savant PBP Quality** | Ongoing | Malformed CSV rows; handled by `io_utils.py` |
| **Temporal Column Naming** | Planned | Standardization needed across datasets |
| **Code Generation Accuracy** | Ongoing | Requires manual review before execution |

### Planned Improvements
- [ ] Enhance tool-specific prompt engineering for improved column routing
- [ ] SQL integration for large dataset processing
- [ ] Better date/season field validation
