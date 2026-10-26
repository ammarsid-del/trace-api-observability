import {useCallback, useEffect, useState} from 'react';
import {Activity, AlertTriangle, ArrowUpRight, Clock3, RefreshCw, Server, Zap} from 'lucide-react';

type Summary = {requests:number;average_latency_ms:number;server_errors:number;error_rate_percent:number;window_hours:number};
type Endpoint = {path:string;method:string;requests:number;average_latency_ms:number;server_errors:number};
type Point = {hour:string;requests:number};
const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function Sparkline({points}:{points:Point[]}) {
  if (!points.length) return <div className="empty">No request data in this time window. Generate traffic with <code>/demo/42</code>.</div>;
  const values=points.map(p=>p.requests), max=Math.max(1,...values);
  const coords=values.map((v,i)=>`${20+(i*660/Math.max(1,values.length-1))},${170-v*125/max}`).join(' ');
  return <div className="chart"><svg viewBox="0 0 700 200" role="img" aria-label="Request volume by hour"><line x1="20" y1="170" x2="680" y2="170" stroke="#303949"/><polyline points={coords} fill="none" stroke="#64b5ff" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"/>{values.map((v,i)=><circle key={i} cx={20+i*660/Math.max(1,values.length-1)} cy={170-v*125/max} r="4" fill="#64b5ff"/>)}</svg><div className="axis"><span>{new Date(points[0].hour).toLocaleString()}</span><span>{new Date(points[points.length-1].hour).toLocaleString()}</span></div></div>;
}
export default function Dashboard(){
  const [hours,setHours]=useState(24);
  const [summary,setSummary]=useState<Summary|null>(null);
  const [endpoints,setEndpoints]=useState<Endpoint[]>([]);
  const [series,setSeries]=useState<Point[]>([]);
  const [error,setError]=useState('');
  const [loading,setLoading]=useState(false);
  const [lastUpdated,setLastUpdated]=useState('');
  const refresh=useCallback(async()=>{
    setLoading(true);
    try{
      const [s,e,t]=await Promise.all(['summary','endpoints','timeseries'].map(name=>fetch(`${API}/metrics/${name}?hours=${hours}`).then(async r=>{if(!r.ok)throw new Error(`API returned ${r.status}`);return r.json()})));
      setSummary(s);setEndpoints(e);setSeries(t);setError('');setLastUpdated(new Date().toLocaleTimeString());
    }catch(e){setError(e instanceof Error?e.message:'Unable to reach the API');}
    finally{setLoading(false);}
  },[hours]);
  useEffect(()=>{void refresh();const timer=setInterval(()=>void refresh(),15000);return()=>clearInterval(timer)},[refresh]);
  return <div className="app">
    <aside className="sidebar"><div className="brand"><span className="brand-mark"><Activity size={20}/></span><span>trace<span className="brand-dot">.</span></span></div><div className="side-label">WORKSPACE</div><div className="nav active"><Activity size={17}/> Overview</div><div className="nav"><Server size={17}/> API Monitoring</div><div className="side-footer">TRACE OBSERVABILITY<br/><span>Developer preview · v0.2</span></div></aside>
    <main className="main"><div className="topbar"><div><div className="eyebrow">OBSERVABILITY / OVERVIEW</div><h1>API Overview</h1><p>Monitor traffic, latency, and reliability across your endpoints.</p></div><div className="controls"><select aria-label="Time window" value={hours} onChange={e=>setHours(Number(e.target.value))}><option value={1}>Last hour</option><option value={24}>Last 24 hours</option><option value={168}>Last 7 days</option></select><button onClick={()=>void refresh()} disabled={loading}><RefreshCw size={16} className={loading?'spin':''}/> Refresh</button></div></div>
    <div className="status"><span className="pulse"/> Connected to {API} <span className="updated">{lastUpdated? `Updated ${lastUpdated}`:'Loading...'}</span></div>
    {error&&<div className="error"><AlertTriangle size={18}/> Could not load metrics: {error}. Check that the backend is running at {API}.</div>}
    <section className="cards">
      <div className="metric"><div className="metric-label">TOTAL REQUESTS <Activity size={18}/></div><strong>{summary?.requests.toLocaleString()??'—'}</strong><div className="metric-sub">Within selected window <ArrowUpRight size={14}/></div></div>
      <div className="metric"><div className="metric-label">AVG LATENCY <Clock3 size={18}/></div><strong>{summary?summary.average_latency_ms.toFixed(1):'—'} <small>ms</small></strong><div className="metric-sub">Mean response time</div></div>
      <div className="metric"><div className="metric-label">SERVER ERRORS <AlertTriangle size={18}/></div><strong>{summary?.server_errors??'—'}</strong><div className="metric-sub">HTTP 5xx responses</div></div>
      <div className="metric"><div className="metric-label">ERROR RATE <Zap size={18}/></div><strong>{summary?summary.error_rate_percent.toFixed(2):'—'}<small>%</small></strong><div className="metric-sub">5xx / total requests</div></div>
    </section>
    <section className="panel"><div className="panel-heading"><div><h2>Request volume</h2><p>Hourly requests across the selected window</p></div><span className="pill">LIVE DATA</span></div><Sparkline points={series}/></section>
    <section className="panel"><div className="panel-heading"><div><h2>Endpoint performance</h2><p>Traffic and response time by route</p></div><span className="pill">{endpoints.length} endpoints</span></div><div className="table-scroll"><table><thead><tr><th>ENDPOINT</th><th>METHOD</th><th>REQUESTS</th><th>AVG LATENCY</th><th>5XX ERRORS</th></tr></thead><tbody>{endpoints.map(e=><tr key={e.method+e.path}><td><code>{e.path}</code></td><td><span className="method">{e.method}</span></td><td>{e.requests.toLocaleString()}</td><td>{e.average_latency_ms.toFixed(2)} ms</td><td>{e.server_errors}</td></tr>)}{!endpoints.length&&<tr><td colSpan={5} className="empty-cell">No endpoint metrics yet.</td></tr>}</tbody></table></div></section>
    <footer>Trace · Open-source API observability MVP</footer>
    </main></div>
}
