"""
╔══════════════════════════════════════════════════════════════════════════════════╗
║         SAHAAY – Anonymous Mental Health Support Chatbot for Indian Students     ║
║                  Vikshit Bharat 2047 | Pillar 2: Healthcare for All              ║
╚══════════════════════════════════════════════════════════════════════════════════╝

SETUP INSTRUCTIONS:
───────────────────
1. Install dependencies:
       pip install fastapi uvicorn

2. Run the application:
       python app.py

3. The server will start and your browser will open automatically.
4. When you press Ctrl+C, the server stops and the browser tab closes.

NOTE: No login required. Fully anonymous. No data is stored.
"""

import uvicorn
import threading
import webbrowser
import time
import random
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

# ─────────────────────────────────────────────────────────────────────────────
#  CHATBOT LOGIC
# ─────────────────────────────────────────────────────────────────────────────

EMERGENCY_KEYWORDS = [
    "suicide", "suicidal", "kill myself", "end my life", "self harm", "self-harm",
    "want to die", "don't want to live", "no reason to live", "cutting myself",
    "hurt myself", "not worth living", "worthless", "depressed badly", "severe depression"
]

BREATHING_EXERCISE = """
🌬️ *Let's do a quick breathing exercise together:*

**Box Breathing (4-4-4-4):**
1. **Inhale** slowly for 4 counts… 1… 2… 3… 4…
2. **Hold** your breath for 4 counts… 1… 2… 3… 4…
3. **Exhale** slowly for 4 counts… 1… 2… 3… 4…
4. **Hold** again for 4 counts… 1… 2… 3… 4…

Repeat this 3–4 times. 🙏

This technique is used by doctors and athletes to calm the nervous system instantly. You're doing great.
"""

AFFIRMATIONS = [
    "You are stronger than you think. Every exam is just a stepping stone, not the final destination. 🌟",
    "One difficult chapter does not define your entire story. Keep going. 💪",
    "It's okay to not be okay. Asking for help is the bravest thing you can do. 🤝",
    "Your worth is not measured by your rank or marks. You are more than a score. ❤️",
    "Today might be hard, but you've survived every difficult day so far. That's 100% success rate. 🎯",
    "Ruko mat. Thako to ruk jao, par ruko mat. — Don't stop. Rest if tired, but don't quit. 🇮🇳",
    "Failure is not the opposite of success — it's part of the journey to success. 🌱",
    "Your parents' dreams for you come from love. And love means they want you to be happy first. 💛",
]

STUDY_TIPS = [
    "🕐 **Pomodoro Technique:** Study for 25 minutes, then take a 5-minute break. After 4 cycles, take a 30-minute break. Your brain needs rest to consolidate memory.",
    "📝 **Active Recall:** Instead of re-reading, close the book and write what you remember. It's 3x more effective than passive reading.",
    "🗺️ **Mind Mapping:** Draw visual diagrams connecting concepts. Especially powerful for Biology, History, and Polity.",
    "🌙 **Sleep is studying:** 7–8 hours of sleep is non-negotiable. Your brain literally organizes memories during deep sleep.",
    "📅 **Spaced Repetition:** Review notes at day 1, day 3, day 7, day 21. This is how toppers retain information for months.",
    "🤝 **Teach to learn:** Explain a concept to someone else (or even to yourself out loud). Teaching exposes gaps in understanding instantly.",
    "📵 **Phone-free zones:** Keep your phone in another room during study sessions. Even its presence reduces focus by 20%.",
]

EXAM_RESPONSES = [
    "Exam pressure is real, and you're not alone in feeling this way. Millions of students across India feel exactly what you're feeling right now. 🇮🇳\n\nHere's something important: **preparation reduces anxiety**. Break your syllabus into small daily goals. Progress, however small, builds confidence.",
    "JEE, NEET, UPSC, boards — India has some of the most competitive exams in the world. The pressure is immense, and it's completely valid to feel overwhelmed.\n\nBut remember: **your entire future is not riding on one exam**. Many successful people have re-attempted, changed paths, or found unexpected routes. Your journey is yours alone.",
    "When exam anxiety hits, your brain goes into fight-or-flight mode. That's biology, not weakness. 🧠\n\nTry this: write down your **three biggest exam worries** on paper. Just naming them reduces their power over you. Then write one small action you can take today.",
]

