from typing import Annotated, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

# Yeh class hamare AI Agent ka temporary database ya memory hai
class CallState(TypedDict):
    # LangGraph isme user aur AI ke messages append karta jayega
    messages: Annotated[list[BaseMessage], add_messages]
    
    # User ka initial prompt (e.g., "Act like an interviewer...")
    user_detailed_prompt: str
    
    # Woh exact transcript format jo aapko chahiye (AI: ... User: ...)
    formatted_transcript: str