/* ═══════════════════════════════════════
   THREE.JS PARTICLE FIELD
═══════════════════════════════════════ */
(function() {
  const canvas = document.getElementById('three-canvas');
  const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setSize(window.innerWidth, window.innerHeight);

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 1000);
  camera.position.z = 5;

  // Particle geometry
  const count = 1200;
  const geo = new THREE.BufferGeometry();
  const pos = new Float32Array(count * 3);
  const col = new Float32Array(count * 3);
  const colors = [
    [0.427, 0.729, 0.667], // sage
    [0.306, 0.749, 0.722], // teal
    [0.608, 0.580, 0.784], // lavender
    [0.431, 0.659, 0.769], // sky
  ];
  for (let i = 0; i < count; i++) {
    pos[i*3]   = (Math.random() - 0.5) * 28;
    pos[i*3+1] = (Math.random() - 0.5) * 18;
    pos[i*3+2] = (Math.random() - 0.5) * 14;
    const c = colors[Math.floor(Math.random() * colors.length)];
    col[i*3]   = c[0]; col[i*3+1] = c[1]; col[i*3+2] = c[2];
  }
  geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  geo.setAttribute('color',    new THREE.BufferAttribute(col, 3));

  const mat = new THREE.PointsMaterial({ size: 0.032, vertexColors: true, transparent: true, opacity: 0.7, sizeAttenuation: true });
  const particles = new THREE.Points(geo, mat);
  scene.add(particles);

  // Subtle connecting lines (constellation effect)
  const lineGeo = new THREE.BufferGeometry();
  const linePos = [];
  for (let i = 0; i < 80; i++) {
    const a = Math.floor(Math.random() * count);
    const b = Math.floor(Math.random() * count);
    linePos.push(pos[a*3],pos[a*3+1],pos[a*3+2]);
    linePos.push(pos[b*3],pos[b*3+1],pos[b*3+2]);
  }
  lineGeo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(linePos), 3));
  const lineMat = new THREE.LineBasicMaterial({ color: 0x6DBAAA, transparent: true, opacity: 0.04 });
  scene.add(new THREE.LineSegments(lineGeo, lineMat));

  let mx = 0, my = 0;
  document.addEventListener('mousemove', e => {
    mx = (e.clientX / window.innerWidth  - 0.5) * 0.3;
    my = (e.clientY / window.innerHeight - 0.5) * 0.3;
  });

  let t = 0;
  function animate() {
    requestAnimationFrame(animate);
    t += 0.003;
    particles.rotation.y  = t * 0.06 + mx * 0.5;
    particles.rotation.x  = t * 0.03 - my * 0.3;
    particles.rotation.z  = t * 0.02;
    camera.position.x += (mx * 0.5 - camera.position.x) * 0.04;
    camera.position.y += (-my * 0.5 - camera.position.y) * 0.04;
    renderer.render(scene, camera);
  }
  animate();

  window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
  });
})();

/* ═══════════════════════════════════════
   CURSOR
═══════════════════════════════════════ */
const co = document.getElementById('cursor-outer');
const ci = document.getElementById('cursor-inner');
let ox=0,oy=0,ix=0,iy=0;
document.addEventListener('mousemove', e => { ix=e.clientX; iy=e.clientY; });
function animCursor() {
  ox += (ix-ox)*.18; oy += (iy-oy)*.18;
  co.style.left=ox+'px'; co.style.top=oy+'px';
  ci.style.left=ix+'px'; ci.style.top=iy+'px';
  requestAnimationFrame(animCursor);
}
animCursor();
document.querySelectorAll('button,a,textarea').forEach(el=>{
  el.addEventListener('mouseenter',()=>document.body.classList.add('cursor-expand','cursor-dot'));
  el.addEventListener('mouseleave',()=>document.body.classList.remove('cursor-expand','cursor-dot'));
});