PARENTAL_PRESSURE_RESPONSES = [
    "Family expectations in India often come wrapped in love — but the weight can feel crushing. You're not alone in this. 💛\n\nYour parents want the best for you because they care. But *you* are the one who has to live your life. It's okay to gently communicate how you feel.\n\nHave you tried talking to them — not about marks, but about how you're feeling inside?",
    "The pressure of being an 'ideal' child in an Indian household is something very few people talk about openly. The constant comparisons, the aunties, the 'log kya kahenge' — it's exhausting. 😔\n\nYour feelings are valid. You don't have to be perfect. You just have to be yourself, and that is enough.",
    "Sometimes parents push hard because they faced hardships we don't fully know about. Their pressure comes from fear — fear that you'll struggle like they did. 🙏\n\nThat doesn't make the pressure okay, but understanding it might make it easier to have a real conversation with them.",
]

CAREER_CONFUSION_RESPONSES = [
    "Career confusion is extremely common among students in India, where society often pushes towards a handful of 'acceptable' paths. 🎭\n\nHere's a question worth sitting with: **What would you do if money and family opinion didn't matter?** That answer often points toward your true interest.",
    "It's okay to not have everything figured out. Most people, even successful ones, changed direction multiple times. 🔄\n\nExplore internships, online courses, and informational interviews. Talk to people working in fields you're curious about. Clarity comes from *action*, not from thinking alone.",
    "Engineering, medicine, law — these are respected paths, but they're not the only paths. Design, psychology, data science, entrepreneurship, arts — India's economy is changing rapidly. 🚀\n\nFollow your curiosity. Skill-building in any genuine interest leads somewhere good.",
]

LONELINESS_RESPONSES = [
    "Feeling lonely, especially in a new city or college, is one of the most common yet unspoken student experiences. 🌙\n\nLoneliness is not a personal failure — it's a signal that you need more connection. Start small: smile at one person, join one club, attend one event.",
    "In hostels and PGs, surrounded by people, you can still feel completely alone. That paradox is real and painful. 💙\n\nYou don't need 50 friends. Even one genuine connection can change everything. Be the person who shows up. Who checks in. Who listens.",
]

GENERAL_RESPONSES = [
    "I hear you. Whatever you're going through, you don't have to face it alone. I'm here to listen and support you. 🤝\n\nCan you tell me more about what's been weighing on you lately?",
    "Thank you for sharing that with me. It takes courage to open up, even anonymously. 💙\n\nRemember — your feelings are valid. What you're experiencing is real, and it matters.",
    "It sounds like things have been really tough. Let's take this one step at a time. 🌱\n\nWould you like some breathing exercises, study tips, or just someone to talk to right now?",
    "You reached out today — that itself is a sign of strength. I'm proud of you for that. ❤️\n\nWhat's been on your mind most?",
]

GREETINGS = [
    "Namaste! 🙏 I'm **Sahaay** — your safe, anonymous mental wellness companion.\n\nI'm here to listen without judgment. Whether it's exam stress, family pressure, career confusion, or just a heavy day — you can talk to me.\n\n*What's on your mind today?*",
    "Hello! 👋 Welcome to Sahaay — a safe space just for you.\n\nEverything here is completely anonymous. I won't judge, I won't remember, I'll just be here for you.\n\n*How are you feeling today?*",
]

EMERGENCY_RESPONSE = """
🚨 **I'm really concerned about you right now.**

Please know: **You matter. Your life has value. This pain is temporary.**

📞 **Reach out immediately — someone is waiting to help:**

| Helpline | Number | Available |
|---|---|---|
| 🇮🇳 **iCall (TISS)** | **9152987821** | Mon–Sat, 8AM–10PM |
| 🇮🇳 **Vandrevala Foundation** | **1860-2662-345** | 24/7 |
| 🇮🇳 **Kiran Mental Health** | **1800-599-0019** | 24/7 Free |
| 🇮🇳 **AASRA** | **9820466627** | 24/7 |
| 🚑 **Emergency** | **112** | 24/7 |

---

**You do not have to face this alone.**

I'm still here with you. Can you tell me a little about what's happening? Sometimes putting it into words helps. 💙
"""


def detect_intent(message: str) -> str:
    """Detect the user's intent from their message."""
    msg = message.lower().strip()

    for keyword in EMERGENCY_KEYWORDS:
        if keyword in msg:
            return "emergency"

    if any(w in msg for w in ["hello", "hi", "hey", "namaste", "start", "hii", "helo"]):
        return "greeting"
    if any(w in msg for w in ["breath", "calm", "panic", "anxious", "anxiety", "breathe", "relax"]):
        return "breathing"
    if any(w in msg for w in ["affirmation", "motivat", "inspire", "quote", "encourage", "uplift"]):
        return "affirmation"
    if any(w in msg for w in ["study", "tip", "technique", "focus", "concentrate", "remember", "memorize", "revision"]):
        return "study_tips"
    if any(w in msg for w in ["exam", "jee", "neet", "upsc", "board", "test", "marks", "result", "score", "rank", "fail"]):
        return "exam"
    if any(w in msg for w in ["parent", "family", "papa", "mummy", "mom", "dad", "pressure", "expect", "disappoint", "ghar", "log kya"]):
        return "parental_pressure"
    if any(w in msg for w in ["career", "job", "future", "path", "course", "branch", "confused", "direction", "engineer", "doctor", "choices"]):
        return "career"
    if any(w in msg for w in ["alone", "lonely", "friend", "nobody", "isolated", "no one"]):
        return "loneliness"

    return "general"


