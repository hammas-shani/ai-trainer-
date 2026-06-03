from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_groq import ChatGroq
from graph_state import CallState
import os
from dotenv import load_dotenv

load_dotenv()

# Model Initialisation safely
try:
    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.8)
except Exception as e:
    print(f"🚨 Error initializing ChatGroq: {e}")
    llm = None

def call_llm(state: CallState):
    """Safely invokes the LLM with robust fallbacks"""
    messages = state.get("messages", [])
    user_prompt = state.get("user_detailed_prompt", "")
    
    system_instructions = (
        f"You are having a casual live voice meeting. Your persona is: {user_prompt}\n\n"
        "RULES:\n"
        "1. Be extremely natural. Start with a simple greeting like 'Hi, how are you?'. Keep it casual.\n"
        "2. Speak maximum 1 or 2 short sentences. Never give long paragraphs.\n"
        "3. Review the chat history carefully. NEVER repeat a question you have already asked.\n"
        "4. If you receive '[SILENCE]', react casually like '*laughs* no worries, let's jump to another topic' and ask something fresh."
    )
    
    # Structure messages safely
    if not messages:
        messages = [SystemMessage(content=system_instructions)]
    else:
        if not isinstance(messages[0], SystemMessage):
            messages.insert(0, SystemMessage(content=system_instructions))

    # Safe API Execution
    if llm is None:
        return {"messages": [AIMessage(content="I am having trouble accessing my brain right now. Can we try again?")]}

    try:
        response = llm.invoke(messages)
    except Exception as api_err:
        print(f"🚨 Groq API Execution Failed: {api_err}")
        # Crash proof fallback response so user connection stays alive
        response = AIMessage(content="Oh, sorry about that, I missed what you said. Could you please repeat?")
        
    return {"messages": [response]}

def format_transcript(state: CallState):
    """Safely extracts messages for transcript logging"""
    try:
        messages = state.get("messages", [])
        current_transcript = state.get("formatted_transcript", "")
        
        if len(messages) >= 2:
            last_message = messages[-1]
            second_last_message = messages[-2]
            
            if isinstance(last_message, AIMessage) and isinstance(second_last_message, HumanMessage):
                user_text = second_last_message.content if second_last_message.content != "[SILENCE]" else "..."
                new_entry = f"User: {user_text}\nAI: {last_message.content}\n\n"
                current_transcript += new_entry
                
        return {"formatted_transcript": current_transcript}
    except Exception as format_err:
        print(f"⚠️ Transcript Formatter Error: {format_err}")
        return {"formatted_transcript": state.get("formatted_transcript", "")}

# Graph Setup with safe boundaries
try:
    workflow = StateGraph(CallState)
    workflow.add_node("agent", call_llm)
    workflow.add_node("transcript_formatter", format_transcript)
    workflow.set_entry_point("agent")
    workflow.add_edge("agent", "transcript_formatter")
    workflow.add_edge("transcript_formatter", END)
    app_graph = workflow.compile()
except Exception as graph_build_err:
    print(f"🚨 Failed to build LangGraph workflow: {graph_build_err}")
    app_graph = None