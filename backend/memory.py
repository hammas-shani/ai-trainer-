from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage

MAX_TOKEN_BUDGET = 4000 # Configurable limit

def estimate_tokens(text: str) -> int:
    """Very rough estimation of tokens"""
    return len(text.split()) * 1.3

class TokenBudgetManager:
    @staticmethod
    def enforce_budget(messages: list[BaseMessage], system_prompt: str) -> list[BaseMessage]:
        """
        Ensures the message list stays within the token budget.
        If it exceeds, older messages (excluding the first few context messages) are pruned.
        """
        budget = MAX_TOKEN_BUDGET - estimate_tokens(system_prompt)
        
        if budget < 500:
            budget = 500 # minimum safe budget
            
        current_tokens = sum(estimate_tokens(m.content) for m in messages)
        
        if current_tokens <= budget:
            return messages
            
        # We need to compress/prune
        # Keep the first 2 messages (usually intro) and start pruning from index 2
        # until current_tokens is under budget
        
        if len(messages) <= 4:
            return messages # too few to prune safely
            
        pruned_messages = [messages[0], messages[1]]
        
        # Calculate how many tokens we need to drop
        tokens_to_drop = current_tokens - budget
        dropped_tokens = 0
        
        start_idx = 2
        while start_idx < len(messages) - 2 and dropped_tokens < tokens_to_drop:
            dropped_tokens += estimate_tokens(messages[start_idx].content)
            start_idx += 1
            
        pruned_messages.extend(messages[start_idx:])
        return pruned_messages

class ContextRetrievalEngine:
    @staticmethod
    def build_context_prompt(user_facts: dict, stage: str) -> str:
        """
        Builds a context string from retrieved user facts and current conversation stage.
        """
        context = f"CURRENT STAGE: {stage}\n"
        if user_facts:
            context += "USER FACTS DISCOVERED SO FAR:\n"
            for k, v in user_facts.items():
                context += f"- {k}: {v}\n"
        
        return context
