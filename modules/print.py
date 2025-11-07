def print_timing_table(instructions):

    if not instructions:
        print("\nNo instructions to display timing for.")
        return

    # Column headers
    headers = ["Instruction", "Issue", "Execute Start", "Execute End", "MEM", "Write Back", "Commit"]
    
    # Calculate initial column widths based on headers
    col_widths = [len(h) for h in headers]
    
    # Prepare data rows and determine maximum column widths
    data_rows = []
    for instr in instructions:
        # Construct the instruction string (e.g., Add.d F1, F2, F3)
        try:
             instr_str = f"{instr.opcode} {', '.join(instr.operands)}"
        except TypeError:
             instr_str = f"{instr.opcode}"

        # Collect cycle data, using '-' for uncompleted stages
        row = [
            instr_str,
            str(instr.issue_cycle) if instr.issue_cycle is not None else "-",
            str(instr.execute_start_cycle) if instr.execute_start_cycle is not None else "-",
            str(instr.execute_end_cycle) if instr.execute_end_cycle is not None else "-",
            str(instr.mem_cycle) if instr.mem_cycle is not None else "-",
            str(instr.write_back_cycle) if instr.write_back_cycle is not None else "-",
            str(instr.commit_cycle) if instr.commit_cycle is not None else "-"
        ]
        data_rows.append(row)
        
        # Update column widths based on data length
        for i, item in enumerate(row):
            col_widths[i] = max(col_widths[i], len(item))

    # Add a buffer space (2 characters) to each width for readability
    col_widths = [w + 2 for w in col_widths]

    # --- Print Table ---
    total_width = sum(col_widths) + len(headers) - 1
    
    print("\n" + "=" * total_width)
    print("Instruction Timing Table (All Cycles)")
    print("=" * total_width)

    # Print Header
    header_line = "".join(f"{h:<{col_widths[i]}}" for i, h in enumerate(headers))
    print(header_line)
    
    # Print Separator
    separator = "".join("-" * col_widths[i] for i in range(len(headers)))
    print(separator)

    # Print Data Rows
    for row in data_rows:
        row_line = "".join(f"{item:<{col_widths[i]}}" for i, item in enumerate(row))
        print(row_line)

    print("-" * total_width)