def generate_response(message: str) -> dict:
    """Generate a chatbot response for the given message."""
    intent = detect_intent(message)

    if intent == "emergency":
        return {"response": EMERGENCY_RESPONSE, "type": "emergency"}

    if intent == "greeting":
        return {"response": random.choice(GREETINGS), "type": "normal"}

    if intent == "breathing":
        return {"response": BREATHING_EXERCISE, "type": "normal"}

    if intent == "affirmation":
        affirmation = random.choice(AFFIRMATIONS)
        return {"response": f"✨ Here's something to hold onto today:\n\n*\"{affirmation}\"*\n\nYou've got this. 💪", "type": "normal"}

    if intent == "study_tips":
        tip = random.choice(STUDY_TIPS)
        return {"response": f"Here's a proven study technique for you:\n\n{tip}\n\nWould you like more tips, or is there something specific you're struggling with?", "type": "normal"}

    if intent == "exam":
        return {"response": random.choice(EXAM_RESPONSES), "type": "normal"}

    if intent == "parental_pressure":
        return {"response": random.choice(PARENTAL_PRESSURE_RESPONSES), "type": "normal"}

    if intent == "career":
        return {"response": random.choice(CAREER_CONFUSION_RESPONSES), "type": "normal"}

    if intent == "loneliness":
        return {"response": random.choice(LONELINESS_RESPONSES), "type": "normal"}

    return {"response": random.choice(GENERAL_RESPONSES), "type": "normal"}


# ─────────────────────────────────────────────────────────────────────────────
#  HTML / CSS / JS FRONTEND (embedded as a Python string)
# ─────────────────────────────────────────────────────────────────────────────

