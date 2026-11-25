import React, { useEffect, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { ArrowDown, ArrowRight, Camera, Check, ChevronDown, CircleHelp, CloudSun, Leaf, Menu, ShieldCheck, Sprout, Upload, X } from 'lucide-react';
import './style.css';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const guides = [
  ['ধানের ব্লাস্ট', 'পাতায় চোখের মতো ধূসর দাগ। দ্রুত শনাক্ত করে আক্রান্ত অংশ আলাদা রাখুন।'],
  ['ব্রাউন স্পট', 'পাতায় ছোট বাদামি গোল দাগ। জমির পানি ও পুষ্টির ভারসাম্য দেখুন।'],
  ['পাতার স্মাট', 'পাতায় সরু গাঢ় রেখা দেখা যায়। আক্রান্ত গাছ পর্যবেক্ষণে রাখুন।'],
];

function App() {
  const [file, setFile] = useState(null), [preview, setPreview] = useState(''), [result, setResult] = useState(null), [busy, setBusy] = useState(false), [error, setError] = useState(''), [menu, setMenu] = useState(false), [cameraOpen, setCameraOpen] = useState(false);
  const input = useRef(null), videoRef = useRef(null), streamRef = useRef(null);
  useEffect(() => {
    if (!cameraOpen || !videoRef.current || !streamRef.current) return;
    videoRef.current.srcObject = streamRef.current;
    void videoRef.current.play().catch(() => setError('ক্যামেরার preview চালু করা যায়নি।'));
  }, [cameraOpen]);
  useEffect(() => () => streamRef.current?.getTracks().forEach(track => track.stop()), []);
  function choose(next) { if (!next) return; setFile(next); setPreview(URL.createObjectURL(next)); setResult(null); setError(''); }
  async function openCamera() {
    setError('');
    if (!navigator.mediaDevices?.getUserMedia) { setError('এই browser-এ camera ব্যবহার করা যাচ্ছে না। localhost বা HTTPS ব্যবহার করুন।'); return; }
    try { streamRef.current = await navigator.mediaDevices.getUserMedia({ video: { facingMode: { ideal: 'environment' } }, audio: false }); setCameraOpen(true); }
    catch { setError('ক্যামেরা চালু হয়নি। Browser permission দিন, অথবা ফাইল বেছে নিন।'); }
  }
  function closeCamera() { streamRef.current?.getTracks().forEach(track => track.stop()); streamRef.current = null; setCameraOpen(false); }
  function capturePhoto() {
    const video = videoRef.current;
    if (!video?.videoWidth || !video.videoHeight) { setError('ক্যামেরা প্রস্তুত হয়নি, আরেকটু অপেক্ষা করুন।'); return; }
    const canvas = document.createElement('canvas'); canvas.width = video.videoWidth; canvas.height = video.videoHeight;
    canvas.getContext('2d')?.drawImage(video, 0, 0, canvas.width, canvas.height);
    canvas.toBlob(blob => { if (!blob) { setError('ছবিটি সংরক্ষণ করা যায়নি। আবার চেষ্টা করুন।'); return; } choose(new File([blob], 'krishok-camera.jpg', { type: 'image/jpeg' })); closeCamera(); }, 'image/jpeg', 0.92);
  }
  async function scan() {
    if (!file) { input.current?.click(); return; }
    setBusy(true); setError(''); setResult(null);
    try {
      const data = new FormData(); data.append('image', file);
      const response = await fetch(`${API}/v1/rice/detect`, { method: 'POST', body: data });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.detail || 'এখন ফলাফল পাওয়া যাচ্ছে না।');
      setResult(payload);
    } catch (e) { setError(e.message || 'সার্ভারের সঙ্গে সংযোগ হচ্ছে না।'); }
    finally { setBusy(false); }
  }
  return <div className="page">
    <header className="nav wrap"><a className="brand" href="#home"><span className="brand-icon"><Leaf size={23}/></span><span>Krishok<span className="brand-ai"> AI</span><small>কৃষকের ডিজিটাল সঙ্গী</small></span></a><button className="menu-toggle" onClick={()=>setMenu(!menu)} aria-label="মেনু">{menu?<X/>:<Menu/>}</button><nav className={menu?'open':''}><a href="#how">যেভাবে কাজ করে</a><a href="#guide">রোগ গাইড</a><a href="#about">আমাদের সম্পর্কে</a><a className="nav-cta" href="#scan">রোগ শনাক্ত করুন <ArrowRight size={16}/></a></nav></header>
    <main>
      <section className="hero wrap" id="home"><div className="hero-copy"><div className="eyebrow"><span className="pulse"/> বাংলাদেশের কৃষকের জন্য তৈরি</div><h1>সুস্থ ধান,<br/><em>সমৃদ্ধ</em> আগামী।</h1><p>ধানের পাতার ছবি তুলুন। রোগ সম্পর্কে জানুন এবং ফসলের যত্নে সঠিক পদক্ষেপ নিন—সহজ বাংলায়।</p><div className="hero-actions"><a className="button primary" href="#scan">পাতা পরীক্ষা করুন <ArrowRight size={18}/></a><a className="text-link" href="#how">কীভাবে কাজ করে <ArrowDown size={16}/></a></div><div className="trust"><span className="trust-icon"><ShieldCheck size={17}/></span><span>তথ্যভিত্তিক পরামর্শ <b>·</b> আপনার ভাষায়</span></div></div><div className="hero-art"><div className="art-orbit orbit-one"/><div className="art-orbit orbit-two"/><div className="sun"/><div className="leaf-emoji">🌾</div><div className="float-card weather"><CloudSun size={19}/><span><b>ধানের যত্ন</b><small>আজই দেখে নিন</small></span></div><div className="float-card healthy"><span className="check"><Check size={15}/></span><span><b>সচেতন চাষ</b><small>ভালো ফসলের প্রথম ধাপ</small></span></div><span className="art-caption">প্রযুক্তি যখন মাঠের পাশে</span></div></section>
      <section className="stats"><div className="wrap stats-inner"><div><span className="stat-icon"><Sprout/></span><strong>৬</strong><small>ধানের রোগ ও সুস্থ পাতা</small></div><div><span className="stat-icon"><CircleHelp/></span><strong>সহজ</strong><small>বাংলায় তথ্য ও দিকনির্দেশনা</small></div><div><span className="stat-icon"><ShieldCheck/></span><strong>সচেতন</strong><small>সঠিক যত্নে সহায়ক তথ্য</small></div></div></section>
      <section className="scan-section wrap" id="scan"><div className="section-intro"><div className="eyebrow">AI দিয়ে প্রাথমিক পরীক্ষা</div><h2>পাতার ছবি দিন,<br/>জানুন কী করতে হবে।</h2><p>পরিষ্কার আলোতে আক্রান্ত পাতার কাছ থেকে একটি ছবি তুলুন। ফলাফল পেতে কয়েক মুহূর্ত লাগবে।</p><ul className="check-list"><li><Check size={16}/> ঝাপসা নয় এমন ছবি বাছুন</li><li><Check size={16}/> পাতার দাগ স্পষ্ট রাখুন</li><li><Check size={16}/> প্রয়োজনে কৃষি বিশেষজ্ঞের পরামর্শ নিন</li></ul></div><div className="upload-card"><div className="upload-heading"><span className="upload-icon"><Leaf size={20}/></span><div><b>ধানের পাতা পরীক্ষা</b><small>JPG, PNG বা WEBP · সর্বোচ্চ ১০ MB</small></div></div><input ref={input} type="file" accept="image/jpeg,image/png,image/webp" hidden onChange={e=>choose(e.target.files?.[0])}/>{preview?<div className="preview-wrap"><img src={preview} alt="আপলোড করা ধানের পাতা"/><button onClick={()=>{setFile(null);setPreview('');setResult(null)}} className="remove" aria-label="ছবি সরান"><X size={17}/></button></div>:<button className="dropzone" onClick={()=>input.current?.click()} onDragOver={e=>e.preventDefault()} onDrop={e=>{e.preventDefault();choose(e.dataTransfer.files?.[0])}}><span className="upload-circle"><Upload size={22}/></span><b>এখানে ছবি দিন</b><span>অথবা <u>ফাইল বেছে নিন</u></span></button>}<button className="camera-action" onClick={()=>void openCamera()}><Camera size={17}/> ক্যামেরা দিয়ে ছবি তুলুন</button><button className="button primary scan-button" onClick={scan} disabled={busy}>{busy?'পরীক্ষা করা হচ্ছে…':<>রোগ পরীক্ষা করুন <ArrowRight size={17}/></>}</button>{error&&<div className="message error">{error}</div>}{result&&<div className="message success"><span className="result-kicker">প্রাথমিক ফলাফল</span><b>{result.diseaseName==='Healthy'?'পাতা সুস্থ':result.diseaseName}</b><span>মডেলের confidence {Math.round(result.confidence*100)}% · এটি প্রাথমিক AI মূল্যায়ন</span></div>}<p className="privacy"><ShieldCheck size={14}/> ছবি শুধু পরীক্ষার জন্য পাঠানো হয়।</p></div></section>
      <section className="how" id="how"><div className="wrap"><div className="center-intro"><div className="eyebrow">সহজ তিনটি ধাপ</div><h2>চাষের সিদ্ধান্তে আরও সচেতন হোন</h2></div><div className="steps"><article><span>০১</span><div className="step-icon"><Upload/></div><h3>ছবি তুলুন</h3><p>পাতার ক্ষতিগ্রস্ত অংশটি পরিষ্কার আলোতে ক্যামেরায় ধরুন।</p></article><article><span>০২</span><div className="step-icon"><Leaf/></div><h3>পরীক্ষা করুন</h3><p>AI মডেল ছবির লক্ষণ দেখে সম্ভাব্য রোগের সঙ্গে মিলিয়ে দেখে।</p></article><article><span>০৩</span><div className="step-icon"><Sprout/></div><h3>জেনে যত্ন নিন</h3><p>ফলাফল বুঝে পরের পদক্ষেপে স্থানীয় কৃষি কর্মকর্তার পরামর্শ নিন।</p></article></div></div></section>
      <section className="guide wrap" id="guide"><div className="guide-top"><div><div className="eyebrow">জানুন, চিনুন, যত্ন নিন</div><h2>ধানের পাতার রোগ গাইড</h2></div><a className="text-link" href="#scan">ছবি পরীক্ষা করুন <ArrowRight size={16}/></a></div><div className="guide-cards">{guides.map(([title,desc],i)=><article className="guide-card" key={title}><span className={`guide-mark mark-${i}`}>{i===0?'◉':i===1?'••':'〰'}</span><div><small>লক্ষণ চিনুন</small><h3>{title}</h3><p>{desc}</p><a href="#scan">পাতা পরীক্ষা করুন <ArrowRight size={14}/></a></div></article>)}</div><div className="guide-note"><CircleHelp size={17}/> রোগের লক্ষণ কাছাকাছি হতে পারে। নিশ্চিত হতে কৃষি সম্প্রসারণ অধিদপ্তর বা স্থানীয় বিশেষজ্ঞের পরামর্শ নিন।</div></section>
      <section className="bottom-cta" id="about"><div className="wrap cta-inner"><div><span className="cta-leaf"><Leaf size={20}/></span><h2>আপনার ফসল, আপনার যত্ন।</h2><p>প্রযুক্তি থাকুক কৃষকের হাতের নাগালে।</p></div><a className="button light" href="#scan">এখনই ছবি পরীক্ষা করুন <ArrowRight size={17}/></a></div></section>
    </main><footer className="wrap footer"><a className="brand" href="#home"><span className="brand-icon"><Leaf size={20}/></span><span>Krishok<span className="brand-ai"> AI</span><small>কৃষকের ডিজিটাল সঙ্গী</small></span></a><span>© ২০২৬ Krishok AI · কৃষকের পাশে প্রযুক্তি</span><a href="#guide">ব্যবহার নির্দেশনা <ChevronDown size={14}/></a></footer>
    {cameraOpen&&<div className="camera-modal" onClick={closeCamera}><section className="camera-dialog" role="dialog" aria-modal="true" aria-label="ক্যামেরা দিয়ে ছবি তুলুন" onClick={e=>e.stopPropagation()}><header><b>ক্যামেরা দিয়ে ছবি তুলুন</b><button className="remove" onClick={closeCamera} aria-label="ক্যামেরা বন্ধ করুন"><X size={18}/></button></header><video ref={videoRef} autoPlay playsInline muted/><p>ধানের পাতাটি frame-এর মধ্যে রাখুন।</p><button className="button primary" onClick={capturePhoto}><Camera size={18}/> ছবি তুলুন</button></section></div>}
  </div>
}

createRoot(document.getElementById('root')).render(<App/>);
