import re

def _extract_connections_from_string(text):
    """
    Parses a string to find connections between properties, callers, and callees.

    This function uses a multi-pass regex approach to robustly handle:
    1.  Property/Method access (A.B)
    2.  Chained calls (A().B)
    3.  Function-to-parameter connections (F(P))
    4.  Caller-to-callee connections (F(G()))

    Returns a list of (source, target) tuples.
    """
    connections = set()

    # A robust regex for a valid identifier
    ID = r'[a-zA-Z_][a-zA-Z0-9_]*'

    # --- Pass 1: Find all direct property and chained call connections ---
    # This pattern finds connections across a dot '.'.
    # It matches:
    #   - A.B              (e.g., Goods.ToggleTaxation)
    #   - A().B            (e.g., GetScriptedGui().Execute)
    #   - A(anything).B    (e.g., SetRoot( ... ).End)
    # The `\([^)]*\)` part is a simplification for `(...)` but is effective here.
    # We use a loop because finditer is more memory-efficient for complex regex.
    chain_pattern = re.compile(rf"({ID})\s*(?:\([^)]*\))?\s*\.\s*({ID})")
    for match in chain_pattern.finditer(text):
        lhs_head, rhs_head = match.groups()
        connections.add((lhs_head, rhs_head))

    # --- Pass 2: Find all function-to-argument and caller-to-callee connections ---
    # This pattern finds a function name and its complete argument block,
    # correctly handling one level of nested parentheses inside the arguments.
    func_pattern = re.compile(rf"({ID})\s*\(((?:[^()]|\([^()]*\))*)\)")
    for func_name, args_block in func_pattern.findall(text):
        if not args_block.strip():
            continue

        # A. Connect the function to any CALLEES within its arguments
        # e.g., In "Execute(ToggleTaxation(GetPlayer))", connect Execute -> ToggleTaxation
        # This finds any identifier that is immediately followed by an open parenthesis.
        callee_pattern = re.compile(rf"({ID})\s*\(")
        for callee_match in callee_pattern.finditer(args_block):
            connections.add((func_name, callee_match.group(1)))

        # B. Connect the function to its simple PARAMETERS
        # To avoid connecting to every part of a complex expression, we only look for
        # parameters that are simple identifiers, not part of a call or property access.
        # We split by comma and process each argument part.
        args = args_block.split(',')
        for arg in args:
            arg = arg.strip()
            # A simple parameter is one that is just an identifier (e.g., "Country").
            # The `re.fullmatch` ensures the entire argument string is just the identifier.
            if re.fullmatch(ID, arg):
                connections.add((func_name, arg))
            # Handle cases like "WarGoal.HoldsArticle" where the "head" is the relevant part.
            # We connect the function to the last part of the property chain.
            elif '.' in arg and '(' not in arg:
                identifiers_in_arg = re.findall(ID, arg)
                if identifiers_in_arg:
                    connections.add((func_name, identifiers_in_arg[-1]))

    return list(connections)