HTML_CONTENT = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>Sahaay – Mental Wellness Companion</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600;700&family=Noto+Sans+Devanagari:wght@400;500&display=swap" rel="stylesheet">
<style>
  /* ── RESET & BASE ─────────────────────────────────────────── */
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --bg: #0f1117;
    --surface: rgba(255,255,255,0.04);
    --surface-hover: rgba(255,255,255,0.07);
    --border: rgba(255,255,255,0.09);
    --accent: #7ee8a2;
    --accent2: #80d4f5;
    --accent3: #f5c77e;
    --emergency: #ff6b6b;
    --text: #e8eaf0;
    --text-muted: #8b909e;
    --user-bubble: linear-gradient(135deg, #2e7d5e, #1a5c43);
    --bot-bubble: rgba(255,255,255,0.05);
    --shadow: 0 8px 32px rgba(0,0,0,0.4);
    --radius: 18px;
    --radius-sm: 10px;
    --font: 'Sora', sans-serif;
    --transition: 0.25s ease;
    --glow: 0 0 24px rgba(126,232,162,0.15);
  }

  .light-mode {
    --bg: #f0f4f8;
    --surface: rgba(255,255,255,0.75);
    --surface-hover: rgba(255,255,255,0.9);
    --border: rgba(0,0,0,0.1);
    --text: #1a1d2e;
    --text-muted: #6b7280;
    --user-bubble: linear-gradient(135deg, #2e7d5e, #3aaa7a);
    --bot-bubble: rgba(255,255,255,0.85);
    --shadow: 0 8px 32px rgba(0,0,0,0.12);
    --glow: 0 0 24px rgba(46,125,94,0.12);
  }

  html, body {
    height: 100%;
    font-family: var(--font);
    background: var(--bg);
    color: var(--text);
    transition: background var(--transition), color var(--transition);
    overflow: hidden;
  }

  /* ── BACKGROUND AMBIENT ───────────────────────────────────── */
  body::before {
    content: '';
    position: fixed; inset: 0; z-index: 0;
    background:
      radial-gradient(ellipse 60% 50% at 20% 20%, rgba(126,232,162,0.06) 0%, transparent 70%),
      radial-gradient(ellipse 50% 60% at 80% 80%, rgba(128,212,245,0.05) 0%, transparent 70%),
      radial-gradient(ellipse 40% 40% at 50% 50%, rgba(245,199,126,0.03) 0%, transparent 70%);
    pointer-events: none;
  }

  .light-mode body::before {
    background:
      radial-gradient(ellipse 60% 50% at 20% 20%, rgba(46,125,94,0.07) 0%, transparent 70%),
      radial-gradient(ellipse 50% 60% at 80% 80%, rgba(0,120,180,0.05) 0%, transparent 70%);
  }

  /* ── LAYOUT ───────────────────────────────────────────────── */
  #app {
    position: relative; z-index: 1;
    display: flex; flex-direction: column; align-items: center;
    height: 100vh; padding: 16px;
  }

  /* ── HEADER ───────────────────────────────────────────────── */
  header {
    width: 100%; max-width: 760px;
    display: flex; align-items: center; justify-content: space-between;
    padding: 14px 20px;
    background: var(--surface);
    backdrop-filter: blur(20px);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    margin-bottom: 12px;
    box-shadow: var(--shadow);
    flex-shrink: 0;
  }

  .logo-area {
    display: flex; align-items: center; gap: 12px;
  }

  .logo-icon {
    width: 42px; height: 42px;
    background: linear-gradient(135deg, #2e7d5e, #7ee8a2);
    border-radius: 12px;
    display: flex; align-items: center; justify-content: center;
    font-size: 20px;
    box-shadow: 0 4px 16px rgba(126,232,162,0.3);
    flex-shrink: 0;
  }

  .logo-text h1 {
    font-size: 1.2rem; font-weight: 700;
    background: linear-gradient(135deg, var(--accent), var(--accent2));
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -0.02em;
  }

  .logo-text p {
    font-size: 0.68rem; color: var(--text-muted);
    font-weight: 400; letter-spacing: 0.03em;
    margin-top: 1px;
  }

  .header-actions { display: flex; align-items: center; gap: 10px; }

  .anon-badge {
    display: flex; align-items: center; gap: 6px;
    background: rgba(126,232,162,0.1);
    border: 1px solid rgba(126,232,162,0.2);
    color: var(--accent);
    font-size: 0.68rem; font-weight: 600;
    padding: 5px 10px; border-radius: 20px;
    letter-spacing: 0.04em;
  }

  .anon-dot {
    width: 6px; height: 6px;
    background: var(--accent);
    border-radius: 50%;
    animation: pulse 2s infinite;
  }

  @keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.5; transform: scale(0.8); }
  }

  .toggle-btn {
    width: 38px; height: 38px;
    background: var(--surface-hover);
    border: 1px solid var(--border);
    border-radius: 10px;
    cursor: pointer;
    display: flex; align-items: center; justify-content: center;
    font-size: 17px;
    transition: all var(--transition);
    color: var(--text);
  }
  .toggle-btn:hover { transform: scale(1.08); background: var(--surface-hover); }

  /* ── CHAT WINDOW ──────────────────────────────────────────── */
  #chat-window {
    width: 100%; max-width: 760px;
    flex: 1;
    overflow-y: auto;
    padding: 16px;
    background: var(--surface);
    backdrop-filter: blur(20px);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    box-shadow: var(--shadow);
    display: flex; flex-direction: column; gap: 14px;
    scroll-behavior: smooth;
  }

  #chat-window::-webkit-scrollbar { width: 4px; }
  #chat-window::-webkit-scrollbar-track { background: transparent; }
  #chat-window::-webkit-scrollbar-thumb { background: var(--border); border-radius: 4px; }

  /* ── DATE DIVIDER ─────────────────────────────────────────── */
  .date-divider {
    text-align: center;
    font-size: 0.65rem; color: var(--text-muted);
    font-weight: 500; letter-spacing: 0.08em;
    text-transform: uppercase;
    padding: 4px 0;
  }

  /* ── MESSAGE ROWS ─────────────────────────────────────────── */
  .msg-row {
    display: flex; gap: 10px;
    animation: msgIn 0.35s cubic-bezier(0.34, 1.56, 0.64, 1) both;
  }

  @keyframes msgIn {
    from { opacity: 0; transform: translateY(16px) scale(0.97); }
    to   { opacity: 1; transform: translateY(0) scale(1); }
  }

  .msg-row.user { flex-direction: row-reverse; }

  .avatar {
    width: 34px; height: 34px; border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 15px; flex-shrink: 0; align-self: flex-end;
  }

  .avatar.bot {
    background: linear-gradient(135deg, #1a5c43, #2e7d5e);
    box-shadow: 0 2px 12px rgba(46,125,94,0.4);
  }

  .avatar.user {
    background: linear-gradient(135deg, #1e3a5f, #2a5298);
    box-shadow: 0 2px 12px rgba(42,82,152,0.4);
  }

  .bubble {
    max-width: 78%;
    padding: 13px 17px;
    border-radius: var(--radius);
    font-size: 0.875rem;
    line-height: 1.65;
    position: relative;
    word-wrap: break-word;
  }

  .bubble.bot {
    background: var(--bot-bubble);
    border: 1px solid var(--border);
    border-bottom-left-radius: 4px;
    color: var(--text);
    box-shadow: 0 2px 12px rgba(0,0,0,0.15);
  }

  .bubble.user {
    background: var(--user-bubble);
    border-bottom-right-radius: 4px;
    color: #fff;
    box-shadow: 0 4px 16px rgba(46,125,94,0.35);
  }

  .bubble.emergency {
    border: 1px solid rgba(255,107,107,0.4);
    background: rgba(255,107,107,0.06);
    box-shadow: 0 0 20px rgba(255,107,107,0.15);
  }

  /* Markdown-like formatting */
  .bubble strong { font-weight: 700; color: var(--accent); }
  .bubble.user strong { color: rgba(255,255,255,0.95); }
  .bubble em { font-style: italic; color: var(--accent2); }
  .bubble.user em { color: rgba(255,255,255,0.85); }

  .bubble table {
    border-collapse: collapse;
    width: 100%;
    margin: 10px 0;
    font-size: 0.8rem;
  }
  .bubble table td, .bubble table th {
    padding: 7px 10px;
    border: 1px solid var(--border);
    text-align: left;
  }
  .bubble table th {
    background: rgba(126,232,162,0.08);
    font-weight: 600;
    color: var(--accent);
  }
  .bubble table tr:nth-child(even) { background: rgba(255,255,255,0.02); }

  .bubble hr {
    border: none;
    border-top: 1px solid var(--border);
    margin: 10px 0;
  }

  .msg-time {
    font-size: 0.6rem; color: var(--text-muted);
    margin-top: 5px; text-align: right;
  }
  .msg-row.bot .msg-time { text-align: left; }

  /* ── TYPING INDICATOR ─────────────────────────────────────── */
  .typing-row { display: flex; gap: 10px; }
  .typing-bubble {
    background: var(--bot-bubble);
    border: 1px solid var(--border);
    padding: 14px 18px;
    border-radius: var(--radius);
    border-bottom-left-radius: 4px;
    display: flex; align-items: center; gap: 5px;
  }
  .typing-dot {
    width: 7px; height: 7px; border-radius: 50%;
    background: var(--text-muted);
    animation: typingBounce 1.2s ease infinite;
  }
  .typing-dot:nth-child(2) { animation-delay: 0.2s; }
  .typing-dot:nth-child(3) { animation-delay: 0.4s; }
  @keyframes typingBounce {
    0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
    30% { transform: translateY(-6px); opacity: 1; }
  }

  /* ── QUICK ACTIONS ────────────────────────────────────────── */
  #quick-actions {
    width: 100%; max-width: 760px;
    display: flex; gap: 8px; flex-wrap: wrap;
    margin: 10px 0;
    padding: 0 2px;
  }

  .quick-btn {
    display: flex; align-items: center; gap: 6px;
    padding: 7px 13px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 20px;
    color: var(--text-muted);
    font-size: 0.72rem; font-weight: 500;
    cursor: pointer;
    transition: all var(--transition);
    font-family: var(--font);
    backdrop-filter: blur(10px);
    white-space: nowrap;
  }
  .quick-btn:hover {
    background: var(--surface-hover);
    color: var(--accent);
    border-color: rgba(126,232,162,0.3);
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(126,232,162,0.1);
  }

  /* ── INPUT BAR ────────────────────────────────────────────── */
  #input-bar {
    width: 100%; max-width: 760px;
    display: flex; gap: 10px; align-items: flex-end;
    padding: 12px 14px;
    background: var(--surface);
    backdrop-filter: blur(20px);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    box-shadow: var(--shadow), var(--glow);
    margin-top: 10px;
    flex-shrink: 0;
    transition: box-shadow var(--transition), border-color var(--transition);
  }

  #input-bar:focus-within {
    border-color: rgba(126,232,162,0.35);
    box-shadow: var(--shadow), 0 0 32px rgba(126,232,162,0.12);
  }

  #user-input {
    flex: 1;
    background: transparent;
    border: none; outline: none;
    color: var(--text);
    font-family: var(--font);
    font-size: 0.88rem;
    line-height: 1.5;
    resize: none;
    max-height: 120px;
    min-height: 22px;
    overflow-y: auto;
    placeholder-color: var(--text-muted);
  }
  #user-input::placeholder { color: var(--text-muted); }

  #send-btn {
    width: 42px; height: 42px; flex-shrink: 0;
    background: linear-gradient(135deg, #2e7d5e, #7ee8a2);
    border: none; border-radius: 12px;
    cursor: pointer;
    display: flex; align-items: center; justify-content: center;
    transition: all var(--transition);
    box-shadow: 0 4px 16px rgba(126,232,162,0.3);
    align-self: flex-end;
  }
  #send-btn:hover { transform: scale(1.06); box-shadow: 0 6px 24px rgba(126,232,162,0.45); }
  #send-btn:active { transform: scale(0.97); }
  #send-btn svg { width: 18px; height: 18px; fill: #fff; }

  /* ── FOOTER ───────────────────────────────────────────────── */
  .footer-note {
    font-size: 0.62rem; color: var(--text-muted);
    text-align: center; margin-top: 8px; letter-spacing: 0.02em;
    flex-shrink: 0;
  }

  /* ── EMERGENCY BANNER ─────────────────────────────────────── */
  #emergency-banner {
    display: none;
    position: fixed; bottom: 0; left: 0; right: 0;
    background: linear-gradient(90deg, #7f1d1d, #991b1b);
    color: #fff;
    text-align: center;
    padding: 12px 20px;
    font-size: 0.8rem; font-weight: 600;
    z-index: 100;
    animation: slideUp 0.4s ease;
    letter-spacing: 0.03em;
  }
  @keyframes slideUp {
    from { transform: translateY(100%); }
    to   { transform: translateY(0); }
  }

  /* ── WELCOME CARD ─────────────────────────────────────────── */
  .welcome-card {
    background: linear-gradient(135deg, rgba(46,125,94,0.15), rgba(128,212,245,0.08));
    border: 1px solid rgba(126,232,162,0.2);
    border-radius: var(--radius);
    padding: 20px;
    text-align: center;
    margin: 10px 0;
  }
  .welcome-card .big-emoji { font-size: 2.5rem; margin-bottom: 8px; }
  .welcome-card h2 { font-size: 1rem; font-weight: 600; margin-bottom: 6px; color: var(--accent); }
  .welcome-card p { font-size: 0.78rem; color: var(--text-muted); line-height: 1.6; }

  /* ── SCROLLBAR LIGHT MODE ─────────────────────────────────── */
  .light-mode #chat-window::-webkit-scrollbar-thumb { background: rgba(0,0,0,0.15); }

  /* ── RESPONSIVE ───────────────────────────────────────────── */
  @media (max-width: 600px) {
    #app { padding: 8px; }
    header { padding: 10px 14px; }
    .logo-text h1 { font-size: 1rem; }
    .anon-badge span { display: none; }
    .bubble { max-width: 88%; font-size: 0.82rem; }
    #quick-actions { overflow-x: auto; flex-wrap: nowrap; padding-bottom: 4px; }
  }

  /* ── SCROLLBAR ─────────────────────────────────────────────── */
  * { scrollbar-width: thin; scrollbar-color: var(--border) transparent; }
