import os
import re
from collections import Counter
from pathlib import Path

# You may need to install the networkx library: pip install networkx
import networkx as nx

# --- Configuration ---
# Use your actual folder paths here
FOLDERS = [rf'C:\Games\Victoria-3\game\gui', ]# rf'C:\Games\Victoria-3\game\localization\english']
TARGET_EXTENSIONS = ('.gui', '.yml')
OUTPUT_FILENAME = 'output_counts.txt'
GRAPHML_FILENAME = 'output_graph' # Filename for the graph output
WRITE_TO_TEXT_FILE = True
LIMIT = 250  # Increased limit for a more interesting graph
ANALYSIS_MODE = 'pairs' # -- TOGGLE: Change this to 'units' or 'pairs' to switch analysis type


def create_graphml_from_pairs(pairs_data, max_weight, limit, filename):
    """
    Creates a directed graph from pairs data and saves it as a GraphML file.

    Args:
        pairs_data (list): A list of ((part1, part2), count) tuples.
        max_weight (int): The highest count found, for normalization.
        limit (int): The number of top pairs to include in the graph.
        filename (str): The path to save the .graphml file.
    """
    print(f"Generating GraphML file at '{filename}'...")

    # Create a new directed graph
    G = nx.DiGraph()

    # Sort pairs_data by count in descending order
    # Get top pairs for visualization

    pairs_data.sort(key=lambda x: x[1], reverse=True)
    top_pairs = pairs_data[:limit]
    
    if not top_pairs:
        print("No pairs to generate a graph from.")
        return

    # Get the unique nodes from the top pairs
    nodes = set()
    for (source, target), count in top_pairs:
        nodes.add(source)
        nodes.add(target)
    
    # Add nodes with a 'label' attribute
    for node_name in nodes:
        G.add_node(node_name, label=node_name)

    # Add edges with 'weight' and 'label' attributes
    for (source, target), count in top_pairs:
        # This is the same weight logic as your original code
        normalized_weight = 10 * count / max_weight
        if normalized_weight < 1:
            normalized_weight = 1
            
        # Add an edge from source to target.
        # We add 'weight' for analysis/thickness and 'label' for visualization.
        G.add_edge(source, target, weight=normalized_weight, label=str(count))

    # Write the graph to a file in GraphML format.
    # The `infer_numeric_types=True` helps yEd recognize numbers.
    nx.write_graphml(G, filename, infer_numeric_types=True)
    print("GraphML file generation complete.")


def find_and_count(root_dirs, extensions, mode='units'):
    """
    Recursively finds values within square brackets, then counts either the
    individual parts or adjacent pairs of parts.
    Returns the sorted counts and the maximum count found.
    """
    counts = Counter()
    bracket_pattern = re.compile(r'\[(.*?)\]')
    identifier_pattern = re.compile(r'[a-zA-Z_][a-zA-Z0-9_]*')
    max_weight = 0

    for folder in root_dirs:
        print(f"Starting search in '{folder}' for files ending with {extensions}...")
        p = Path(folder)
        all_files = []
        for filename in p.rglob('*.*'):
            all_files.append(filename)
        for filename in all_files:
            if filename.suffix in extensions:
                # if filename.endswith(extensions):
                # file_path = os.path.join(dirpath, filename)
                try:
                    with open(filename, 'r', encoding='utf-8-sig') as f:
                        content = f.read()
                        matches = bracket_pattern.findall(content)
                        for match in matches:
                            parts = identifier_pattern.findall(match)
                            if not parts:
                                continue
                            if mode == 'units':
                                counts.update(parts)
                            elif mode == 'pairs':
                                for i in range(len(parts) - 1):
                                    pair = (parts[i], parts[i+1])
                                    counts.update([pair])
                except Exception as e:
                    print(f"Could not read file {file_path}: {e}")
    
    if not counts:
        return [], 0
    
    # Find the max count among all items
    max_weight = counts.most_common(1)[0][1]

    return counts.most_common(), max_weight

# --- Main execution block ---
if __name__ == "__main__":
    if ANALYSIS_MODE not in ['units', 'pairs']:
        raise ValueError(f"Invalid ANALYSIS_MODE: '{ANALYSIS_MODE}'. Please choose 'units' or 'pairs'.")

    print(f"Running analysis in '{ANALYSIS_MODE}' mode...")
    results, max_w = find_and_count(FOLDERS, TARGET_EXTENSIONS, mode=ANALYSIS_MODE)

    if results:
        if WRITE_TO_TEXT_FILE:
            print(f"\nAnalysis complete. Writing text results to '{OUTPUT_FILENAME}'...")
            with open(OUTPUT_FILENAME, 'w', encoding='utf-8') as f:
                if ANALYSIS_MODE == 'units':
                    f.write("--- Found Units (Sorted by Count) ---\n")
                    for part, count in results:
                        f.write(f"{part}: {count}\n")
                elif ANALYSIS_MODE == 'pairs':
                    f.write("--- Found Pairs (Sorted by Count) ---\n")
                    for (part1, part2), count in results:
                        f.write(f"{part1} -> {part2}: {count}\n")
            print(f"\nFound a total of {len(results)} unique {ANALYSIS_MODE}.")

        if ANALYSIS_MODE == 'pairs':
            create_graphml_from_pairs(results, max_w, LIMIT, f"{GRAPHML_FILENAME}_{LIMIT}.graphml")
    else:
        print("\nNo values found in square brackets.")