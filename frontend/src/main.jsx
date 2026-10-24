import React, { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { Sparkles, Search, Image as ImageIcon, Download, Copy, Clock3, ArrowUpRight, CheckCircle2, AlertTriangle, LoaderCircle, Instagram, Linkedin, Twitter, ChevronRight, Layers3, Plus, FileText, ExternalLink, WandSparkles } from 'lucide-react';
import './styles.css';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const platforms = ['Instagram', 'LinkedIn', 'X / Twitter'];
function App() {
  const [topic, setTopic] = useState('Sustainable fashion trends');
  const [platform, setPlatform] = useState('Instagram');
  const [tone, setTone] = useState('Professional');
  const [post, setPost] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [copied, setCopied] = useState(false);
  const [health, setHealth] = useState(false);

  async function loadHistory() { try { const r = await fetch(`${API}/api/posts?limit=8`); if (r.ok) setHistory(await r.json()); } catch {} }
  useEffect(() => { fetch(`${API}/api/health`).then(r => setHealth(r.ok)).catch(() => setHealth(false)); loadHistory(); }, []);
  async function generate(e) {
    e?.preventDefault(); setError(''); setLoading(true);
    try {
      const response = await fetch(`${API}/api/generate`, { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({topic, platform, tone}) });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Could not generate the post.');
      setPost(data); await loadHistory();
    } catch (err) { setError(`${err.message}. Make sure the FastAPI backend is running on port 8000.`); }
    finally { setLoading(false); }
  }
  const captionText = post ? `${post.title}\n\n${post.caption}\n\n${post.hashtags.join(' ')}\n\n${post.call_to_action}` : '';
  async function copyPost() { try { await navigator.clipboard.writeText(captionText); setCopied(true); setTimeout(() => setCopied(false), 1800); } catch { setError('Clipboard access was blocked by the browser. Select and copy the text manually.'); } }
  function exportPost() {
    if (!post) return;
    const html = `<!doctype html><html><head><meta charset="utf-8"><title>${escapeHtml(post.title)}</title><style>body{font:16px Arial;max-width:760px;margin:40px auto;padding:0 20px;color:#20202b}img{width:100%;border-radius:16px}h1{line-height:1.15}p{line-height:1.6;white-space:pre-wrap}</style></head><body><h1>${escapeHtml(post.article_title || post.title)}</h1><article>${escapeHtml(post.article || '').replace(/\n/g, '<br>')}</article><hr><h2>${escapeHtml(post.title)}</h2><img src="${post.image_data}"/><p>${escapeHtml(post.caption)}</p><p>${escapeHtml(post.hashtags.join(' '))}</p><strong>${escapeHtml(post.call_to_action)}</strong><h2>Sources for review</h2><ul>${post.sources.map(s=>`<li><a href="${escapeHtml(s.url)}">${escapeHtml(s.title)}</a> - ${escapeHtml(s.credibility)}</li>`).join('')}</ul><p><small>Review factual claims and sources before publishing.</small></p></body></html>`;
    const blob = new Blob([html], {type:'text/html;charset=utf-8'}); const url = URL.createObjectURL(blob); const a = document.createElement('a'); a.href=url; a.download=`marketing-post-${post.id || 'draft'}.html`; a.click(); URL.revokeObjectURL(url);
  }
  function chooseHistory(item) { setPost({...item, platform, tone, hashtags: Array.isArray(item.hashtags) ? item.hashtags : item.hashtags.split(/\s+/).filter(Boolean), verification:{summary:'Saved post loaded from history.',warnings:['Review source details and claims before publishing.'],confidence:'Basic'}}); setTopic(item.topic); }
  return <div className="app-shell">
    <aside className="sidebar">
      <div className="brand"><div className="brand-icon"><Layers3 size={20}/></div><div><strong>Arlo<span>ai</span></strong><small>CONTENT ENGINE</small></div></div>
      <div className="workspace-label">WORKSPACE</div>
      <button className="nav-item active"><WandSparkles size={17}/> Content studio <span className="nav-dot"/></button>
      <button className="nav-item" onClick={loadHistory}><Clock3 size={17}/> Recent projects</button>
      <div className="sidebar-section"><div className="workspace-label">YOUR WORK</div><div className="history-list">{history.length ? history.slice(0,6).map(item=><button key={item.id} className="history-item" onClick={()=>chooseHistory(item)}><span className="history-bullet"/><span>{item.topic}</span></button>) : <p className="empty-history">Your generated posts will appear here.</p>}</div></div>
      <div className="sidebar-bottom"><div className="profile"><div className="avatar">K</div><div><strong>Creator workspace</strong><small>Personal studio</small></div><ChevronRight size={16}/></div><div className="api-status"><span className={health?'status-dot':'status-dot offline'}/>{health ? 'Backend connected' : 'Backend not connected'}</div></div>
    </aside>
    <main className="main-area">
      <header className="topbar"><div className="breadcrumbs">Workspace <ChevronRight size={14}/> <strong>Content studio</strong></div><div className="top-actions"><span className="mode-pill"><span className="green-dot"/> {post?.mode === 'live' ? 'Live services' : 'Prototype mode'}</span><div className="top-avatar">K</div></div></header>
      <div className="page-content">
        <section className="intro"><div className="eyebrow"><Sparkles size={14}/> AI-POWERED CREATIVE WORKFLOW</div><h1>Turn ideas into<br/><span>content that connects.</span></h1><p>Research a topic, shape your message, and create a ready-to-review social post in one place.</p></section>
        <div className="studio-grid">
          <section className="panel editor-panel"><div className="panel-heading"><div className="step-icon"><WandSparkles size={18}/></div><div><h2>Build your post</h2><p>Start with a topic. We’ll handle the first draft.</p></div><span className="step-label">STEP 01</span></div>
            <form onSubmit={generate}>
              <label className="field-label" htmlFor="topic">What do you want to talk about?</label><textarea id="topic" value={topic} onChange={e=>setTopic(e.target.value)} maxLength={300} placeholder="e.g. The future of sustainable fashion" required minLength={3}/><div className="field-meta"><span>Be specific for better results</span><span>{topic.length}/300</span></div>
              <div className="field-label platform-label">Choose a platform</div><div className="platform-options">{platforms.map(p=><button type="button" key={p} onClick={()=>setPlatform(p)} className={`platform-option ${platform===p?'selected':''}`}>{p==='Instagram'?<Instagram size={16}/>:p==='LinkedIn'?<Linkedin size={16}/>:<Twitter size={16}/>}<span>{p}</span>{platform===p&&<CheckCircle2 size={14} className="selected-check"/>}</button>)}</div>
              <label className="field-label" htmlFor="tone">Writing tone</label><select id="tone" value={tone} onChange={e=>setTone(e.target.value)}><option>Professional</option><option>Friendly</option><option>Bold</option><option>Educational</option><option>Playful</option></select>
              <div className="workflow-mini"><div className="mini-step"><Search size={15}/><span>Research</span></div><ChevronRight size={13}/><div className="mini-step"><Sparkles size={15}/><span>Write</span></div><ChevronRight size={13}/><div className="mini-step"><ImageIcon size={15}/><span>Visual</span></div></div>
              {error&&<div className="error-box"><AlertTriangle size={16}/><span>{error}</span></div>}
              <button className="generate-button" type="submit" disabled={loading||topic.trim().length<3}>{loading?<><LoaderCircle size={18} className="spin"/> Creating your post...</>:<><Sparkles size={17}/> Generate content <ArrowUpRight size={17}/></>}</button>
              <div className="secure-note"><span className="tiny-lock">⌑</span> Your API keys stay on the backend. Demo mode works without keys.</div>
            </form>
          </section>
          <section className="panel article-panel"><div className="panel-heading preview-heading"><div className="step-icon muted"><FileText size={18}/></div><div><h2>Website article</h2><p>Long-form draft based on extracted source content.</p></div><span className="draft-label">{post?.article ? 'ARTICLE' : 'WAITING'}</span></div>{post ? <div className="article-content"><h3>{post.article_title || post.title}</h3><p className="article-note">Generated from available source text. Verify claims and citations before publishing.</p><article>{post.article || 'No article text was returned.'}</article><div className="article-actions"><button className="secondary-button" onClick={()=>navigator.clipboard.writeText(`${post.article_title || post.title}\n\n${post.article || ''}`)}><Copy size={14}/> Copy article</button></div></div> : <div className="article-empty">Your website article will appear here after research and extraction.</div>}</section>
          <section className="panel preview-panel"><div className="panel-heading preview-heading"><div className="step-icon muted"><FileText size={18}/></div><div><h2>Post preview</h2><p>Your content, ready for a final review.</p></div><span className="draft-label">{post?'GENERATED':'AWAITING INPUT'}</span></div>
            {post ? <div className="post-result"><div className="preview-meta"><span className="platform-badge">{post.platform || platform}</span><span className={`mode-tag ${post.mode}`}>{post.mode==='live'?'Live AI':post.mode==='hybrid'?'Hybrid':'Demo draft'}</span><span className="post-id">#{post.id}</span></div><div className="generated-image-wrap"><img src={`data:image/png;base64,${post.image_data}`} alt={`Generated visual about ${post.topic}`}/><div className="image-label"><ImageIcon size={13}/> AI VISUAL CONCEPT</div></div><div className="post-copy"><h3>{post.title}</h3><p className="caption">{post.caption}</p><p className="hashtags">{post.hashtags.join(' ')}</p><p className="cta">{post.call_to_action}</p></div><div className="preview-actions"><button className="secondary-button" onClick={copyPost}><Copy size={15}/>{copied?'Copied':'Copy text'}</button><button className="primary-small" onClick={exportPost}><Download size={15}/> Export post</button></div><div className="stage-panel"><div className="verification-title"><Layers3 size={15}/> LLM & workflow activity <span>{post.stages?.length || 0} STAGES</span></div>{(post.stages || []).map((stage,i)=><div className="stage-row" key={i}><span className={`stage-status ${stage.status}`}>{stage.status==='completed'?'✓':stage.status==='failed'?'×':'!'}</span><div><strong>{stage.name}</strong><p>{stage.detail}</p></div></div>)}</div><div className="verification"><div className="verification-title"><CheckCircle2 size={16}/> Research & verification <span>Basic</span></div><p>{post.verification?.summary}</p>{post.verification?.warnings?.map((w,i)=><div className="warning-line" key={i}><AlertTriangle size={14}/>{w}</div>)}<div className="source-list"><strong>Reference sources</strong>{post.sources?.map((s,i)=><a key={i} href={s.url} target="_blank" rel="noreferrer"><span>{s.title}</span><ExternalLink size={13}/></a>)}</div></div></div> : <div className="empty-preview"><div className="empty-art"><div className="art-orbit orbit-one"/><div className="art-orbit orbit-two"/><div className="art-card"><Sparkles size={23}/><span>YOUR IDEA</span><div className="art-lines"><i/><i/><i/></div></div><div className="art-spark spark-one">✳</div><div className="art-spark spark-two">✦</div></div><h3>Your next post starts here.</h3><p>Enter a topic and generate your first draft. Your caption, hashtags, visual concept and source links will show up here.</p><div className="empty-tags"><span><Search size={13}/> Research</span><span><Sparkles size={13}/> AI copy</span><span><ImageIcon size={13}/> Visual</span></div></div>}
          </section>
        </div>
        <footer className="footer"><span>STUDIO AI <span className="footer-dot">·</span> MARKETING CONTENT ENGINE</span><span>Review every claim before publishing <span className="footer-dot">·</span> Built for creative workflows</span></footer>
      </div>
    </main>
  </div>;
}
function escapeHtml(value='') { return String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }

createRoot(document.getElementById('root')).render(<App/>);