/* ═══════════════════════════════════════
   PARALLAX DEPTH
═══════════════════════════════════════ */
const dl1 = document.getElementById('dl1');
document.addEventListener('mousemove', e => {
  const x = (e.clientX / window.innerWidth  - 0.5);
  const y = (e.clientY / window.innerHeight - 0.5);
  dl1.style.transform = `rotateX(${y*4}deg) rotateY(${-x*4}deg) translateZ(0)`;
});

/* ═══════════════════════════════════════
   3D CARD TILT
═══════════════════════════════════════ */
function enableTilt(el, depth=14) {
  el.addEventListener('mousemove', e => {
    const r = el.getBoundingClientRect();
    const x = (e.clientX - r.left) / r.width  - 0.5;
    const y = (e.clientY - r.top)  / r.height - 0.5;
    el.style.transform = `perspective(600px) rotateX(${-y*depth}deg) rotateY(${x*depth}deg) translateZ(6px)`;
    el.style.boxShadow = `${-x*20}px ${-y*20}px 60px rgba(0,0,0,.6), 0 20px 60px rgba(0,0,0,.5)`;
    const gloss = el.querySelector('.gloss');
    if(gloss) { gloss.style.background=`radial-gradient(circle at ${(x+.5)*100}% ${(y+.5)*100}%,rgba(255,255,255,.14),transparent 60%)`; }
  });
  el.addEventListener('mouseleave', () => {
    el.style.transform=''; el.style.boxShadow='';
  });
}

/* ═══════════════════════════════════════
   APP STATE & API
═══════════════════════════════════════ */
const API = 'http://localhost:8000';
const MOODS = [
  {s:1,e:"😔",l:"Sad",     c:"#6EA8C4",r:"110,168,196"},
  {s:2,e:"😟",l:"Anxious", c:"#9B94C8",r:"155,148,200"},
  {s:3,e:"😐",l:"Neutral", c:"#8AADA7",r:"138,173,167"},
  {s:4,e:"🙂",l:"Good",    c:"#6DBAAA",r:"109,186,170"},
  {s:5,e:"😄",l:"Joyful",  c:"#E8AA3C",r:"232,170,60"},
];
const PROMPTS = [
  "What's weighing on your mind today?",
  "Describe one small win from today.",
  "What emotion has been most present today?",
  "What are you grateful for right now?",
  "What would make tomorrow better?",
  "How is your body feeling today?",
  "What drained your energy, and what restored it?",
  "Describe a moment when you felt truly present.",
  "What's something you're looking forward to?",
  "What would you tell your past self right now?",
];
const S = { view:'journal',mood:null,entry:'',submitted:false,loading:false,aiText:'',aiEmotions:[],pi:0,history:[],stats:null,insight:'',iLoading:false };

const getToken = () => localStorage.getItem('solace_token');
const setToken = (t) => localStorage.setItem('solace_token', t);
const clearToken = () => localStorage.removeItem('solace_token');

const getUsernameFromToken = () => {
  const t = getToken();
  if(!t) return null;
  try {
    const payload = JSON.parse(atob(t.split('.')[1]));
    return payload.sub;
  } catch(e) { return null; }
};

function logout() {
  clearToken();
  renderAuth(true);
  toast('Logged out securely', '👋');
}

const post = async(p,b)=>{
  const h = {'Content-Type':'application/json'};
  const t = getToken();
  if(t) h['Authorization'] = `Bearer ${t}`;
  const r=await fetch(API+p,{method:'POST',headers:h,body:JSON.stringify(b)});
  if(r.status===401) { clearToken(); renderAuth(); throw new Error('Auth'); }
  if(!r.ok) throw new Error();
  return r.json();
};

const get = async(p) => {
  const h = {};
  const t = getToken();
  if(t) h['Authorization'] = `Bearer ${t}`;
  const r=await fetch(API+p, {headers: h});
  if(r.status===401) { clearToken(); renderAuth(); throw new Error('Auth'); }
  if(!r.ok) throw new Error();
  return r.json();
};


