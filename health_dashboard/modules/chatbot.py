"""
Module 6: AI Health and Medicine Information Chatbot
Provides conversational health assistance, medication information, symptom guidance,
and dashboard contextual insights with clinical safety guardrails.
Supports external LLM API (Google Gemini / OpenAI) with an intelligent built-in
clinical knowledge base fallback for guaranteed 100% offline local functionality.
"""
import os
import json
import requests
from datetime import datetime
from config import Config
from database import get_db_connection, search_medicine, get_user_by_id

# System Prompt embodying clinical safety and educational guidelines
SYSTEM_PROMPT = """
You are the AI Health & Medicine Information Assistant for the Local Personal Health Dashboard.
Your role is to provide clear, empathetic, and informative health and wellness explanations to users.

STRICT MEDICAL SAFETY RULES:
1. NEVER provide a definitive medical diagnosis. Always frame observations as possibilities or general educational information.
2. NEVER prescribe medications, calculate specific drug dosages, or tell a patient to start/stop medications.
3. When discussing medicines, outline: Common Uses, General Precautions, Common Side Effects, and Potential Drug Interactions.
4. Always include a disclaimer recommending consultation with a qualified doctor, pharmacist, or healthcare provider for personal clinical decisions.
5. In case of emergency symptoms (e.g., crushing chest pain, sudden numbness, difficulty breathing), immediately advise seeking emergency medical services (e.g., 911 / 112 / nearest hospital).
6. Explain complex medical terminology simply and warmly in plain English.
"""

OFFLINE_KNOWLEDGE_RULES = [
    {
        "keywords": ["chest pain", "heart attack", "can't breathe", "cannot breathe", "shortness of breath", "stroke", "paralysis", "faint"],
        "is_emergency": True,
        "response": (
            "⚠️ **URGENT MEDICAL NOTICE**\n\n"
            "The symptoms you described (such as severe chest pain, shortness of breath, or sudden weakness) can be indicators of an acute medical emergency.\n\n"
            "**Immediate Action Required:**\n"
            "- Please call your local emergency medical services (such as 112, 911, or 999) or visit the nearest emergency room immediately.\n"
            "- Sit or lie down in a safe position and rest while awaiting help.\n"
            "- Do not drive yourself to the emergency hospital.\n\n"
            "*This dashboard cannot diagnose or treat emergency cardiovascular or respiratory conditions.*"
        )
    },
    {
        "keywords": ["headache", "migraine", "head pain", "temple pain"],
        "response": (
            "### 🤕 Understanding Headaches & Head Pain\n\n"
            "Headaches are among the most common physical complaints and can stem from various everyday physiological factors:\n\n"
            "**Common Causes:**\n"
            "- **Tension / Stress:** Tightness in neck and scalp muscles from prolonged screen time or anxiety.\n"
            "- **Dehydration:** Inadequate fluid intake reduces blood volume and oxygen delivery to cranial tissues.\n"
            "- **Sleep Irregularity:** Insufficient sleep or sudden shifts in your sleep cycle.\n"
            "- **Caffeine Withdrawal or Eye Strain:** Staring at monitors without adequate breaks.\n\n"
            "**General Self-Care Tips:**\n"
            "1. Drink 1–2 tall glasses of water.\n"
            "2. Rest in a quiet, dimly lit room with a cool or warm compress on your forehead.\n"
            "3. Practice 20-20-20 screen pauses (every 20 minutes, look at an object 20 feet away for 20 seconds).\n\n"
            "**When to See a Doctor:**\n"
            "Consult a physician if the headache is sudden and explosive ('thunderclap'), accompanied by a stiff neck, fever, confusion, or visual disturbances."
        )
    },
    {
        "keywords": ["sleep", "insomnia", "tired", "fatigue", "deep sleep", "wake up"],
        "response": (
            "### 🌙 Enhancing Sleep Quality & Recovery\n\n"
            "Quality sleep is vital for cellular repair, memory consolidation, and cardiovascular health. Healthy adults typically need **7 to 9 hours** of sleep each night.\n\n"
            "**Science-Backed Sleep Hygiene Tips:**\n"
            "- **Consistent Sleep Schedule:** Go to bed and wake up at the exact same time every day, even on weekends.\n"
            "- **Blue Light Restriction:** Dim overhead lights and avoid phones/laptops at least 60 minutes before bed.\n"
            "- **Cool Sleeping Environment:** Keep the bedroom cool (around 18–20°C / 65–68°F).\n"
            "- **Caffeine Cutoff:** Avoid caffeine at least 6–8 hours prior to bedtime.\n"
            "- **Deep Sleep Boosters:** Moderate daytime cardiovascular exercise (steps) promotes slow-wave deep sleep.\n\n"
            "**Dashboard Correlation:** Check the *Health Analytics* tab to observe how your daily step volume directly correlates with your sleep duration!"
        )
    },
    {
        "keywords": ["steps", "walking", "step goal", "10000 steps", "sedentary"],
        "response": (
            "### 🚶 Daily Steps & Cardiovascular Fitness\n\n"
            "Walking is one of the most effective, low-impact forms of aerobic exercise available.\n\n"
            "**Benefits of Consistent Daily Steps:**\n"
            "- **Cardiovascular Efficiency:** Strengthens cardiac muscle, gradually lowering resting heart rate over time.\n"
            "- **Metabolic Balance:** Improves insulin sensitivity and regulates blood glucose levels.\n"
            "- **Mental Well-being:** Stimulates endorphin release, reducing cortisol (stress hormone) levels.\n\n"
            "**Target Benchmarks:**\n"
            "- **7,000 to 10,000 steps/day:** Associated with significant reductions in all-cause mortality.\n"
            "- If you currently average 4,000 steps, aim to incrementally increase by 1,000 steps every week to avoid joint strain.\n\n"
            "*Remember to wear supportive footwear and stay properly hydrated.*"
        )
    },
    {
        "keywords": ["heart rate", "pulse", "bpm", "resting heart rate", "tachycardia", "bradycardia"],
        "response": (
            "### ❤️ Understanding Heart Rate & Pulse Dynamics\n\n"
            "Your heart rate is a primary vital sign reflecting autonomic nervous system balance and cardiovascular conditioning.\n\n"
            "**Standard Clinical Ranges for Adults:**\n"
            "- **Normal Resting Heart Rate (RHR):** 60 to 100 beats per minute (bpm).\n"
            "- **Athletic / Conditioning Range:** Well-trained endurance athletes often have healthy resting heart rates between 40 to 60 bpm.\n"
            "- **Tachycardia:** Resting heart rate consistently above 100 bpm.\n"
            "- **Bradycardia:** Resting heart rate below 60 bpm.\n\n"
            "**Common Influences on Heart Rate:**\n"
            "- Hydration levels, caffeine intake, emotional stress, ambient temperature, fever, and physical recovery status.\n\n"
            "**Note:** If your resting heart rate feels abnormally irregular, racing while at rest, or is accompanied by dizziness, consult a physician."
        )
    },
    {
        "keywords": ["fever", "temperature", "high temp", "chills"],
        "response": (
            "### 🌡️ Managing Fever & Elevated Temperature\n\n"
            "A fever (body temperature ≥ 38.0°C or 100.4°F) is an adaptive physiological response by your immune system to fight off infection.\n\n"
            "**General Supportive Care:**\n"
            "- **Hydration:** Sip water, oral rehydration solutions, clear broths, or herbal teas.\n"
            "- **Rest:** Limit strenuous exertion to allow the immune system to allocate energy toward recovery.\n"
            "- **Comfort:** Wear lightweight breathable clothing and rest in a well-ventilated room.\n"
            "- **Fever Reducers:** Over-the-counter options like Paracetamol (Acetaminophen) can help manage discomfort when taken strictly according to manufacturer instructions.\n\n"
            "**When to Seek Medical Care:**\n"
            "Seek medical evaluation if fever exceeds 39.4°C (103°F), persists longer than 3 consecutive days, or is accompanied by stiff neck, confusion, or rash."
        )
    }
]

