"""
Notebook converter utilities:
- .ngnb (JSON) <-> script (.py) conversion
- The .ngnb format is simple JSON with metadata and list of cells.
"""
import json, nbformatpip ins, textwrap

def ngnb_to_py(ngnb_path, py_path):
    with open(ngnb_path) as f:
        nb = json.load(f)
    parts = []
    for cell in nb.get("cells", []):
        if cell["type"] == "markdown":
            parts.append('# %% [markdown]\n' + '\n'.join(["# " + line for line in cell["source"].splitlines()]))
        elif cell["type"] == "sql":
            meta = cell.get("meta", {})
            header = f'%%sql connection={meta.get("connection","duckdb:///:memory:")} result={meta.get("result","")} dtype={meta.get("dtype","pandas")}\n'
            parts.append('# %% [sql]\n' + header + cell["source"])
        else:
            parts.append('# %% [python]\n' + cell["source"])
    with open(py_path, "w") as f:
        f.write("\n\n".join(parts))

def py_to_ngnb(py_path, ngnb_path):
    cells = []
    with open(py_path) as f:
        raw = f.read()
    blocks = raw.split("# %%")
    for b in blocks:
        b = b.strip()
        if not b:
            continue
        if b.startswith("[markdown]"):
            src = "\n".join([line[2:] if line.startswith("# ") else line for line in b.splitlines()[1:]])
            cells.append({"type":"markdown", "source": src})
        elif b.startswith("[sql]"):
            lines = b.splitlines()[1:]
            header = lines[0]
            source = "\n".join(lines[1:])
            # parse header naive
            meta = {}
            for token in header.split():
                if "=" in token:
                    k,v = token.split("=",1)
                    meta[k]=v
            cells.append({"type":"sql","source":source,"meta":meta})
        else:
            src = "\n".join(b.splitlines()[1:])
            cells.append({"type":"python","source":src})
    with open(ngnb_path,"w") as f:
        json.dump({"cells":cells}, f, indent=2)
