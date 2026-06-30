from typing import Annotated, TypedDict, Optional
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

# Yeh class hamare AI Agent ka temporary database ya memory hai
class CallState(TypedDict):
    # LangGraph isme user aur AI ke messages append karta jayega
    messages: Annotated[list[BaseMessage], add_messages]
    
    # Session ID
    session_id: str

    # User ka initial prompt (e.g., "Act like an interviewer...") - deprecating in favor of system_prompt
    user_detailed_prompt: str
    
    # Dynamically generated system prompt
    system_prompt: str
    
    # Woh exact transcript format jo aapko chahiye (AI: ... User: ...)
    formatted_transcript: str
    
    # Current Conversation Stage
    current_stage: str
    
    # Discovered user facts
    user_facts: dict
    
    # Async Callback for streaming sentences
    handle_sentence_callback: Optional[object]