</style>
</head>
<body>
<div id="app">
  <!-- HEADER -->
  <header>
    <div class="logo-area">
      <div class="logo-icon">🌿</div>
      <div class="logo-text">
        <h1>Sahaay</h1>
        <p>सहाय · Your Anonymous Wellness Companion</p>
      </div>
    </div>
    <div class="header-actions">
      <div class="anon-badge">
        <div class="anon-dot"></div>
        <span>Anonymous</span>
      </div>
      <button class="toggle-btn" id="theme-toggle" title="Toggle theme" aria-label="Toggle theme">🌙</button>
    </div>
  </header>

  <!-- CHAT WINDOW -->
  <div id="chat-window" role="log" aria-live="polite" aria-label="Chat messages">
    <div class="welcome-card">
      <div class="big-emoji">🙏</div>
      <h2>Welcome to Sahaay</h2>
      <p>A safe, judgment-free space for Indian students.<br/>
      Talk about anything — stress, exams, family, career, or just how you're feeling today.</p>
    </div>
    <div class="date-divider">Today</div>
  </div>

  <!-- QUICK ACTIONS -->
  <div id="quick-actions" role="navigation" aria-label="Quick actions">
    <button class="quick-btn" onclick="sendQuick('I need a breathing exercise 🌬️')">🌬️ Breathing</button>
    <button class="quick-btn" onclick="sendQuick('Give me a motivational quote ✨')">✨ Motivation</button>
    <button class="quick-btn" onclick="sendQuick('I need study tips 📚')">📚 Study Tips</button>
    <button class="quick-btn" onclick="sendQuick('I am stressed about exams 😰')">😰 Exam Stress</button>
    <button class="quick-btn" onclick="sendQuick('Family pressure is too much 😔')">😔 Family Pressure</button>
    <button class="quick-btn" onclick="sendQuick('I am confused about my career 🤔')">🤔 Career</button>
  </div>

  <!-- INPUT BAR -->
  <div id="input-bar">
    <textarea
      id="user-input"
      placeholder="Type how you're feeling… (completely anonymous)"
      rows="1"
      aria-label="Message input"
      maxlength="1000"
    ></textarea>
    <button id="send-btn" onclick="sendMessage()" aria-label="Send message">
      <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
      </svg>
    </button>
  </div>

  <p class="footer-note">
    Vikshit Bharat 2047 · Ayushman Bharat · All conversations are private &amp; never stored
  </p>
