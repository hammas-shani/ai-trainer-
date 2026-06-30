from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_groq import ChatGroq
from graph_state import CallState
from memory import TokenBudgetManager, ContextRetrievalEngine
from config import config
from prompt_builder import build_system_prompt
from dotenv import load_dotenv
import re

load_dotenv()

llm = ChatGroq(model=config.MODEL_NAME, temperature=config.TEMPERATURE)

def conversation_health_monitor(response_text: str) -> bool:
    sentences = re.split(r'[.!?]+', response_text)
    sentences = [s for s in sentences if s.strip()]
    if len(sentences) > config.MAX_AI_SENTENCES + 2:
        return False
        
    questions = response_text.count("?")
    if questions > 1:
        return False
        
    robotic_phrases = ["as an ai", "how can i help you", "i'm here to assist"]
    if any(phrase in response_text.lower() for phrase in robotic_phrases):
        return False
        
    return True

def planner_node(state: CallState):
    """
    Examines the conversation state and progresses the stage if needed.
    """
    messages = state.get("messages", [])
    current_stage = state.get("current_stage", "Greeting")
    
    # Simple progression logic based on turn count
    # In a full system, this would use a fast LLM or strict heuristics to classify the user's intent.
    user_turns = len([m for m in messages if isinstance(m, HumanMessage)])
    
    if current_stage == "Greeting" and user_turns >= 1:
        state["current_stage"] = "Ice Breaking"
    elif current_stage == "Ice Breaking" and user_turns >= 2:
        state["current_stage"] = "Background Discovery"
    elif current_stage == "Background Discovery" and user_turns >= 4:
        state["current_stage"] = "Technical Discussion"
    elif current_stage == "Technical Discussion" and user_turns >= 8:
        state["current_stage"] = "Summary"
        
    # Update the system prompt with the new stage
    old_prompt = state.get("system_prompt", "")
    # Using a simple regex to update the stage in the prompt string
    new_prompt = re.sub(r'STAGE: The current conversation stage is \[.*?\]', 
                        f'STAGE: The current conversation stage is [{state["current_stage"]}]', 
                        old_prompt)
    
    state["system_prompt"] = new_prompt
    return state

async def call_llm(state: CallState):
    messages = state.get("messages", [])
    
    messages = TokenBudgetManager.enforce_budget(messages, state.get("system_prompt", ""))
    
    system_prompt = state.get("system_prompt")
    if not system_prompt:
        system = SystemMessage(content="You are a conversational AI.")
    else:
        system = SystemMessage(content=system_prompt)

    formatted = [system]
    
    for m in messages:
        if isinstance(m, dict):
            if m.get("role") == "user":
                formatted.append(HumanMessage(content=m.get("content", "")))
            elif m.get("role") == "ai":
                formatted.append(AIMessage(content=m.get("content", "")))
        else:
            formatted.append(m)

    response_text = ""
    sentence_buffer = ""
    cb = state.get("handle_sentence_callback")
    
    try:
        async for chunk in llm.astream(formatted):
            token = chunk.content
            response_text += token
            sentence_buffer += token
            
            # Simple sentence boundary detection
            if any(p in sentence_buffer for p in ['. ', '? ', '! ', '.\n', '?\n', '!\n']):
                if cb and sentence_buffer.strip():
                    await cb(sentence_buffer.strip())
                sentence_buffer = ""
                
        if sentence_buffer.strip():
            if cb:
                await cb(sentence_buffer.strip())
    except Exception as e:
        print(f"LLM Stream Error: {e}")
        response_text = "I missed that, could you repeat?"
        if cb:
            await cb(response_text)

    return {"messages": [AIMessage(content=response_text)]}

workflow = StateGraph(CallState)

workflow.add_node("planner", planner_node)
workflow.add_node("agent", call_llm)

workflow.set_entry_point("planner")
workflow.add_edge("planner", "agent")
workflow.add_edge("agent", END)

app_graph = workflow.compile()