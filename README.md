# Tomasuloslegacy – Out-of-Order Execution Simulator
*A Python implementation of Tomasulo’s Algorithm with full debugging and configurable hardware.*

## Overview

This project simulates Tomasulo’s Algorithm including issue, execute, write-back, and commit stages.
It supports:

- Full ARF + RAT register tracking
- Branch prediction
- Load/store forwarding
- Structural hazard modeling
- Custom hardware configuration
- Detailed logging and debugging output

## Requirements

**Python version:** `3.13.7`

Must be run using `python` (NOT `python3`). Tested only on Windows.

## How to Run

### 1. Clone or Download
Download the ZIP from the repository:

```
Tomasuloslegacy-main.zip
```

GitHub link:  
https://github.com/harshamondo/Tomasuloslegacy

### 2. Install Python 3.13.7

Ensure your terminal runs it using:

```
python
```

### 3. Run the Simulator

Open Command Prompt, navigate to the project folder:

```bash
cd /path/to/Tomasuloslegacy-main
```

Then run:

```bash
python new_main.py
```

## What You Will See

The terminal will display:

- Step-by-step debug logs
- Functional unit activity
- RAT & ARF updates
- Memory operations
- Final instruction timing table

Additional full output is saved in:

```
run.log
```

## Input Instructions

Default instruction file:

```
instruction_sets/new_test_cases.txt
```

Paste custom instructions here to test workloads.

## Configuration Options

### Instruction Set Selection
Modify in:

```
new_main.py
```

### Hardware Configuration
Edit `config.csv`:

- Number of RS entries
- Execution cycles
- Memory latency
- FU counts

### Register Files
- ARF: `arf.csv`
- RAT: `rat.csv`

## Included Test Benchmarks

The simulator includes test cases demonstrating CPU behavior:

- Straight-line code (no dependencies)
- Straight-line code with dependencies (RAW / WAR / WAW)
- Load/Store forwarding
- No forwarding
- Structural hazards
- Custom config tests from `config.csv`
- Simple loop to test branch prediction/commit handling

## Contributors

### Harsh
- Execute Stage  
- Write-Back Stage  
- Commit Stage  
- Branching & Branch Prediction  
- Helper Functions  
- Print Table (partial)  
- Main Debugger  
- Tests  

### Victor
- Issue Stage  
- Architecture & Pipeline Framework  
- Load/Store & Memory  
- Load/Store Forwarding  
- Main Debugger  
- Tests  

### Roshan
- Print Table (partial)  
- Report

## License

Educational project for computer architecture coursework.