</div>

<!-- EMERGENCY BANNER -->
<div id="emergency-banner">
  🚨 If you're in crisis, call <strong>Kiran: 1800-599-0019</strong> or <strong>Vandrevala: 1860-2662-345</strong> (Free · 24/7)
</div>

<script>
  /* ── STATE ───────────────────────────────────────────────── */
  const API_BASE = window.location.origin;
  let isTyping = false;
  let isLight = false;

  /* ── DOM REFS ─────────────────────────────────────────────── */
  const chatWindow   = document.getElementById('chat-window');
  const userInput    = document.getElementById('user-input');
  const sendBtn      = document.getElementById('send-btn');
  const themeToggle  = document.getElementById('theme-toggle');
  const emergBanner  = document.getElementById('emergency-banner');

  /* ── THEME TOGGLE ─────────────────────────────────────────── */
  themeToggle.addEventListener('click', () => {
    isLight = !isLight;
    document.documentElement.classList.toggle('light-mode', isLight);
    themeToggle.textContent = isLight ? '☀️' : '🌙';
  });

  /* ── AUTO-RESIZE TEXTAREA ────────────────────────────────── */
  userInput.addEventListener('input', () => {
    userInput.style.height = 'auto';
    userInput.style.height = Math.min(userInput.scrollHeight, 120) + 'px';
  });

  userInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  /* ── UTILS ────────────────────────────────────────────────── */
  function getTime() {
    return new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' });
  }

  function scrollToBottom() {
    chatWindow.scrollTop = chatWindow.scrollHeight;
  }

  /* ── SIMPLE MARKDOWN RENDERER ────────────────────────────── */
  function renderMarkdown(text) {
    return text
      // Tables
      .replace(/\|(.+)\|\n\|[-| ]+\|\n((?:\|.+\|\n?)+)/g, (_, header, rows) => {
        const ths = header.split('|').filter(c => c.trim()).map(c => `<th>${c.trim()}</th>`).join('');
        const trs = rows.trim().split('\n').map(row => {
          const tds = row.split('|').filter(c => c.trim()).map(c => `<td>${c.trim()}</td>`).join('');
          return `<tr>${tds}</tr>`;
        }).join('');
        return `<table><thead><tr>${ths}</tr></thead><tbody>${trs}</tbody></table>`;
      })
      // HR
      .replace(/^---$/gm, '<hr/>')
      // Bold
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      // Italic
      .replace(/\*(.+?)\*/g, '<em>$1</em>')
      // Newlines
      .replace(/\n/g, '<br/>');
  }

  /* ── ADD MESSAGE ─────────────────────────────────────────── */
  function addMessage(text, sender, type = 'normal') {
    const row = document.createElement('div');
    row.className = `msg-row ${sender}`;

    const av = document.createElement('div');
    av.className = `avatar ${sender}`;
    av.textContent = sender === 'bot' ? '🌿' : '🧑';

    const bubbleWrap = document.createElement('div');

    const bubble = document.createElement('div');
    bubble.className = `bubble ${sender}${type === 'emergency' ? ' emergency' : ''}`;
    bubble.innerHTML = renderMarkdown(text);

    const timeEl = document.createElement('div');
    timeEl.className = 'msg-time';
    timeEl.textContent = getTime();

    bubbleWrap.appendChild(bubble);
    bubbleWrap.appendChild(timeEl);

    if (sender === 'user') {
      row.appendChild(bubbleWrap);
      row.appendChild(av);
    } else {
      row.appendChild(av);
      row.appendChild(bubbleWrap);
    }

    chatWindow.appendChild(row);
    scrollToBottom();
  }

  /* ── TYPING INDICATOR ────────────────────────────────────── */
  function showTyping() {
    const row = document.createElement('div');
    row.className = 'typing-row';
    row.id = 'typing-indicator';

    const av = document.createElement('div');
    av.className = 'avatar bot';
    av.textContent = '🌿';

    const bubble = document.createElement('div');
    bubble.className = 'typing-bubble';
    bubble.innerHTML = '<div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>';

    row.appendChild(av);
    row.appendChild(bubble);
    chatWindow.appendChild(row);
    scrollToBottom();
  }

  function hideTyping() {
    const el = document.getElementById('typing-indicator');
    if (el) el.remove();
  }

  /* ── EMERGENCY BANNER ────────────────────────────────────── */
  function showEmergencyBanner() {
    emergBanner.style.display = 'block';
    setTimeout(() => { emergBanner.style.display = 'none'; }, 15000);
  }

  /* ── SEND MESSAGE ─────────────────────────────────────────── */
  async function sendMessage() {
    const text = userInput.value.trim();
    if (!text || isTyping) return;

    addMessage(text, 'user');
    userInput.value = '';
    userInput.style.height = 'auto';

    isTyping = true;
    sendBtn.disabled = true;
    sendBtn.style.opacity = '0.5';

    showTyping();

    // Realistic typing delay
    const delay = 800 + Math.random() * 800;

    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text })
      });

      await new Promise(r => setTimeout(r, delay));
      hideTyping();

      if (!res.ok) throw new Error('Server error');
      const data = await res.json();

      addMessage(data.response, 'bot', data.type);

      if (data.type === 'emergency') {
        showEmergencyBanner();
      }

    } catch (err) {
      hideTyping();
      addMessage('I\'m having a little trouble connecting right now. 😔 Please try again in a moment.', 'bot');
    }

    isTyping = false;
    sendBtn.disabled = false;
    sendBtn.style.opacity = '1';
    userInput.focus();
  }

  /* ── QUICK SEND ──────────────────────────────────────────── */
  function sendQuick(text) {
    userInput.value = text;
    sendMessage();
  }

  /* ── HEARTBEAT – auto-close on server shutdown ───────────── */
  let heartbeatFails = 0;
  async function heartbeat() {
    try {
      const res = await fetch(`${API_BASE}/health`, { cache: 'no-store' });
      if (res.ok) { heartbeatFails = 0; return; }
    } catch (_) {}

    heartbeatFails++;
    if (heartbeatFails >= 3) {
      // Server is down — close the tab
      window.close();
    }
  }
  setInterval(heartbeat, 3000);

  /* ── INIT GREETING ────────────────────────────────────────── */
  window.addEventListener('DOMContentLoaded', async () => {
    await new Promise(r => setTimeout(r, 600));
    showTyping();
    await new Promise(r => setTimeout(r, 1200));
    hideTyping();

    const greetings = [
      "Namaste! 🙏 I'm **Sahaay** — your safe, anonymous mental wellness companion.\n\nI'm here to listen without judgment. Whether it's exam stress, family pressure, career confusion, or just a heavy day — you can talk to me.\n\n*What's on your mind today?*",
    ];
    addMessage(greetings[0], 'bot');
    userInput.focus();
  });