function toast(m,i='🌿',d=3200){
  document.getElementById('tm').textContent=m;
  document.getElementById('ti').textContent=i;
  const el=document.getElementById('toast');
  el.classList.add('show');
  setTimeout(()=>el.classList.remove('show'),d);
}
const mc  = s=>MOODS.find(m=>m.s===s)?.c||'#6DBAAA';
const mr  = s=>MOODS.find(m=>m.s===s)?.r||'109,186,170';
const fd  = iso=>new Date(iso).toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric'});
const ft  = iso=>new Date(iso).toLocaleTimeString('en-US',{hour:'2-digit',minute:'2-digit'});

function typewriter(el,text,speed=15){
  let i=0;el.innerHTML='';
  const cur=Object.assign(document.createElement('span'),{className:'cursor',textContent:'|'});
  el.appendChild(cur);
  const iv=setInterval(()=>{ if(i<text.length){el.insertBefore(document.createTextNode(text[i++]),cur);}else{clearInterval(iv);cur.style.display='none';}},speed);
}
function addRipple(btn,e){
  const d=document.createElement('div');d.className='ripple-dot';
  const r=btn.getBoundingClientRect();
  d.style.left=(e.clientX-r.left-5)+'px';d.style.top=(e.clientY-r.top-5)+'px';
  btn.appendChild(d);setTimeout(()=>d.remove(),800);
}

/* ═══════════════════════════════════════
   ROUTER
═══════════════════════════════════════ */
function gv(v){
  S.view=v;
  document.querySelectorAll('.tab').forEach(b=>b.classList.toggle('active',b.dataset.view===v));
  render();
  if(v==='history')  loadHistory();
  if(v==='insights') loadStats();
}


function renderAuth(isLogin=true) {
  document.querySelector('.header').style.display = 'none';
  document.querySelector('.nav').style.display = 'none';
  const up = document.getElementById('userProfile');
  if(up) up.style.display = 'none';
  const el=document.getElementById('app');
  el.className='main anim-up';
  
  el.innerHTML = `
    <div style="max-width:360px;margin:100px auto" class="stagger">
      <div class="logo-gem" style="margin:0 auto 20px;width:60px;height:60px;font-size:28px">🌿</div>
      <h2 style="text-align:center;font-family:var(--f-serif);font-size:32px;font-weight:300;margin-bottom:10px">${isLogin ? 'Welcome back' : 'Join Solace'}</h2>
      <p style="text-align:center;color:var(--text3);font-size:14px;margin-bottom:30px">${isLogin ? 'Sign in to your private journal' : 'Create your secure, private space'}</p>
      
      <div class="journal-box" style="padding:24px">
        <div style="margin-bottom:16px">
          <label style="font-size:11px;color:var(--text3);text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;display:block">Username</label>
          <input type="text" id="authU" style="width:100%;background:rgba(0,0,0,.2);border:1px solid var(--border);border-radius:12px;padding:12px;font-size:15px;color:var(--text)" />
        </div>
        <div style="margin-bottom:24px">
          <label style="font-size:11px;color:var(--text3);text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;display:block">Password</label>
          <input type="password" id="authP" style="width:100%;background:rgba(0,0,0,.2);border:1px solid var(--border);border-radius:12px;padding:12px;font-size:15px;color:var(--text)" />
        </div>
        <button class="sub-btn ready" id="authBtn" onclick="doAuth(${isLogin})">
          <div class="sbi"><span>${isLogin ? 'Sign In' : 'Create Account'}</span>✦</div>
        </button>
      </div>
      
      <div style="text-align:center;margin-top:20px;font-size:13px;color:var(--text4)">
        ${isLogin ? "Don't have an account? <a href='#' onclick='renderAuth(false)' style='color:var(--sage)'>Sign up</a>" : "Already have an account? <a href='#' onclick='renderAuth(true)' style='color:var(--sage)'>Sign in</a>"}
      </div>
    </div>
  `;
}

