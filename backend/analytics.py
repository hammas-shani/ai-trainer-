from langchain_core.messages import BaseMessage
from langchain_groq import ChatGroq
from config import config

llm = ChatGroq(model=config.MODEL_NAME, temperature=0.3) # lower temp for analysis

def generate_meeting_summary(messages: list[BaseMessage]) -> dict:
    """
    Generates a post-meeting analytics report from the transcript.
    """
    transcript = "\n".join([f"{'User' if m.type == 'human' else 'AI'}: {m.content}" for m in messages])
    
    prompt = f"""
    Analyze the following conversation transcript and provide a structured JSON report.
    Do NOT output anything except valid JSON.
    
    Required keys:
    - "summary": (string) 2-3 sentences summarizing the meeting.
    - "topics_covered": (list of strings)
    - "strengths": (list of strings) User's strengths shown.
    - "weaknesses": (list of strings) Areas of improvement.
    - "communication_score": (int 1-10)
    - "technical_score": (int 1-10)
    - "action_items": (list of strings) Next steps.
    
    Transcript:
    {transcript}
    """
    
    try:
        response = llm.invoke(prompt)
        # Parse JSON from response
        # Using a simple fallback if JSON is wrapped in markdown
        content = response.content.strip()
        if content.startswith("```json"):
            content = content[7:-3]
        import json
        return json.loads(content)
    except Exception as e:
        print(f"Error generating analytics: {e}")
        return {
            "summary": "Analysis failed.",
            "topics_covered": [],
            "strengths": [],
            "weaknesses": [],
            "communication_score": 0,
            "technical_score": 0,
            "action_items": []
        }
