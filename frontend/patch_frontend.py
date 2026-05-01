import re

with open('js/app.js', 'r', encoding='utf-8') as f:
    js_content = f.read()

# 1. Update API requests to include JWT token
auth_helpers = """const getToken = () => localStorage.getItem('solace_token');
const setToken = (t) => localStorage.setItem('solace_token', t);
const clearToken = () => localStorage.removeItem('solace_token');

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
"""

js_content = re.sub(r'const post = async\(p,b\)=>\{.*?\};[\s\n]*const get\s*=\s*async\(p\)\s*=>\{.*?\};', auth_helpers, js_content, flags=re.DOTALL)
js_content = re.sub(r'const post = async\(p,b\)=>\{.*?\};[\s\n]*const get\s*=\s*async\(p\)\s*=>\{.*?\};', auth_helpers, js_content, flags=re.DOTALL)

# Handle cases where post/get was one-liners (as it was in original code)
js_content = re.sub(r"const post\s*=\s*async\(p,b\)=>\{const r=await fetch\(API\+p,\{method:'POST',headers:\{'Content-Type':'application/json'\},body:JSON\.stringify\(b\)\}\);if\(!r\.ok\)throw new Error\(\);return r\.json\(\)\};", "", js_content)
js_content = re.sub(r"const get\s*=\s*async\(p\)\s*=>\{const r=await fetch\(API\+p\);if\(!r\.ok\)throw new Error\(\);return r\.json\(\)\};", "", js_content)
if "const getToken" not in js_content:
    js_content = js_content.replace('const S = {', auth_helpers + '\nconst S = {')

# 2. Add Login/Register UI
login_logic = """
function renderAuth(isLogin=true) {
  document.querySelector('.header').style.display = 'none';
  document.querySelector('.nav').style.display = 'none';
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
  gv('journal');
}

"""

js_content = js_content.replace('function render(){', login_logic + '\nfunction render(){')

# 3. Modify init call
init_logic = """
document.getElementById('hdrDate').textContent=new Date().toLocaleDateString('en-US',{weekday:'long',month:'long',day:'numeric'});
if(getToken()) {
  startApp();
} else {
  renderAuth();
}
"""
js_content = re.sub(r"document\.getElementById\('hdrDate'\).*?render\(\);", init_logic, js_content, flags=re.DOTALL)

with open('js/app.js', 'w', encoding='utf-8') as f:
    f.write(js_content)

print("Frontend patched for Auth successfully.")