async function doAuth(isLogin) {
  const u = document.getElementById('authU').value.trim();
  const p = document.getElementById('authP').value.trim();
  if(!u || !p) return toast('Please fill all fields', '⚠️');
  
  const btn = document.getElementById('authBtn');
  btn.className = 'sub-btn loading';
  btn.innerHTML = `<div class="sbi"><div class="spinner"></div> ${isLogin ? 'Signing in...' : 'Creating account...'}</div>`;
  
  try {
    if(isLogin) {
      const fd = new URLSearchParams();
      fd.append('username', u); fd.append('password', p);
      const r = await fetch(API+'/login', {method:'POST', body:fd});
      if(!r.ok) throw new Error();
      const d = await r.json();
      setToken(d.access_token);
      toast('Welcome back', '🌿');
      startApp();
    } else {
      await post('/register', {username: u, password: p});
      toast('Account created! Please sign in.', '✨');
      renderAuth(true);
    }
  } catch(e) {
    btn.className = 'sub-btn ready';
    btn.innerHTML = `<div class="sbi"><span>${isLogin ? 'Sign In' : 'Create Account'}</span>✦</div>`;
    toast(isLogin ? 'Invalid credentials' : 'Username taken', '⚠️');
  }
}

function startApp() {
  document.querySelector('.header').style.display = 'flex';
  document.querySelector('.nav').style.display = 'flex';
  const u = getUsernameFromToken();
  const up = document.getElementById('userProfile');
  if(u && up) {
    up.style.display = 'flex';
    document.getElementById('userName').textContent = u;
  }
  gv('journal');
}


function render(){
  const el=document.getElementById('app');
  el.className='main anim-up';
  el.innerHTML='';
  void el.offsetWidth;
  if(S.view==='journal')  rJournal(el);
  if(S.view==='insights') rInsights(el);
  if(S.view==='history')  rHistory(el);
  // re-attach cursor listeners to new elements
  el.querySelectorAll('button,a,textarea').forEach(e=>{
    e.addEventListener('mouseenter',()=>document.body.classList.add('cursor-expand','cursor-dot'));
    e.addEventListener('mouseleave',()=>document.body.classList.remove('cursor-expand','cursor-dot'));
  });
}

