# Assignment 3: Build 3 – HITL + Tool Router Agent with Time Series Support

**Course**: QAC387  
**Students**: Jacob Poore and Arian Zarazua  


## Overview

This project implements a Human-in-the-Loop (HITL) AI Data Analysis Agent using an LLM-based router with enhanced time series analysis capabilities.

The agent:
- Accepts natural language data questions
- Intelligently routes tasks to specialized tools or generates Python code
- Prioritizes temporal trend analysis when time-based columns are available
- Requires human approval before executing generated code
- Returns results with explanations and visualizations
- Optionally logs activity using Langfuse

**Assignment 3 Additions**
-  **Time Series Tools**: Temporal aggregation and line chart visualization
-  **Enhanced Router**: Improved system prompts for temporal analysis detection
- **Better Suggestions**: LLM now recommends time-series analyses first when temporal columns exist

## How to Run 

1. Install dependencies from root:
   
   `pip install -r requirements.txt `

2. Set API keys:
   ```
   OPENAI_API_KEY=your_key  
   LANGFUSE_PUBLIC_KEY=your_key 
   LANGFUSE_SECRET_KEY=your_key  
   LANGFUSE_BASE_URL = "http://localhost:(open localport, e.g. '3000')"
   ```

3. Run the agent:
   
   **Single CSV file:**
   ```bash
   python builds/build3_hitl_router_agent.py --data data/Pro-Football-Reference/Stats/2023_NFL_Team_Statistics.csv --report_dir reports --tags build3 --memory
   ```

   **Directory of CSV files (batch processing):**
   ```bash
   python builds/build3_hitl_router_agent.py --data data/Pro-Football-Reference/Stats --report_dir reports --tags build3 --memory
   ```

   **Optional flags:**
   - `--stream`: Enable streaming output from LLM
   - `--memory`: Enable multi-turn conversation memory
   - `--tags build3`: Tag all traces with "build3" (for Langfuse logging)


## Agent Commands

Once the agent starts, you can interact with it using:

```
help                  Show available commands
schema                Display dataset schema (columns + dtypes)
suggest <question>    Get AI suggestions for analyses (prioritizes temporal trends)
ask <request>         Router decides: tool execution OR code generation (HITL)
tool <request>        Force tool execution: router selects best tool
code <request>        Force code generation (HITL): review before approving
run                   Execute last approved/generated script
exit                  Quit the agent
```


## Example Usage

### Time Series Analysis
```
ask plot average passing yards by season
```

## Cautions & Limitations

 **Code Generation Risks:**
- Generated code may be incorrect or unintended; review manually before executing
- LLM outputs are probabilistic and can contain logical errors
- Always read and approve code before running

 **Tool Limitations:**
- Some Build0 tools work best with single CSV files (batch mode may use codegen instead)
- Large datasets may reduce performance (SQL integration planned for future builds)
- Tool arguments are validated against schema but edge cases may occur (currently PBP data has issues with dates/seasons)

 **Time Series Features:**
- Temporal analysis is prioritized when time-based columns are detected
- Supported temporal columns: season, year, month, game_id, week, date, etc.
- Aggregation handles NULL values gracefully (drops before aggregation) 


## Project Context: NFL Data AI Agent

This assignment is a core component of our larger project:

"Using AI Agents to Analyze NFL Data"

Goal:
Allow users to query a decade of NFL using plain English. 

Example:
"Who was the best quarterback of the 2010s?"



## LLM Router Agent
   - **Intelligent Routing**: Evaluates user requests and decides between:
     - **Tool Execution**: Dispatches to specialized tools (faster, deterministic)
     - **Code Generation**: Creates custom Python scripts for complex analyses (flexible)
   - **Enhanced System Prompts**: 
     - Router detects temporal columns and prioritizes time-series tools
     - Tool plan generator includes parameter validation
     - Suggestion engine recommends temporal analyses when appropriate
   - **HITL (Human-In-The-Loop)**:
     - Users review and approve generated code before execution
     - Command-based interface for easy interaction and control


## Additional Test Runs

**Pro-Football-Reference Datasets:**
```bash
# Team statistics across multiple seasons
python builds/build3_hitl_router_agent.py --data data/Pro-Football-Reference/Stats --report_dir reports --tags build3 --memory

# Metadata and contextual information
python builds/build3_hitl_router_agent.py --data data/Pro-Football-Reference/Metadata --report_dir reports --tags build3 --memory
```

**NFL Savant Play-by-Play Data:**
```bash
# Granular game-level play information (test temporal analysis with game_id or week)
python builds/build3_hitl_router_agent.py --data data/Stat-Savant/PBP --report_dir reports --tags build3 --memory
```


## Known Issues & Limitations

### Current Challenges
1. **Tool Misselection**: Agent occasionally selects incorrect tools or misroutes column types
   - Partially mitigated by enhanced prompts and column type validation
   
2. **Data Quality Issues**:
   - Stat-Savant PBP data contains malformed CSV rows (partially handled by io_utils.py)
   - Missing season information in some date fields requires manual augmentation
   - Filtering by specific year/season can produce inconsistent results

3. **Build0 Tool Compatibility**:
   - Some existing Build0 tools may not work correctly with batch (directory) input
   - Single CSV files are more reliable for specialized tools
   - Workaround: Use code generation for complex multi-file analyses

4. **Code Generation Limitations**:
   - OpenAI sometimes generates time-series code that doesn't match user intent
   - Generated code requires manual review and validation

### Future Fixes Planned
- [ ] Standardize temporal column naming across datasets
- [ ] Enhance tool-specific prompt engineering for improved column routing