def query_gemini_api(api_key: str, prompt: str, user_context: str = "") -> str:
    """Invokes Google Gemini API if key is available."""
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        full_content = f"{SYSTEM_PROMPT}\n\nUSER CONTEXT:\n{user_context}\n\nUSER QUERY:\n{prompt}"
        
        payload = {
            "contents": [{
                "parts": [{"text": full_content}]
            }],
            "generationConfig": {
                "temperature": 0.4,
                "maxOutputTokens": 800
            }
        }
        
        response = requests.post(url, json=payload, timeout=8)
        if response.status_code == 200:
            data = response.json()
            return data['candidates'][0]['content']['parts'][0]['text']
        else:
            return ""
    except Exception:
        return ""

def query_openai_api(api_key: str, prompt: str, user_context: str = "") -> str:
    """Invokes OpenAI API if key is available."""
    try:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": f"{SYSTEM_PROMPT}\nUser Context:\n{user_context}"},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 700,
            "temperature": 0.5
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=8)
        if resp.status_code == 200:
            data = resp.json()
            return data['choices'][0]['message']['content']
        return ""
    except Exception:
        return ""

def get_dashboard_context(user_id: int) -> str:
    """Builds a concise summary of the user's latest health data for chatbot context."""
    conn = get_db_connection()
    user = get_user_by_id(user_id)
    records = conn.execute(
        "SELECT * FROM health_records WHERE user_id = ? ORDER BY record_date DESC LIMIT 7",
        (user_id,)
    ).fetchall()
    anomalies = conn.execute(
        "SELECT * FROM anomalies WHERE user_id = ? ORDER BY record_date DESC LIMIT 3",
        (user_id,)
    ).fetchall()
    conn.close()
    
    if not records:
        return f"User Profile: {user['full_name'] if user else 'User'}, Age {user['age'] if user else 24}. No wearable records uploaded yet."
        
    latest = records[0]
    avg_steps = sum(r['steps'] for r in records) / len(records)
    avg_hr = sum(r['avg_heart_rate'] for r in records) / len(records)
    avg_sleep = sum(r['sleep_hours'] for r in records) / len(records)
    
    context = (
        f"User: {user['full_name']}, Age: {user['age']}, Gender: {user['gender']}.\n"
        f"Recent 7-Day Averages: Steps: {int(avg_steps)}, Sleep: {avg_sleep:.1f} hrs, Avg HR: {avg_hr:.1f} bpm.\n"
        f"Latest Record ({latest['record_date']}): Steps: {latest['steps']}, Resting HR: {latest['resting_heart_rate']} bpm, Sleep: {latest['sleep_hours']} hrs.\n"
    )
    if anomalies:
        anom_str = "; ".join([f"{a['metric_name']} on {a['record_date']} ({a['actual_value']})" for a in anomalies])
        context += f"Recent Detected Anomalies: {anom_str}.\n"
        
    return context

