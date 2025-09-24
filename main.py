import re
from collections import Counter
from pathlib import Path

from Localization import HEADER, FOOTER, print_node, print_edge
from Node import Node
from Parser import _extract_connections_from_string

# --- Configuration ---f
FOLDERS = [rf'C:\Games\Victoria-3\game\gui']
TARGET_EXTENSIONS = ('.gui', '.yml')
OUTPUT_FILENAME = 'output_counts.txt'
GRAPHML_FILENAME = 'output_graph'
WRITE_TO_TEXT_FILE = True
ANALYSIS_MODE = 'pairs' # -- TOGGLE: 'units' or 'pairs'
edge_style = 'percentile' # -- TOGGLE: 'percent' / 'percentile'
LIMIT = 1000  # Increased limit for a more interesting graph

def prepare_graphml_from_pairs(pairs_data, max_weight, limit, filename):
    """
    Creates a directed graph from pairs data and saves it as a GraphML file.
    """

    # --- Step 1: Get the top pairs and find all unique node names ---
    # pairs_data.sort(key=lambda x: x[1], reverse=True)
    top_pairs = pairs_data
    if limit > 0:
        top_pairs = top_pairs[:limit]


    if not top_pairs:
        print("No pairs to generate a graph from.")
        return

    # Get the unique node names from the top pairs
    unique_node_names = set()
    for (source_name, target_name), count in top_pairs:
        unique_node_names.add(source_name)
        unique_node_names.add(target_name)
    unique_node_names = sorted(list(unique_node_names)) # sorted for consistent IDs

    # --- Step 2: Create Node objects and the name-to-ID mapping ---
    nodes = []
    name_to_id = {}
    for i, name in enumerate(unique_node_names):
        node_id = i
        nodes.append(Node(id=node_id, name=name))
        name_to_id[name] = node_id

    # Header
    file_contents = HEADER

    # Add node definitions
    for node in nodes:
        file_contents += print_node(node)


    # Add edge definitions
    count_edges = len(top_pairs)
    prev_count = 0
    normalized_weight = 1
    for i, ((source_name, target_name), count) in enumerate(top_pairs):
        source_id = name_to_id[source_name]
        target_id = name_to_id[target_name]

        # Normalize weight for line thickness
        if edge_style == 'percent':
            normalized_weight = max(1.0, 10 * count / max_weight)
        elif edge_style == 'percentile':
            if prev_count != count:
                normalized_weight = max(1.0, 10 * (count_edges - i) / count_edges)
        else:
            raise 'Undefined edge style'

        file_contents += print_edge(i, source_id, target_id, count, normalized_weight)
        count_prev = count


    # Footer
    file_contents += FOOTER

    # Write the final string to a file
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(file_contents)

    print(f"GraphML file generation complete: {filename}")


def find_and_count(root_dirs, extensions, mode='units'):
    """
    Finds and counts units or pairs from files.
    This function now works exclusively with strings for simplicity and correctness.
    """
    counts = Counter()
    bracket_pattern = re.compile(r'\[(.*?)\]')
    identifier_pattern = re.compile(r'[a-zA-Z_][a-zA-Z0-9_]*')

    for folder in root_dirs:
        print(f"Searching in '{folder}' for files ending with {extensions}...")
        p = Path(folder)
        for file_path in p.rglob('*'):
            if file_path.suffix in extensions:
                try:
                    with open(file_path, 'r', encoding='utf-8-sig') as f:
                        content = f.read()
                        matches = bracket_pattern.findall(content)
                        for match in matches:
                            connections = _extract_connections_from_string(match)
                            if connections:
                                counts.update(connections)
                            # if not parts:
                            #     continue

                            # if mode == 'units':
                            #     counts.update(parts)
                            # elif mode == 'pairs':
                            #     for i in range(len(parts) - 1):
                            #         pair = (parts[i], parts[i+1])
                            #         counts.update([pair]) # update expects an iterable
                except Exception as e:
                    print(f"Could not read file {file_path}: {e}")

    if not counts:
        return [], 0

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
            output_path = Path(OUTPUT_FILENAME)
            print(f"\nAnalysis complete. Writing text results to '{output_path}'...")
            with open(output_path, 'w', encoding='utf-8') as f:
                if ANALYSIS_MODE == 'units':
                    f.write("--- Found Units (Sorted by Count) ---\n")
                    for part, count in results:
                        f.write(f"{part}: {count}\n")
                elif ANALYSIS_MODE == 'pairs':
                    f.write("--- Found Pairs (Sorted by Count) ---\n")
                    for (part1, part2), count in results:
                        f.write(f"{part1} -> {part2}: {count}\n")
            print(f"Found a total of {len(results)} unique {ANALYSIS_MODE}.")

        if ANALYSIS_MODE == 'pairs':
            graph_filename = f"{GRAPHML_FILENAME}_{LIMIT}.graphml"
            prepare_graphml_from_pairs(results, max_w, LIMIT, graph_filename)
    else:
        print("\nNo values found in square brackets.")