/* ═══════════════════════════════════════
   JOURNAL VIEW
═══════════════════════════════════════ */
function rJournal(el){
  if(!S.submitted){
    el.innerHTML=`
    <div class="stagger">
      <div class="prompt-card tilt-card" id="pCard">
        <div class="gloss"></div>
        <div class="prompt-eye"><div class="pdot"></div>Today's prompt</div>
        <p class="prompt-q" id="pq">"${PROMPTS[S.pi]}"</p>
        <button class="new-prompt-btn" onclick="nextPrompt()">↻ &nbsp;New prompt</button>
      </div>

      <div>
        <div class="glass-label">How are you feeling right now?</div>
        <div class="mood-grid">
          ${MOODS.map(m=>`
            <button class="mood-btn${S.mood===m.s?' sel':''}" id="mb${m.s}"
              style="--mc:${m.c};--mr:${m.r}"
              onclick="pickMood(${m.s},event)">
              <span class="mood-emoji">${m.e}</span>
              <span class="mood-lbl">${m.l}</span>
            </button>`).join('')}
        </div>
      </div>

      <div class="journal-box" id="jbox">
        <div class="tb">
          <button class="tb-btn"><b>B</b></button>
          <button class="tb-btn"><i>I</i></button>
          <button class="tb-btn">≡</button>
          <div class="tb-sep"></div>
          <button class="tb-btn" onclick="clearJ()">✕</button>
          <div class="tb-r">🔒 encrypted &amp; private</div>
        </div>
        <div class="jbody">
          <textarea class="jta" id="jta" rows="8"
            placeholder="Start writing freely… this is your safe, private space."
            oninput="onType(this)">${S.entry}</textarea>
        </div>
        <div class="jfooter">
          <div class="cw">
            <div class="ctrack"><div class="cfill" id="cf" style="width:${Math.min((S.entry.length/500)*100,100)}%"></div></div>
            <span class="cnum" id="cn">${S.entry.length} chars</span>
          </div>
          <span class="hint">⌘+Enter to save</span>
        </div>
      </div>

      <button class="sub-btn ${S.entry.trim()&&S.mood?'ready':'off'}" id="sb" onclick="doSub()">
        <div class="sbi"><span>Save entry &amp; get reflection</span><span>✦</span></div>
      </button>
    </div>`;

    // Tilt effects
    enableTilt(document.getElementById('pCard'), 10);
    document.getElementById('jta')?.addEventListener('keydown',e=>{if((e.metaKey||e.ctrlKey)&&e.key==='Enter')doSub();});
    document.getElementById('jta')?.focus();

  } else {
    const m=MOODS.find(x=>x.s===S.mood);
    el.innerHTML=`
    <div class="stagger">
      <div class="succ-bar">
        <div class="succ-bubble">${m?.e}</div>
        <div>
          <div class="succ-title">Entry saved</div>
          <div class="succ-sub">Feeling ${m?.l?.toLowerCase()} · ${new Date().toLocaleTimeString('en-US',{hour:'2-digit',minute:'2-digit'})}</div>
        </div>
        <div class="succ-check">✓</div>
      </div>
      ${S.aiEmotions.length?`
        <div class="emo-row">
          <span class="emo-l">Detected emotions —</span>
          ${S.aiEmotions.map((e,i)=>`<span class="emo-chip" style="animation-delay:${i*.1}s">${e}</span>`).join('')}
        </div>`:''}
      <div class="entry-q">"${S.entry.length>200?S.entry.slice(0,200)+'…':S.entry}"</div>
      ${S.aiText?`
        <div class="ai-card">
          <div class="ai-head"><div class="ai-orb">✦</div><span class="ai-tag">AI Reflection</span></div>
          <div class="ai-body"><p class="ai-text" id="aitxt"></p></div>
        </div>`:''}
      <button class="new-btn" onclick="newEntry()"><span>+</span> Write another entry</button>
    </div>`;

    // Tilt on ai card
    const ac=el.querySelector('.ai-card');
    if(ac) enableTilt(ac, 6);
    if(S.aiText) setTimeout(()=>typewriter(document.getElementById('aitxt'),S.aiText),350);
  }
}

function nextPrompt(){
  S.pi=(S.pi+1)%PROMPTS.length;
  const el=document.getElementById('pq');
  if(el){el.style.opacity='0';setTimeout(()=>{el.textContent=`"${PROMPTS[S.pi]}"`;el.style.opacity='1';el.style.transition='opacity .3s';},160);}
}

function pickMood(s,e){
  S.mood=s;
  MOODS.forEach(m=>{const b=document.getElementById('mb'+m.s);if(b)b.classList.toggle('sel',m.s===s);});
  if(e) addRipple(document.getElementById('mb'+s),e);
  syncSub();
}

function onType(el){
  S.entry=el.value;
  const p=Math.min((el.value.length/500)*100,100);
  const f=document.getElementById('cf'),n=document.getElementById('cn');
  if(f)f.style.width=p+'%';
  if(n)n.textContent=el.value.length+' chars';
  syncSub();
}

function clearJ(){S.entry='';const ta=document.getElementById('jta');if(ta){ta.value='';onType(ta);}}

function syncSub(){
  const b=document.getElementById('sb');
  if(b)b.className=`sub-btn ${S.entry.trim()&&S.mood?'ready':'off'}`;
}

