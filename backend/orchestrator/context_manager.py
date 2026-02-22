from typing import List, Dict
from collections import defaultdict
import uuid

# In-memory store -- replace with Redis for production
_conversations: dict = defaultdict(list)


def get_history(conversation_id: str) -> List[Dict]:
    return _conversations.get(conversation_id, [])


def add_turn(conversation_id: str, role: str, content: str):
    _conversations[conversation_id].append({"role": role, "content": content})
    # Keep last 10 turns to manage context window
    if len(_conversations[conversation_id]) > 20:
        _conversations[conversation_id] = _conversations[conversation_id][-20:]


def new_conversation_id() -> str:
    return str(uuid.uuid4())
