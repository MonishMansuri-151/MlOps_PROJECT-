"""Test helpers: a scripted fake database and a fake Groq client."""
import json
import types
from contextlib import contextmanager


class ScriptedDB:
    """
    Replaces database.connection.get_db.

    `results` is consumed in order: every fetchone()/fetchall() call pops the
    next item. Every executed SQL statement is saved in `.queries`.
    """

    def __init__(self, results=None, lastrowid=55):
        self.results = list(results or [])
        self.queries = []
        self.lastrowid = lastrowid
        self.rowcount = 1
        self.committed = False
        self.rolled_back = False

    def __call__(self):
        db = self

        class Cursor:
            lastrowid = db.lastrowid
            rowcount = db.rowcount

            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

            def execute(self, sql, params=None):
                db.queries.append((" ".join(sql.split()), params))

            def fetchone(self):
                return db.results.pop(0) if db.results else None

            def fetchall(self):
                return db.results.pop(0) if db.results else []

        class Conn:
            def cursor(self):
                return Cursor()

        @contextmanager
        def ctx():
            yield Conn()

        return ctx()


# ---- fake Groq ---------------------------------------------------------

def text_reply(text):
    msg = types.SimpleNamespace(content=text, tool_calls=None)
    return types.SimpleNamespace(choices=[types.SimpleNamespace(message=msg)])


def tool_reply(call_id, name, args):
    call = types.SimpleNamespace(
        id=call_id,
        function=types.SimpleNamespace(name=name, arguments=json.dumps(args)),
    )
    msg = types.SimpleNamespace(content=None, tool_calls=[call])
    return types.SimpleNamespace(choices=[types.SimpleNamespace(message=msg)])


class FakeGroq:
    """`script` items: a response object, or an Exception to raise."""

    def __init__(self, script):
        self.script = list(script)
        self.calls = []
        outer = self

        class Completions:
            @staticmethod
            def create(**kwargs):
                outer.calls.append(kwargs)
                item = outer.script.pop(0)
                if isinstance(item, Exception):
                    raise item
                return item

        self.chat = types.SimpleNamespace(completions=Completions())