async function doSub(){
  if(!S.entry.trim()||!S.mood||S.loading)return;
  S.loading=true;
  const btn=document.getElementById('sb');
  if(btn){btn.className='sub-btn loading';btn.innerHTML=`<div class="sbi"><div class="spinner"></div> Reflecting…</div>`;}
  const m=MOODS.find(x=>x.s===S.mood);
  try{
    const d=await post('/entries',{content:S.entry,mood_score:S.mood,mood_label:m.l});
    S.aiText=d.ai_response||'';S.aiEmotions=d.emotions||[];S.submitted=true;
    toast('Entry saved','🌿');
  }catch{
    toast('Backend unreachable','⚠️');
    if(btn){btn.className='sub-btn ready';btn.innerHTML=`<div class="sbi"><span>Save entry &amp; get reflection</span><span>✦</span></div>`;}
  }
  S.loading=false;if(S.submitted)render();
}

function newEntry(){
  Object.assign(S,{entry:'',mood:null,submitted:false,aiText:'',aiEmotions:[],pi:(S.pi+1)%PROMPTS.length});
  render();
}

/* ═══════════════════════════════════════
   INSIGHTS
═══════════════════════════════════════ */
async function loadStats(){
  try{S.stats=await get('/insights/stats');rInsights(document.getElementById('app'));}catch{}
}

function rInsights(el){
  const s=S.stats;
  const avg=s?.avg_mood||'—',total=s?.total_entries||'—',topE=s?.top_emotions||[];
  const wd=s?.daily_moods?.length
    ?s.daily_moods.slice(0,7).reverse().map(d=>({day:new Date(d.day+'T00:00:00').toLocaleDateString('en',{weekday:'short'}).slice(0,1),score:Math.round(d.avg_mood)}))
    :[{day:'M',score:2},{day:'T',score:4},{day:'W',score:3},{day:'T',score:5},{day:'F',score:4},{day:'S',score:3},{day:'S',score:4}];

  const cp=['var(--lav)','var(--sky)','var(--sage)','var(--amber)','var(--rose)','var(--teal)'];
  const sz=[21,19,18,16,15,13,12,11];

  const cloud=topE.length
    ?topE.map((e,i)=>`<span class="ctag" style="font-size:${sz[i]||11}px;color:${cp[i%cp.length]};opacity:${.5+(sz[i]||11-10)/12}">${e.emotion}</span>`).join('')
    :[['work',21],['sleep',17],['family',19],['grateful',18],['tired',15],['hope',16],['anxious',14]].map(([w,sz],i)=>
      `<span class="ctag" style="font-size:${sz}px;color:${cp[i%cp.length]};opacity:${.5+(sz-11)/10}">${w}</span>`).join('');

  el.innerHTML=`
  <div class="stagger">
    <div class="pg-hero">
      <h1 class="pg-title">Your patterns</h1>
      <p class="pg-sub">Mood &amp; emotional analytics</p>
    </div>

    <div class="stats-row">
      <div class="stat-card tilt-card" style="--sa:var(--sage);--sar:109,186,170"><div class="gloss"></div><div class="stat-bot"></div><div class="stat-icon">✦</div><div class="stat-val">${avg}/5</div><div class="stat-lbl">Avg Mood</div></div>
      <div class="stat-card tilt-card" style="--sa:var(--sky);--sar:110,168,196"><div class="gloss"></div><div class="stat-bot"></div><div class="stat-icon">📝</div><div class="stat-val">${total}</div><div class="stat-lbl">Entries</div></div>
      <div class="stat-card tilt-card" style="--sa:var(--amber);--sar:232,170,60"><div class="gloss"></div><div class="stat-bot"></div><div class="stat-icon">🔥</div><div class="stat-val">—</div><div class="stat-lbl">Streak</div></div>
    </div>

    <div class="glass">
      <div class="aurora"></div>
      <div class="glass-p">
        <div class="glass-label">Weekly mood</div>
        <div class="chart-area">
          ${wd.map((d,i)=>`
            <div class="bcol">
              <div class="bhold">
                <div class="bar" style="height:${(d.score/5)*86}px;background:linear-gradient(180deg,${mc(d.score)},${mc(d.score)}50);box-shadow:0 0 16px ${mc(d.score)}44;animation-delay:${i*.08}s"></div>
              </div>
              <span class="bday">${d.day}</span>
            </div>`).join('')}
        </div>
      </div>
    </div>

    <div class="glass">
      <div class="aurora"></div>
      <div class="glass-p">
        <div class="glass-label">Common themes &amp; emotions</div>
        <div class="cloud-wrap">${cloud}</div>
      </div>
    </div>

    <div class="ins-banner tilt-card" id="insCard">
      <div class="gloss"></div>
      <div class="ins-head"><div class="ins-orb">✦</div><div class="ins-eye">Weekly AI Insight</div></div>
      <p class="ins-txt" id="insTxt">${S.insight||'Click below to generate a personalized insight based on your recent entries.'}</p>
      <button class="ins-btn" onclick="genIns()" id="insBtn">
        ${S.iLoading?`<div class="spinner"></div> Generating…`:S.insight?'↻ Refresh insight':'✦ Generate insight'}
      </button>
    </div>
  </div>`;

  el.querySelectorAll('.tilt-card').forEach(c=>enableTilt(c,8));
}

