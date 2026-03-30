# Assignment 3: Build 3 – HITL + Tool Router Agent

**Course**: QAC387  
**Students**: Jacob Poore and Arian Zarazua  


## Overview

This project implements a Human-in-the-Loop (HITL) AI Data Analysis Agent using an LLM-based router.

The agent:
- Accepts natural language data questions
- Routes tasks to tools or generates Python code
- Requires human approval before executing code
- Returns results with explanations
- Logs activity using Langfuse

## Repository Structure

builds/        → Main agent (build3_hitl_router_agent.py)  
data/          → Datasets
docs/          → Logs, tracing, evaluation  
knowledge/     → Context or references  
scripts/       → Helper scripts  
src/           → Core modules  
requirements.txt  
test_modules.py  


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

3. Run:
   ```
   python builds/build3_hitl_router_agent.py --data data/penguins.csv --report_dir reports --tags build3 --memory
   ```
     - (optional) `--stream` tag



## Cautions

- Generate code may be incorrect/damaging, review code manually before running  
- LLM outputs may contain errors  
- Large datasets may reduce performance (improved w/ future SQL) 



## Project Context: NFL Data AI Agent

This assignment is a core component of our larger project:

"Using AI Agents to Analyze NFL Data"

Goal:
Allow users to query 15 seasons of NFL data (2010–2025) using plain English instead of SQL.

Example:
"Who was the best quarterback of the 2010s?"



## System Architecture (Planned)


1. LLM Router Agent **(incorporated into this assignment)**  
   - Chooses tools or generates code  
   - Enforces human approval  

2. NFL Database  **(incorporated in this assingment)**
   - Structured multi-season dataset  
    - Compiled through https://www.pro-football-reference.com. Their contributors and sources of revelvent statistics are sited:
    
          "The majority of our data comes from the work of Pete Palmer, Ken Pullis, and Gary Gillette.
          Scott Kacsmar is our source for comeback and game-winning drive information.
          Andrew McKillop is our source for training camp information"
    - Play by play data downloaded through https://nflsavant.com/about.php. (Are looking for a superior source)
          "All data and stats from this site are compiled from publicly-available NFL play-by-play data on the internet."
    - NFL GIS data (official stats)
          Currently unable to access but are looking for ways to access the datasheets. 

3. NL-to-SQL  
   - Converts user input into SQL  
   - Includes retry/self-correction  

4. Docker GUI  
   - Browser-based interface  

## Summary

This assignment builds the decision-making core of a larger AI system that enables natural language exploration of complex sports data.