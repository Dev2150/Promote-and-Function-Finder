import os
import re
from collections import Counter

# --- Configuration ---
FOLDERS = (rf'C:\Games\Victoria-3\game\common', rf'C:\Games\Victoria-3\game\localization\english')
TARGET_EXTENSIONS = ('.gui', '.yml')
OUTPUT_FILENAME = 'output.txt'

# --- TOGGLE: Change this to 'units' or 'pairs' to switch analysis type ---
ANALYSIS_MODE = 'pairs' # or 'units'

def find_and_count(root_dirs, extensions, mode='units'):
    """
    Recursively finds values within square brackets, then counts either the
    individual parts or adjacent pairs of parts.

    Args:
        root_dirs (list): A list of folder paths to start searching from.
        extensions (tuple): A tuple of file extensions to look for.
        mode (str): The analysis mode. Can be 'units' or 'pairs'.

    Returns:
        list: A list of (item, count) tuples, sorted by count.
              If mode is 'units', item is a string.
              If mode is 'pairs', item is a tuple (part1, part2).
    """
    counts = Counter()

    # Regex to find the content inside square brackets.
    bracket_pattern = re.compile(r'\[(.*?)\]')
    
    # Regex to find valid "identifiers" within the bracketed content.
    identifier_pattern = re.compile(r'[a-zA-Z_][a-zA-Z0-9_]*')

    for folder in root_dirs:
        print(f"Starting search in '{folder}' for files ending with {extensions}...")
        for dirpath, _, filenames in os.walk(folder):
            for filename in filenames:
                if filename.endswith(extensions):
                    file_path = os.path.join(dirpath, filename)
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8-sig') as f:
                            content = f.read()
                            
                            matches = bracket_pattern.findall(content)
                            
                            for match in matches:
                                parts = identifier_pattern.findall(match)
                                
                                if not parts:
                                    continue

                                # --- KEY LOGIC CHANGE BASED ON MODE ---
                                if mode == 'units':
                                    counts.update(parts)
                                
                                elif mode == 'pairs':
                                    # Create pairs of adjacent items.
                                    # e.g., ['A', 'B', 'C'] becomes [('A', 'B'), ('B', 'C')]
                                    for i in range(len(parts) - 1):
                                        pair = (parts[i], parts[i+1])
                                        counts.update([pair]) # Counter.update expects an iterable

                    except Exception as e:
                        print(f"Could not read file {file_path}: {e}")

    if not counts:
        return []
        
    # Return the items sorted by frequency.
    return counts.most_common()

# --- Main execution block ---
if __name__ == "__main__":
    # Validate the chosen mode
    if ANALYSIS_MODE not in ['units', 'pairs']:
        raise ValueError(f"Invalid ANALYSIS_MODE: '{ANALYSIS_MODE}'. Please choose 'units' or 'pairs'.")

    print(f"Running analysis in '{ANALYSIS_MODE}' mode...")
    results = find_and_count(FOLDERS, TARGET_EXTENSIONS, mode=ANALYSIS_MODE)

    if results:
        print(f"\nAnalysis complete. Writing results to '{OUTPUT_FILENAME}'...")
        with open(OUTPUT_FILENAME, 'w', encoding='utf-8') as f:
            # --- DYNAMIC OUTPUT FORMATTING ---
            if ANALYSIS_MODE == 'units':
                f.write("--- Found Units (Sorted by Count) ---\n")
                for part, count in results:
                    f.write(f"{part}: {count}\n")
                
            elif ANALYSIS_MODE == 'pairs':
                f.write("--- Found Pairs (Sorted by Count) ---\n")
                # Unpack the tuple for pairs: e.g., (('A', 'B'), 4)
                for (part1, part2), count in results:
                    f.write(f"{count:6}\t{part1:20} . {part2}\n")

        print(f"\nFound a total of {len(results)} unique {ANALYSIS_MODE}.")
    else:
        print("\nNo values found in square brackets.")