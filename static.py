"""
Static export: convert .ngnb notebook to a self-contained HTML file.
- Embeds cell output (tables/plots) as JSON
- Renders widgets as static controls where possible (for full interactivity use a server backend)

Usage:
python export/export_static.py notebooks/example.ngnb > out.html
"""
import json, sys, jinja2, os

TEMPLATE = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>{{ title }}</title>
  <style>body{font-family: Arial, sans-serif; padding:20px} pre{background:#f6f8fa;padding:10px}</style>
</head>
<body>
  <h1>{{ title }}</h1>
  {% for cell in cells %}
    {% if cell.type == "markdown" %}
      <div class="md">{{ cell.source }}</div>
    {% elif cell.type == "sql" %}
      <div style="border:1px solid #eee;padding:10px;margin:8px 0">
        <pre>{{ cell.source }}</pre>
        <div><b>Output:</b><pre>{{ cell.output | tojson }}</pre></div>
      </div>
    {% else %}
      <div style="border:1px solid #eee;padding:10px;margin:8px 0"><pre>{{ cell.source }}</pre></div>
    {% endif %}
  {% endfor %}
</body>
</html>
"""

def export_static(ngnb_path):
    with open(ngnb_path) as f:
        nb = json.load(f)
    # For static export ensure each cell has output embedded (user should run notebook first)
    env = jinja2.Environment()
    tpl = env.from_string(TEMPLATE)
    out = tpl.render(title=nb.get("metadata",{}).get("title","Notebook"), cells=nb["cells"])
    print(out)

if __name__ == "__main__":
    export_static(sys.argv[1])