def generate_offline_clinical_response(prompt: str, user_id: int, user_context: str) -> str:
    """
    Intelligent clinical rule-based engine providing detailed,
    medically compliant answers for medicine searches, symptoms, and dashboard observations.
    """
    prompt_lower = prompt.lower().strip()
    
    # 1. Emergency safety check first
    for rule in OFFLINE_KNOWLEDGE_RULES:
        if rule.get("is_emergency"):
            if any(kw in prompt_lower for kw in rule["keywords"]):
                return rule["response"]
                
    # 2. Check for medication inquiry in local SQLite medicine database
    med_results = search_medicine(prompt_lower)
    if not med_results:
        # Search individual alphanumeric tokens for generic/brand name match
        import re
        tokens = re.findall(r'[a-zA-Z]{3,}', prompt_lower)
        for token in tokens:
            token_lower = token.lower()
            if token_lower not in ['what', 'when', 'where', 'which', 'about', 'uses', 'side', 'effects', 'dose', 'tell', 'common']:
                res = search_medicine(token_lower)
                if res:
                    for r in res:
                        if token_lower in r['medicine_name'].lower() or token_lower in r['generic_name'].lower():
                            med_results = [r]
                            break
                    if med_results:
                        break
                    
    if med_results:
        med = med_results[0]
        response = (
            f"### 💊 Medication Information: **{med['medicine_name']}**\n"
            f"- **Generic Active Ingredient:** {med['generic_name']}\n"
            f"- **Pharmacological Category:** {med['category']}\n\n"
            f"#### 🎯 Common Clinical Uses:\n"
            f"{med['common_uses']}\n\n"
            f"#### ⚠️ Important Precautions:\n"
            f"{med['precautions']}\n\n"
            f"#### ⚠️ Common Side Effects:\n"
            f"{med['side_effects']}\n\n"
            f"#### 🔄 Potential Interactions:\n"
            f"{med['interactions']}\n\n"
            f"**Medical Safety Reminder:** {med['dosage_warning']}\n\n"
            f"*Disclaimer: This information is strictly educational. Never initiate, adjust, or discontinue any medication without consulting your prescribing physician or licensed pharmacist.*"
        )
        return response

    # 3. Check dashboard-specific observation queries
    if any(q in prompt_lower for q in ['my dashboard', 'my data', 'my health', 'my steps', 'my heart rate', 'my sleep', 'how am i doing']):
        conn = get_db_connection()
        records = conn.execute(
            "SELECT * FROM health_records WHERE user_id = ? ORDER BY record_date DESC LIMIT 7",
            (user_id,)
        ).fetchall()
        anomalies = conn.execute(
            "SELECT * FROM anomalies WHERE user_id = ? ORDER BY record_date DESC LIMIT 5",
            (user_id,)
        ).fetchall()
        conn.close()
        
        if not records:
            return (
                "### 📊 Dashboard Analysis\n\n"
                "I don't see any wearable health records uploaded to your account yet!\n\n"
                "To get personalized observations:\n"
                "1. Head over to the **Upload Data** tab.\n"
                "2. Upload your wearable CSV file (or use our sample 90-day dataset).\n"
                "3. Once processed, ask me again and I will analyze your steps, heart rate trends, and sleep cycles."
            )
            
        latest = records[0]
        avg_steps = sum(r['steps'] for r in records) / len(records)
        avg_sleep = sum(r['sleep_hours'] for r in records) / len(records)
        avg_rhr = sum(r['resting_heart_rate'] for r in records) / len(records)
        
        response = (
            f"### 📊 Clinical Overview of Your Recent Health Data\n\n"
            f"Here is a summary of your recent 7-day wearable biometrics:\n\n"
            f"- **Daily Mobility:** Averaging **{int(avg_steps):,} steps/day**. "
            f"{'🎉 Great consistency!' if avg_steps >= 8000 else 'Consider adding short 10-minute walking breaks during work hours.'}\n"
            f"- **Resting Heart Rate:** Averaging **{avg_rhr:.1f} bpm** (Latest: {latest['resting_heart_rate']} bpm). "
            f"{'Within the typical normal range (60–80 bpm).' if 60 <= avg_rhr <= 80 else 'Slightly outside the typical adult rest range.'}\n"
            f"- **Sleep Recovery:** Averaging **{avg_sleep:.1f} hours/night**. "
            f"{'Healthy sleep duration for adult recovery.' if 7.0 <= avg_sleep <= 8.5 else 'You might benefit from focusing on earlier bedtime consistency.'}\n\n"
        )
        
        if anomalies:
            response += (
                f"**Recent Detected Observations:**\n"
                f"- Found **{len(anomalies)}** metric variations flagged by our ML anomaly detector (such as *{anomalies[0]['metric_name']} on {anomalies[0]['record_date']}*).\n"
                f"Explore the **Anomaly Detection** tab for comprehensive baselines and explanations.\n\n"
            )
        response += "*Always discuss persistent deviations or unusual physiological symptoms with your healthcare provider.*"
        return response

    # 4. Check offline symptom and wellness rules
    for rule in OFFLINE_KNOWLEDGE_RULES:
        if any(kw in prompt_lower for kw in rule["keywords"]):
            return rule["response"]

    # 5. General intelligent response
    return (
        f"### 🩺 Health Information & Guidance\n\n"
        f"Thank you for asking about **'{prompt.strip()}'**.\n\n"
        f"**General Health Perspective:**\n"
        f"- Physiological well-being is strongly influenced by consistent sleep, balanced nutrition, active movement, and stress management.\n"
        f"- When observing changes in your body, keeping a structured journal of when symptoms occur, their severity, and your daily habits is beneficial.\n\n"
        f"**Suggested Next Steps:**\n"
        f"1. You can ask me specific questions like: *'Tell me about Paracetamol'*, *'What causes insomnia?'*, or *'How can I lower my resting heart rate?'*.\n"
        f"2. Check the **Health Analytics** tab to see your biometric patterns over time.\n\n"
        f"*Medical Disclaimer: I am an AI educational assistant. I do not provide diagnostic assessments or medical prescriptions. For any concerning symptoms or medical conditions, always consult a licensed doctor.*"
    )

