import React, {useState} from "react";
import axios from "axios";

export default function SqlCell({initialSQL="", connection="", resultVar="df", dtype="pandas"}) {
  const [sql, setSql] = useState(initialSQL);
  const [taskId, setTaskId] = useState(null);
  const [result, setResult] = useState(null);
  const run = async () => {
    const resp = await axios.post("/api/execute", {
      cell_type: "sql",
      source: sql,
      connection,
      result: resultVar,
      dtype
    });
    const id = resp.data.task_id;
    setTaskId(id);
    // Poll for result (simple)
    const poll = async () => {
      const r = await axios.get(`/api/result/${id}`);
      if (r.data.ready) {
        setResult(r.data.result);
      } else {
        setTimeout(poll, 500);
      }
    };
    poll();
  };
  return (
    <div style={{border:"1px solid #ddd", padding:12, borderRadius:6}}>
      <textarea style={{width:"100%",height:120}} value={sql} onChange={e=>setSql(e.target.value)} />
      <div style={{display:"flex",gap:8, marginTop:8}}>
        <button onClick={run}>Run SQL</button>
        <div>Result var: <b>{resultVar}</b></div>
        <div>Task: {taskId}</div>
      </div>
      <pre style={{marginTop:12}}>{result && JSON.stringify(result, null, 2)}</pre>
    </div>
  );
}
