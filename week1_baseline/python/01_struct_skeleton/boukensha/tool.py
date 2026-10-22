from dataclasses import dataclass
from typing import Callable


@dataclass
class Tool:
    name: str
    description: str
    parameters: dict
    block: Callable

    def __str__(self):
        description = "" if self.description is None else str(self.description)
        return (
            f"#<Tool name={self.name} description={description[:41]} "
            f"params={list(self.parameters.keys())}>"
        )