async function genIns(){
  S.iLoading=true;
  const b=document.getElementById('insBtn');if(b)b.innerHTML=`<div class="spinner"></div> Generating…`;
  try{const d=await post('/insights/weekly',{});S.insight=d.insight;toast('Insight ready','✦');}
  catch{S.insight='Keep journaling consistently to unlock personalized weekly insights.';}
  S.iLoading=false;rInsights(document.getElementById('app'));
}

/* ═══════════════════════════════════════
   HISTORY
═══════════════════════════════════════ */
async function loadHistory(){
  try{
    S.history=await get('/entries?limit=30');
    const b=document.getElementById('hct');if(b)b.textContent=S.history.length;
    rHistory(document.getElementById('app'));
  }catch{}
}

function rHistory(el){
  const E=S.history;
  const b=document.getElementById('hct');if(b&&E.length)b.textContent=E.length;
  el.innerHTML=`
  <div class="stagger">
    <div class="pg-hero">
      <h1 class="pg-title">Past entries</h1>
      <p class="pg-sub">${E.length?E.length+' entries · your journey documented':'Your journey, documented'}</p>
    </div>
    <div class="hlist">
      ${E.length===0?`
        <div class="h-empty">
          <div class="h-ei">📔</div>
          <div class="h-et">No entries yet</div>
          <div class="h-es">Start writing to see your history here</div>
        </div>`
        :E.map((e,i)=>`
        <div class="hcard anim-scale" style="--hmc:${mc(e.mood_score)};animation-delay:${i*.06}s">
          <div class="hinn">
            <div class="htop">
              <div class="hleft">
                <div class="hbub">${e.mood_emoji||'📝'}</div>
                <div>
                  <div class="hdate">${fd(e.created_at)}</div>
                  <div class="htime">${ft(e.created_at)} · ${e.mood_label}</div>
                </div>
              </div>
              <div class="hchips">${(e.emotions||[]).slice(0,2).map(em=>`<span class="hchip">${em}</span>`).join('')}</div>
            </div>
            <p class="hexcerpt">"${e.content.length>160?e.content.slice(0,160)+'…':e.content}"</p>
          </div>
        </div>`).join('')}
    </div>
    <div style="text-align:center;margin-top:30px;font-size:11px;color:var(--text4)">✦ &nbsp; All entries are encrypted and private &nbsp; ✦</div>
  </div>`;
}

/* ═══════════════════════════════════════
   INIT
═══════════════════════════════════════ */

document.getElementById('hdrDate').textContent=new Date().toLocaleDateString('en-US',{weekday:'long',month:'long',day:'numeric'});
if(getToken()) {
  startApp();
} else {
  renderAuth();
}
