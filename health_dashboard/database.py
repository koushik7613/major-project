"""
Database Module for Local Personal Health Dashboard
SQLite database schema, connection pooling, and data helpers.
"""
import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config

def get_db_connection():
    """Returns a sqlite3 connection with Row factory enabled and WAL mode for concurrency."""
    conn = sqlite3.connect(str(Config.DATABASE_PATH), timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn

def init_db():
    """Initializes tables and seeds initial medicine knowledge and demo user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT NOT NULL,
        age INTEGER DEFAULT 24,
        gender TEXT DEFAULT 'Other',
        weight_kg REAL DEFAULT 70.0,
        height_cm REAL DEFAULT 172.0,
        daily_step_goal INTEGER DEFAULT 10000,
        sleep_goal_hours REAL DEFAULT 8.0,
        active_min_goal INTEGER DEFAULT 45,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # 2. Uploaded files table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS uploaded_files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        filename TEXT NOT NULL,
        original_name TEXT NOT NULL,
        file_path TEXT NOT NULL,
        row_count INTEGER DEFAULT 0,
        upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'processed',
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    )
    """)
    
    # 3. Health records table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS health_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        file_id INTEGER,
        record_date TEXT NOT NULL,
        steps INTEGER DEFAULT 0,
        resting_heart_rate REAL DEFAULT 0,
        avg_heart_rate REAL DEFAULT 0,
        max_heart_rate REAL DEFAULT 0,
        sleep_hours REAL DEFAULT 0,
        deep_sleep_hours REAL DEFAULT 0,
        active_minutes REAL DEFAULT 0,
        calories_burned REAL DEFAULT 0,
        distance_km REAL DEFAULT 0,
        spo2 REAL DEFAULT 98.0,
        stress_level REAL DEFAULT 30.0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, record_date) ON CONFLICT REPLACE,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
        FOREIGN KEY (file_id) REFERENCES uploaded_files (id) ON DELETE SET NULL
    )
    """)
    
    # Index for fast date lookups
    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_health_user_date 
    ON health_records(user_id, record_date)
    """)
    
    # 4. Anomalies table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS anomalies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        record_date TEXT NOT NULL,
        metric_name TEXT NOT NULL,
        actual_value REAL NOT NULL,
        baseline_value REAL NOT NULL,
        deviation_pct REAL NOT NULL,
        severity TEXT DEFAULT 'Moderate',
        explanation TEXT NOT NULL,
        detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    )
    """)
    
    # 5. Chat history table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chat_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        context_tag TEXT DEFAULT 'general',
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    )
    """)
    
    # 6. Medicine knowledge base table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS medicine_knowledge (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        medicine_name TEXT UNIQUE NOT NULL,
        generic_name TEXT NOT NULL,
        category TEXT NOT NULL,
        common_uses TEXT NOT NULL,
        precautions TEXT NOT NULL,
        side_effects TEXT NOT NULL,
        interactions TEXT NOT NULL,
        dosage_warning TEXT NOT NULL
    )
    """)
    
    conn.commit()
    
    # Seed default user if not exists
    cursor.execute("SELECT id FROM users WHERE username = 'demo_user'")
    if not cursor.fetchone():
        demo_pwd_hash = generate_password_hash("demo123")
        cursor.execute("""
        INSERT INTO users (username, email, password_hash, full_name, age, gender, weight_kg, height_cm)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, ('demo_user', 'demo@healthboard.local', demo_pwd_hash, 'Student Researcher', 22, 'Male', 68.5, 175.0))
        conn.commit()

    # Seed medicine database
    seed_medicine_knowledge(cursor)
    conn.commit()
    conn.close()

