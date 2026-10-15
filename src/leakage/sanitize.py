"""Code-only notebook extraction with explicit exclusions and source locations."""
import ast
import io
import tokenize

def clean_source(source):
    # Preserve every physical line. Remove comments and docstrings so prior
    # conclusions and notebook narrative cannot become model evidence.
    lines = source.splitlines(keepends=True)
    for t in tokenize.generate_tokens(io.StringIO(source).readline):
        if t.type == tokenize.COMMENT:
            row, col = t.start
            lines[row - 1] = lines[row - 1][:col] + " " * (t.end[1] - col) + lines[row - 1][t.end[1]:]
    source = "".join(lines)
    tree = ast.parse(source)
    for n in ast.walk(tree):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and n.body:
            first = n.body[0]
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
                begin, end = first.lineno - 1, first.end_lineno - 1
                if begin == end:
                    lines[begin] = lines[begin][:first.col_offset] + "''" + lines[begin][first.end_col_offset:]
                else:
                    prefix = lines[begin][:first.col_offset]
                    suffix = lines[end][first.end_col_offset:]
                    lines[begin] = prefix + "(''\n"
                    for i in range(begin + 1, end):
                        lines[i] = "\n"
                    lines[end] = " " * first.col_offset + ")" + suffix
    return "".join(lines)

def extract_notebook(notebook):
    parts, mapping, row = [], [], 1
    for cell_index, cell in enumerate(notebook.get("cells", [])):
        if cell.get("cell_type") != "code":
            continue
        source = cell.get("source", [])
        source = source if isinstance(source, str) else "".join(source)
        if not source.endswith("\n"):
            source += "\n"
        for cell_line in range(1, len(source.splitlines()) + 1):
            mapping.append({"line": row, "cell_index": cell_index, "cell_line": cell_line})
            row += 1
        parts.append(source)
    return clean_source("".join(parts)), mapping