def handle_chat_query(user_id: int, user_message: str) -> dict:
    """
    Main entry point for Chatbot interactions:
    1. Logs user message to chat_history.
    2. Builds dashboard context.
    3. Calls external LLM (Gemini or OpenAI) if configured.
    4. Falls back to offline clinical engine.
    5. Logs assistant reply to chat_history.
    """
    clean_message = user_message.strip()
    if not clean_message:
        return {"success": False, "error": "Empty message"}
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Save user message
    cursor.execute("""
    INSERT INTO chat_history (user_id, role, content, context_tag)
    VALUES (?, 'user', ?, 'chat')
    """, (user_id, clean_message))
    conn.commit()
    
    # Build user context
    user_context = get_dashboard_context(user_id)
    
    # Try external LLM API if configured
    assistant_reply = ""
    if Config.GEMINI_API_KEY:
        assistant_reply = query_gemini_api(Config.GEMINI_API_KEY, clean_message, user_context)
    elif Config.OPENAI_API_KEY:
        assistant_reply = query_openai_api(Config.OPENAI_API_KEY, clean_message, user_context)
        
    # If no API key or external API failed, use offline clinical engine
    if not assistant_reply:
        assistant_reply = generate_offline_clinical_response(clean_message, user_id, user_context)
        
    # Save assistant message
    cursor.execute("""
    INSERT INTO chat_history (user_id, role, content, context_tag)
    VALUES (?, 'assistant', ?, 'chat')
    """, (user_id, assistant_reply))
    conn.commit()
    conn.close()
    
    return {
        "success": True,
        "reply": assistant_reply,
        "timestamp": datetime.now().strftime("%I:%M %p")
    }

def get_recent_chat_history(user_id: int, limit: int = 20) -> list:
    """Fetches recent conversation history for display."""
    conn = get_db_connection()
    rows = conn.execute("""
    SELECT role, content, timestamp 
    FROM chat_history 
    WHERE user_id = ? 
    ORDER BY id ASC 
    LIMIT ?
    """, (user_id, limit)).fetchall()
    conn.close()
    return [dict(r) for r in rows]
