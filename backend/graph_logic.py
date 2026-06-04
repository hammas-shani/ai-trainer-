from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_groq import ChatGroq
from graph_state import CallState
from dotenv import load_dotenv

load_dotenv()

llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.7)

def call_llm(state: CallState):
    messages = state.get("messages", [])
    persona = state.get("user_detailed_prompt", "Act as a professional interviewer.")

    system = SystemMessage(content=f"""
You are a real-time voice assistant.

Persona: {persona}

Rules:
- Speak VERY short (1-2 lines max)
- Natural conversational tone
- Never repeat yourself
- Ask follow-up questions
""")

    formatted = [system]
    
    for m in messages:
        # 🚀 THE FIX: Handle both Dictionary and Object safely
        if isinstance(m, dict):
            if m.get("role") == "user":
                formatted.append(HumanMessage(content=m.get("content", "")))
            elif m.get("role") == "ai":
                formatted.append(AIMessage(content=m.get("content", "")))
        else:
            # Agar pehle se HumanMessage/AIMessage object hai
            formatted.append(m)

    try:
        response = llm.invoke(formatted)
    except Exception as e:
        print(f"LLM Error: {e}")
        response = AIMessage(content="Sorry, could you repeat that?")

    return {"messages": [response]}

def format_transcript(state: CallState):
    return state

workflow = StateGraph(CallState)

workflow.add_node("agent", call_llm)
workflow.add_node("format", format_transcript)

workflow.set_entry_point("agent")
workflow.add_edge("agent", "format")
workflow.add_edge("format", END)

app_graph = workflow.compile()