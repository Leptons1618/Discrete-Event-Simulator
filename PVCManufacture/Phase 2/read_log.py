import re

def read_simulation_log(log_file):
    with open(log_file, 'r') as file:
        lines = file.readlines()

    config_start = False
    results_start = False
    config_blocks = []
    results_blocks = []
    current_config = []
    current_results = []

    for line in lines:
        if "Simulation Configuration:" in line:
            config_start = True
            if current_config:
                config_blocks.append(current_config)
                current_config = []
            continue
        if "Simulation Results:" in line:
            results_start = True
            if current_results:
                results_blocks.append(current_results)
                current_results = []
            continue
        if config_start and "_" * 50 in line:
            config_start = False
            config_blocks.append(current_config)
            current_config = []
        if results_start and "_" * 50 in line:
            results_start = False
            results_blocks.append(current_results)
            current_results = []

        if config_start:
            current_config.append(line.strip())
        if results_start:
            current_results.append(line.strip())

    return config_blocks, results_blocks

def generate_markdown_table(config_blocks, results_blocks):
    markdown = ""
    for config_lines, results_lines in zip(config_blocks, results_blocks):
        markdown += "# Simulation Configuration\n\n"
        markdown += "| Parameter | Value |\n"
        markdown += "|-----------|-------|\n"
        for line in config_lines:
            if line and ": " in line:
                key, value = line.split(": ", 1)
                markdown += f"| {key} | {value} |\n"

        markdown += "\n# Simulation Results\n\n"
        markdown += "| Metric | Value |\n"
        markdown += "|--------|-------|\n"
        for line in results_lines:
            if line and ": " in line and not line.startswith("Shift-wise Production Logs:"):
                key, value = line.split(": ", 1)
                markdown += f"| {key} | {value} |\n"
        markdown += "\n---\n"  # Add separator between simulations

    return markdown

def print_table_in_terminal(markdown):
    print(markdown)

if __name__ == "__main__":
    config_blocks, results_blocks = read_simulation_log("simulation.log")
    markdown = generate_markdown_table(config_blocks, results_blocks)
    with open("simulation_results.md", "w") as file:
        file.write(markdown)
    print_table_in_terminal(markdown)