def seed_medicine_knowledge(cursor):
    """Seeds comprehensive, clinically accurate general medicine information."""
    cursor.execute("SELECT COUNT(*) as count FROM medicine_knowledge")
    count = cursor.fetchone()['count']
    if count > 0:
        return
        
    meds = [
        ("Paracetamol (Acetaminophen)", "Acetaminophen", "Analgesic / Antipyretic",
         "Relief of mild to moderate pain (headaches, muscular aches, toothaches) and fever reduction.",
         "Do not exceed 4,000 mg in 24 hours. Avoid alcohol consumption to protect liver. Consult doctor if fever persists > 3 days.",
         "Rare at therapeutic doses; nausea, allergic rash; high doses cause severe hepatic damage.",
         "May interact with blood thinners (Warfarin) on chronic high doses, alcohol, and other acetaminophen-containing medications.",
         "Strictly general information. Always follow physician's prescription or package directions."),

        ("Ibuprofen", "Ibuprofen", "NSAID (Nonsteroidal Anti-inflammatory)",
         "Relief of inflammatory pain, arthritis, dental pain, dysmenorrhea, fever, and sports injuries.",
         "Take with or after food to minimize gastrointestinal upset. Caution in individuals with history of peptic ulcers, kidney disease, or hypertension.",
         "Stomach ache, heartburn, nausea, dizziness, fluid retention.",
         "Interacts with Aspirin, ACE inhibitors, diuretics, anticoagulants, SSRIs.",
         "Not recommended during the third trimester of pregnancy without direct medical authorization."),

        ("Amoxicillin", "Amoxicillin", "Penicillin Antibiotic",
         "Bacterial infections including ENT (ear, nose, throat), respiratory tract, skin, and urinary tract infections.",
         "Complete the full prescribed course even if symptoms subside to avoid antibiotic resistance. Ineffective against viral illnesses like the common cold or flu.",
         "Diarrhea, mild rash, nausea, vomiting, fungal superinfections (thrush).",
         "Oral contraceptives (reduced efficacy), Allopurinol, Methotrexate.",
         "Requires a valid doctor's prescription. Seek immediate emergency care if experiencing anaphylactic symptoms (wheezing, hives, lip swelling)."),

        ("Cetirizine", "Cetirizine Hydrochloride", "Antihistamine (Second Generation)",
         "Relief of allergy symptoms such as hay fever, allergic rhinitis, runny nose, sneezing, itchy eyes, and chronic urticaria (hives).",
         "May cause mild drowsiness in sensitive individuals; avoid alcohol or operating heavy machinery until effect is known.",
         "Drowsiness, dry mouth, headache, fatigue.",
         "CNS depressants, sedatives, alcohol.",
         "Over-the-counter allergy relief. Consult doctor if symptoms persist beyond 7 days."),

        ("Metformin", "Metformin Hydrochloride", "Biguanide Antidiabetic",
         "First-line management of Type 2 Diabetes Mellitus to improve glycemic control by reducing hepatic glucose output.",
         "Take with meals to reduce stomach upset. Periodic renal function tests (eGFR) and Vitamin B12 monitoring recommended.",
         "Gastrointestinal discomfort (diarrhea, cramping, nausea), metallic taste; rare risk of lactic acidosis.",
         "Iodinated contrast media (discontinue prior to scan), alcohol, Cimetidine.",
         "Prescription only. Always adjust under endocrinologist guidance; do not change doses independently."),

        ("Amlodipine", "Amlodipine Besylate", "Calcium Channel Blocker (Antihypertensive)",
         "Management of hypertension (high blood pressure) and coronary artery disease (chronic stable angina).",
         "Do not stop abruptly. Monitor blood pressure routinely. Caution with grapefruit and grapefruit juice.",
         "Peripheral edema (swelling of ankles/feet), flushing, dizziness, fatigue, palpitations.",
         "Simvastatin (dose cap applies), CYP3A4 inhibitors, other blood pressure agents.",
         "Cardiovascular prescription medication. Take at the same time each day."),

        ("Atorvastatin", "Atorvastatin Calcium", "HMG-CoA Reductase Inhibitor (Statin)",
         "Lowering LDL cholesterol and triglycerides, raising HDL, and reducing cardiovascular event risks.",
         "Take once daily (evening preferred). Report unexplained muscle soreness, tenderness, or weakness immediately.",
         "Muscle ache (myalgia), digestive upset, elevated liver transaminases, headache.",
         "Grapefruit juice in large amounts, Clarithromycin, Gemfibrozil, Cyclosporine.",
         "Prescription only. Requires baseline and periodic lipid panels and liver enzyme checks."),

        ("Omeprazole", "Omeprazole", "Proton Pump Inhibitor (PPI)",
         "Gastroesophageal reflux disease (GERD), peptic ulcers, heartburn, and Zollinger-Ellison syndrome.",
         "Best taken 30-60 minutes before breakfast. Long-term use may require monitoring for magnesium and B12 levels.",
         "Headache, abdominal pain, constipation, flatulence, nausea.",
         "Clopidogrel (Plavix), Diazepam, Iron supplements, Digoxin.",
         "Short-term relief of acid symptoms. Consult physician for chronic or worsening symptoms."),

        ("Azithromycin", "Azithromycin", "Macrolide Antibiotic",
         "Atypical bacterial respiratory infections, bronchitis, pneumonia, sinusitis, and skin infections.",
         "Strict adherence to prescribed regimen. Do not use for viral infections. Notify doctor of cardiac history.",
         "Loose stools, nausea, abdominal pain, temporary taste disturbance, rare QT interval prolongation.",
         "Antacids containing magnesium or aluminum (separate dosing by 2 hours), Warfarin, Digoxin.",
         "Prescription-only antibiotic. Complete full 3-day or 5-day cycle as instructed by your clinician."),

        ("Pantoprazole", "Pantoprazole Sodium", "Proton Pump Inhibitor (PPI)",
         "Acid reflux, erosive esophagitis, stomach ulcer prevention during long-term NSAID therapy.",
         "Take before morning meal. Swallow tablet whole; do not crush or chew.",
         "Mild headache, diarrhea, dizziness, arthralgia.",
         "Methotrexate, HIV protease inhibitors, Ketoconazole.",
         "Prescription and OTC. Not intended for immediate relief of sudden heartburn.")
    ]
    
    cursor.executemany("""
    INSERT INTO medicine_knowledge 
    (medicine_name, generic_name, category, common_uses, precautions, side_effects, interactions, dosage_warning)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, meds)

# User Helpers
def create_user(username, email, password, full_name, age=24, gender='Other', weight=70.0, height=172.0):
    conn = get_db_connection()
    pwd_hash = generate_password_hash(password)
    try:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO users (username, email, password_hash, full_name, age, gender, weight_kg, height_cm)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (username.strip().lower(), email.strip().lower(), pwd_hash, full_name.strip(), age, gender, weight, height))
        conn.commit()
        user_id = cursor.lastrowid
        return user_id, None
    except sqlite3.IntegrityError:
        existing = conn.execute("SELECT id FROM users WHERE username = ? OR email = ?", 
                                (username.strip().lower(), email.strip().lower())).fetchone()
        if existing:
            return existing['id'], None
        return None, "Registration failed: Duplicate user entry."
    finally:
        conn.close()

def verify_user(username, password):
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ? OR email = ?", 
                        (username.strip().lower(), username.strip().lower())).fetchone()
    conn.close()
    if user and check_password_hash(user['password_hash'], password):
        return user
    return None

def get_user_by_id(user_id):
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return user

def update_user_profile(user_id, full_name, age, gender, weight, height, step_goal, sleep_goal, active_goal):
    conn = get_db_connection()
    conn.execute("""
    UPDATE users SET 
        full_name = ?, age = ?, gender = ?, weight_kg = ?, height_cm = ?,
        daily_step_goal = ?, sleep_goal_hours = ?, active_min_goal = ?
    WHERE id = ?
    """, (full_name, age, gender, weight, height, step_goal, sleep_goal, active_goal, user_id))
    conn.commit()
    conn.close()

def search_medicine(query):
    """Searches medicine database prioritizing medicine and generic names first."""
    conn = get_db_connection()
    term = f"%{query.strip()}%"
    rows = conn.execute("""
    SELECT * FROM medicine_knowledge 
    WHERE medicine_name LIKE ? 
       OR generic_name LIKE ? 
    ORDER BY 
       CASE 
         WHEN medicine_name LIKE ? THEN 1
         WHEN generic_name LIKE ? THEN 2
         ELSE 3
       END
    LIMIT 6
    """, (term, term, term, term)).fetchall()
    
    if not rows:
        rows = conn.execute("""
        SELECT * FROM medicine_knowledge 
        WHERE category LIKE ? 
           OR common_uses LIKE ?
        LIMIT 6
        """, (term, term)).fetchall()
        
    conn.close()
    return [dict(r) for r in rows]

def clear_user_data(user_id):
    """Deletes all health records, anomalies, and chat history for a user."""
    conn = get_db_connection()
    conn.execute("DELETE FROM health_records WHERE user_id = ?", (user_id,))
    conn.execute("DELETE FROM anomalies WHERE user_id = ?", (user_id,))
    conn.execute("DELETE FROM uploaded_files WHERE user_id = ?", (user_id,))
    conn.execute("DELETE FROM chat_history WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
