from config import config

def get_personality_rules(tone: str) -> dict:
    profiles = {
        "Friendly & casual": {
            "desc": "Friendly HR or recruiter. Very warm, patient, and uses lots of rapport-building language.",
            "fillers": ["Gotcha.", "I see.", "That makes sense.", "Oh, nice!"]
        },
        "Formal & corporate": {
            "desc": "Strict Technical Interviewer or Busy Executive. Very professional, no-nonsense, gets straight to the point.",
            "fillers": ["Understood.", "Noted.", "Right.", "Proceed."]
        },
        "Fast-paced & challenging": {
            "desc": "Startup Founder or Senior Engineering Manager. Impatient, interrupts, asks tough follow-ups quickly.",
            "fillers": ["Okay, but...", "Right, moving on.", "Got it.", "Sure, so..."]
        }
    }
    
    for key, val in profiles.items():
        if key.lower() in tone.lower():
            return val
            
    # Default
    return {
        "desc": "Standard professional.",
        "fillers": ["Got it.", "I see.", "Right."]
    }

def build_system_prompt(payload: dict, stage: str, user_facts: dict) -> str:
    session_type = payload.get("sessionType")
    custom_notes = payload.get("customNotes", "")
    tone = payload.get("tone", "professional")
    
    personality = get_personality_rules(tone)
    
    difficulty = payload.get("difficulty", "Medium")
    
    global_rules = f"""GLOBAL RULES FOR REALISM (CRITICAL):
1. Sound like a real, unscripted professional call — natural phrasing, brief acknowledgments. Do NOT sound like an AI assistant. Never say "How can I help you?".
2. Active Listening: Use natural filler words exactly ONCE at the start of your turn to acknowledge their answer (e.g., {', '.join(personality['fillers'])}).
3. EXTREME LENGTH LIMIT: Keep each message extremely short! Maximum 2 to 3 lines. Maximum 15 to 25 words total. NEVER exceed this. Do not monologue.
4. Ask ONE question per turn. Wait for the user's response before continuing.
5. NEVER ask textbook definitions (e.g. "What is React?"). Instead ask practical follow-ups.
6. STAGE: The current conversation stage is [{stage}]. Guide the conversation smoothly within this stage.
7. DIFFICULTY: The user selected [{difficulty}] difficulty. Tailor your questions to exactly this level. Easy = basics, Medium = practical, Hard = advanced trade-offs, Expert = complex architecture/scaling.
"""

    facts_str = "\n".join([f"- {k}: {v}" for k,v in user_facts.items()])
    if facts_str:
        facts_str = f"USER FACTS DISCOVERED SO FAR (Do not ask these again):\n{facts_str}"
        
    if session_type == "interview":
        field = payload.get("field", "the industry")
        seniority = payload.get("seniority", "this")
        focus = payload.get("focus", "general")
        
        persona = f"You are a {personality['desc']} interviewing a candidate for a {seniority} {field} position."
        
        scenario_rules = f"""IF sessionType == interview:
- Focus of this interview: {focus}.
- If the user struggles (Beginner), ask a simpler practical question. If they answer well (Senior), challenge them with architecture, scaling, or edge-case questions.
"""

    elif session_type == "client_call":
        expertise = payload.get("userExpertise", "expert")
        project = payload.get("projectType", "project")
        client_persona = payload.get("clientPersona", "standard")
        goal = payload.get("callGoal", "discuss")
        
        persona = f"You are a {client_persona} client looking to hire a {expertise} for a {project} project."
        
        scenario_rules = f"""IF sessionType == client_call:
- You are the CLIENT. You need {project}. The user is the {expertise}.
- Ask discovery questions to understand how they would approach your project.
- If they propose pricing, react as a {client_persona}. Push back if budget-conscious.
- Your ultimate goal is to {goal}. Do not reach this goal in the first 2 minutes. Take your time.
"""

    else:
        persona = "You are a generic professional."
        scenario_rules = "No specific rules."

    prompt = f"""{global_rules}

Persona: {persona}

{scenario_rules}

{facts_str}

Additional user notes to incorporate: {custom_notes}"""

    return prompt
