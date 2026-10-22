from dataclasses import dataclass
from typing import Optional


@dataclass
class Message:
    role: str
    content: str
    tool_use_id: Optional[str] = None

    def __str__(self):
        id_tag = "" if self.tool_use_id is None else f" [{self.tool_use_id}]"
        content = "" if self.content is None else str(self.content)
        return f"#<Message role={self.role}{id_tag} content={content[:61]}...>"
