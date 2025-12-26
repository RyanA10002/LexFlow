"""
SandboxRunner runs user cells inside a short-lived Docker container.

Design:
- Create a temporary dir for the task, write `task.py` that contains the cell execution logic
- Start a python:3.10-slim container with the temp dir mounted read-only for safety where possible
- Run the container with CPU/memory limits and a timeout
- Capture stdout/stderr and a JSON result file written by inside container script

This is a prototype. For production consider:
- gVisor / Firecracker for stronger isolation
- network egress restrictions
- removing host mounts and using images that include required libs
"""
import tempfile, os, shutil, json, uuid, subprocess, textwrap, time
from docker import from_env as docker_from_env

class SandboxRunner:
    def __init__(self):
        self.docker = docker_from_env()

    def _build_task_script(self, payload):
        # Build a small Python script that executes the cell and writes result.json
        cell_type = payload.get("cell_type")
        src = payload.get("source", "")
        connection = payload.get("connection")
        result_name = payload.get("result")
        dtype = payload.get("dtype", "pandas")

        # The inner script writes a JSON file with result and may create a .pkl with dataframe if needed.
        script = f'''
import sys, json, traceback, time
import pandas as pd
import polars as pl
import duckdb
from sqlalchemy import create_engine

payload = {json.dumps(payload)}
out = {{}}
try:
    cell_type = payload.get("cell_type")
    if cell_type == "sql":
        sql = payload.get("source")
        conn = payload.get("connection") or "duckdb:///:memory:"
        if conn.startswith("duckdb"):
            # duckdb: allow file path after duckdb:///
            if "///" in conn:
                dbpath = conn.split("///",1)[1]
                con = duckdb.connect(database=dbpath)
            else:
                con = duckdb.connect(":memory:")
            df = con.execute(sql).fetchdf()
            df = pd.DataFrame(df)
        else:
            eng = create_engine(conn)
            with eng.connect() as c:
                df = pd.read_sql(sql, c)
        # optionally persist as parquet for host to pick up
        if payload.get("result"):
            df.to_parquet(payload.get("result") + ".parquet")
        out = {"type":"dataframe","columns":list(df.columns),"rows":len(df)}
    elif cell_type == "python":
        # execute python with a small globals dict; user code can read variables from payload['session_vars'] if provided
        _locals = {{}}
        _globals = {{}}
        code = payload.get("source")
        exec(code, _globals, _locals)
        out = {{"type":"python","stdout":""}}
    else:
        out = {{"type":"unknown","info":"unsupported cell type"}}
except Exception as e:
    out = {{"type":"error","error":str(e),"traceback":traceback.format_exc()}}
# write result
with open("result.json","w") as f:
    json.dump(out,f)
'''
        return script

    def execute_in_sandbox(self, payload, task_id=None, timeout=20):
        tmpdir = tempfile.mkdtemp(prefix="task_")
        try:
            script = self._build_task_script(payload)
            script_path = os.path.join(tmpdir, "task.py")
            with open(script_path, "w") as f:
                f.write(script)

            # Run docker container
            image = "python:3.10-slim"
            container = self.docker.containers.run(
                image,
                command=["python","/work/task.py"],
                volumes={tmpdir: {"bind": "/work", "mode": "rw"}},
                detach=True,
                stderr=True,
                stdout=True,
                mem_limit="512m",
                cpu_quota=50000,  # limit CPU
                network_disabled=False,  # set True in locked-down env
                security_opt=["no-new-privileges"]
            )
            start = time.time()
            while True:
                container.reload()
                status = container.status
                if status in ("exited", "dead"):
                    break
                if time.time() - start > timeout:
                    container.kill()
                    raise TimeoutError("Sandbox execution timed out")
                time.sleep(0.2)

            # fetch result.json
            bits, stat = container.get_archive("/work/result.json")
            file_bytes = b""
            for chunk in bits:
                file_bytes += chunk
            # Docker wraps tar archive; extract small file by writing tar blob to temp and reading
            import tarfile, io
            tar_buffer = io.BytesIO(file_bytes)
            tar = tarfile.open(fileobj=tar_buffer)
            member = tar.extractfile("result.json")
            result_data = json.loads(member.read().decode("utf-8"))
            # if dataframe persisted, load basic schema info
            if payload.get("result"):
                parquet_path = os.path.join(tmpdir, payload.get("result") + ".parquet")
                if os.path.exists(parquet_path):
                    import pyarrow.parquet as pq
                    pf = pq.ParquetFile(parquet_path)
                    num_rows = pf.metadata.num_rows
                    cols = pf.schema.names
                    result_data.setdefault("parquet", {"rows": num_rows, "columns": cols})
            container.remove()
            return result_data
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)