</script>
</body>
</html>
"""


# ─────────────────────────────────────────────────────────────────────────────
#  FASTAPI APP
# ─────────────────────────────────────────────────────────────────────────────

app = FastAPI(title="Sahaay Mental Health Chatbot", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str


@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Serve the embedded frontend."""
    return HTMLResponse(content=HTML_CONTENT)


@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    """Process a chat message and return a response."""
    if not req.message or not req.message.strip():
        return JSONResponse({"response": "Please share what's on your mind. I'm here to listen. 💙", "type": "normal"})

    result = generate_response(req.message)
    return JSONResponse(result)


@app.get("/health")
async def health_check():
    """Health check endpoint — used by frontend heartbeat to detect shutdown."""
    return {"status": "ok", "service": "Sahaay"}


# ─────────────────────────────────────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

HOST = "127.0.0.1"
PORT = 8765


def open_browser():
    """Wait briefly then open the browser."""
    time.sleep(1.8)
    webbrowser.open(f"http://{HOST}:{PORT}")


if __name__ == "__main__":
    print()
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║     🌿  SAHAAY – Anonymous Mental Health Chatbot                 ║")
    print("║         Vikshit Bharat 2047 · Ayushman Bharat                   ║")
    print("╠══════════════════════════════════════════════════════════════════╣")
    print(f"║  🚀  Server   →  http://{HOST}:{PORT}                            ║")
    print("║  🌐  Browser opens automatically in a moment…                   ║")
    print("║  🔒  Fully anonymous — no data stored                           ║")
    print("║  ⛔  Press Ctrl+C to stop                                       ║")
    print("╚══════════════════════════════════════════════════════════════════╝")
    print()
# Open browser in background thread
    threading.Thread(target=open_browser, daemon=True).start()

    # Start server (blocking)
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)), log_level="warning")