from .message import Message


class Context:
    def __init__(self, *, task, system=None):
        self._task = task
        self._system = system
        self._messages = []
        self._tools = {}

    @property
    def task(self):
        return self._task

    @property
    def system(self):
        return self._system

    @property
    def messages(self):
        return self._messages

    @property
    def tools(self):
        return self._tools

    def register_tool(self, tool):
        self._tools[tool.name] = tool

    def add_message(self, role, content, *, tool_use_id=None):
        self._messages.append(Message(role, content, tool_use_id))

    @property
    def tool_count(self):
        return len(self._tools)

    @property
    def turn_count(self):
        return len(self._messages)

    def __str__(self):
        task_name = self._task.task_name if self._task is not None else ""
        return f"#<Context task={task_name} turns={self.turn_count} tools={self.tool_count}>"

    __repr__ = __str__
