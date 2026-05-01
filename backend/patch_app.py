import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add imports
imports_addition = """from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
import jwt
from datetime import datetime, date, timedelta"""
content = re.sub(r'from datetime import datetime, date', imports_addition, content)

# 2. Add Auth Setup
auth_setup = """# ─────────────────────────────────────────────
# Auth Setup
# ─────────────────────────────────────────────
SECRET_KEY = "super-secret-key-solace"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    return username

"""

content = content.replace('# ─────────────────────────────────────────────\n# Database Setup', auth_setup + '# ─────────────────────────────────────────────\n# Database Setup')

# 3. Add users table to init_db
users_table = """
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL
        );
"""
content = content.replace('CREATE TABLE IF NOT EXISTS entries (', users_table + '        CREATE TABLE IF NOT EXISTS entries (')

# 4. Add auth models
auth_models = """class UserCreate(BaseModel):
    username: str
    password: str

"""
content = content.replace('class JournalEntry(BaseModel):', auth_models + 'class JournalEntry(BaseModel):')

# 5. Add auth routes
auth_routes = """@app.post("/register")
def register(user: UserCreate):
    conn = get_db()
    existing = conn.execute("SELECT * FROM users WHERE username = ?", (user.username,)).fetchone()
    if existing:
        conn.close()
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed_pw = get_password_hash(user.password)
    conn.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (user.username, hashed_pw))
    conn.commit()
    conn.close()
    return {"message": "User created successfully"}

@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (form_data.username,)).fetchone()
    conn.close()
    if not user or not verify_password(form_data.password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    access_token = create_access_token(data={"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}

"""
content = content.replace('@app.post("/entries"', auth_routes + '@app.post("/entries"')

# 6. Protect routes by changing parameters and using current_user
content = re.sub(r'def create_entry\(entry: JournalEntry\):', r'def create_entry(entry: JournalEntry, current_user: str = Depends(get_current_user)):', content)
content = re.sub(r'entry.user_id', r'current_user', content)

content = re.sub(r'def get_entries\(user_id: str = "default", limit: int = 20\):', r'def get_entries(limit: int = 20, current_user: str = Depends(get_current_user)):', content)
content = re.sub(r'\(user_id, limit\)', r'(current_user, limit)', content)

content = re.sub(r'def get_entry\(entry_id: int, user_id: str = "default"\):', r'def get_entry(entry_id: int, current_user: str = Depends(get_current_user)):', content)
content = re.sub(r'\(entry_id, user_id\)', r'(entry_id, current_user)', content)

content = re.sub(r'def delete_entry\(entry_id: int, user_id: str = "default"\):', r'def delete_entry(entry_id: int, current_user: str = Depends(get_current_user)):', content)

content = re.sub(r'def get_stats\(user_id: str = "default"\):', r'def get_stats(current_user: str = Depends(get_current_user)):', content)
content = re.sub(r'\(user_id,\)', r'(current_user,)', content)

content = re.sub(r'def generate_weekly_insight\(req: WeeklyInsightRequest\):', r'def generate_weekly_insight(req: WeeklyInsightRequest, current_user: str = Depends(get_current_user)):', content)
content = re.sub(r'req\.user_id', r'current_user', content)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Backend patched successfully.")
