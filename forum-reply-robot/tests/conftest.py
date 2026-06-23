import importlib.abc
import importlib.machinery
import importlib.util
import os
import sys
import types


ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCHEMA_DIR = os.path.join(ROOT_DIR, "src", "ForumBot", "SchemaValidation")
MDB_DIR = os.path.join(ROOT_DIR, "src", "ForumBot", "MdbValidation")

for path in (ROOT_DIR, SCHEMA_DIR, MDB_DIR):
    if path not in sys.path:
        sys.path.insert(0, path)


if "psycopg2" not in sys.modules:
    psycopg2_module = types.ModuleType("psycopg2")
    psycopg2_module.connect = lambda **kwargs: None
    sys.modules["psycopg2"] = psycopg2_module
    
    psycopg2_pool_module = types.ModuleType("psycopg2.pool")
    
    class DummyThreadedConnectionPool:
        def __init__(self, minconn, maxconn, **kwargs):
            self.minconn = minconn
            self.maxconn = maxconn
            self.kwargs = kwargs
        
        def getconn(self):
            return None
        
        def putconn(self, conn):
            pass
        
        def closeall(self):
            pass
    
    class DummyOperationalError(Exception):
        pass
    
    class DummyError(Exception):
        pass
    
    psycopg2_module.OperationalError = DummyOperationalError
    psycopg2_module.Error = DummyError
    
    psycopg2_pool_module.ThreadedConnectionPool = DummyThreadedConnectionPool
    psycopg2_module.pool = psycopg2_pool_module
    sys.modules["psycopg2.pool"] = psycopg2_pool_module
    
    psycopg2_extras_module = types.ModuleType("psycopg2.extras")
    psycopg2_extras_module.register_default_jsonb = lambda globally=True: None

    def _json_adapter(obj):
        import json
        return json.dumps(obj)
    psycopg2_extras_module.Json = _json_adapter

    psycopg2_module.extras = psycopg2_extras_module
    sys.modules["psycopg2.extras"] = psycopg2_extras_module

    psycopg2_extensions_module = types.ModuleType("psycopg2.extensions")
    psycopg2_extensions_module.register_adapter = lambda cls, adapter: None
    psycopg2_module.extensions = psycopg2_extensions_module
    sys.modules["psycopg2.extensions"] = psycopg2_extensions_module


if "markdownify" not in sys.modules:
    markdownify_module = types.ModuleType("markdownify")

    def markdownify(html, *args, **kwargs):
        from bs4 import BeautifulSoup, NavigableString

        soup = BeautifulSoup(str(html), "html.parser")
        for br in soup.find_all("br"):
            br.replace_with(NavigableString("\n"))
        for strong in soup.find_all(["strong", "b"]):
            strong.replace_with(NavigableString(f"**{strong.get_text(strip=True)}**"))
        for level in range(6, 0, -1):
            for heading in soup.find_all(f"h{level}"):
                heading.replace_with(NavigableString(f"\n\n{'#' * level} {heading.get_text(strip=True)}\n\n"))
        for paragraph in soup.find_all("p"):
            paragraph.replace_with(NavigableString(f"\n{paragraph.get_text()}\n"))
        return soup.get_text()

    markdownify_module.markdownify = markdownify
    sys.modules["markdownify"] = markdownify_module


if "openai" not in sys.modules:
    openai_module = types.ModuleType("openai")

    class DummyOpenAI:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs
            self.chat = types.SimpleNamespace(
                completions=types.SimpleNamespace(
                    create=lambda *a, **k: (_ for _ in ()).throw(
                        RuntimeError("OpenAI.chat.completions.create should be mocked in tests")
                    )
                )
            )

    class DummyOpenAIError(Exception):
        pass

    openai_module.OpenAI = DummyOpenAI
    openai_module.APIError = DummyOpenAIError
    openai_module.APITimeoutError = DummyOpenAIError
    openai_module.InternalServerError = DummyOpenAIError
    sys.modules["openai"] = openai_module


if "langchain_openai" not in sys.modules:
    langchain_module = types.ModuleType("langchain_openai")

    class DummyChatOpenAI:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

        def invoke(self, prompt):
            raise RuntimeError("ChatOpenAI.invoke should be mocked in tests")

    langchain_module.ChatOpenAI = DummyChatOpenAI
    sys.modules["langchain_openai"] = langchain_module


if "langchain_core" not in sys.modules:
    langchain_core_module = types.ModuleType("langchain_core")
    prompts_module = types.ModuleType("langchain_core.prompts")
    output_parsers_module = types.ModuleType("langchain_core.output_parsers")
    messages_module = types.ModuleType("langchain_core.messages")

    class _DummyRunnable:
        def __init__(self, invoke_fn):
            self._invoke_fn = invoke_fn

        def invoke(self, input_value):
            return self._invoke_fn(input_value)

        def __or__(self, other):
            if hasattr(other, "invoke"):
                return _DummyRunnable(lambda x: other.invoke(self.invoke(x)))
            if callable(other):
                return _DummyRunnable(lambda x: other(self.invoke(x)))
            return _DummyRunnable(lambda x: self.invoke(x))

    class DummyChatPromptTemplate:
        def __init__(self, messages):
            self.messages = messages

        @classmethod
        def from_messages(cls, messages):
            return cls(messages)

        def invoke(self, input_value):
            return input_value

        def __or__(self, other):
            if hasattr(other, "invoke"):
                return _DummyRunnable(lambda x: other.invoke(self.invoke(x)))
            if callable(other):
                return _DummyRunnable(lambda x: other(self.invoke(x)))
            return _DummyRunnable(lambda x: self.invoke(x))

    class DummyStrOutputParser:
        def invoke(self, value):
            if hasattr(value, "content"):
                return value.content
            return value

    class DummySystemMessage:
        def __init__(self, content):
            self.content = content

    class DummyHumanMessage:
        def __init__(self, content):
            self.content = content

    prompts_module.ChatPromptTemplate = DummyChatPromptTemplate
    output_parsers_module.StrOutputParser = DummyStrOutputParser
    messages_module.SystemMessage = DummySystemMessage
    messages_module.HumanMessage = DummyHumanMessage

    langchain_core_module.prompts = prompts_module
    langchain_core_module.output_parsers = output_parsers_module
    langchain_core_module.messages = messages_module

    sys.modules["langchain_core"] = langchain_core_module
    sys.modules["langchain_core.prompts"] = prompts_module
    sys.modules["langchain_core.output_parsers"] = output_parsers_module
    sys.modules["langchain_core.messages"] = messages_module





if "git" not in sys.modules:
    git_module = types.ModuleType("git")

    class DummyRepo:
        def __init__(self, *args, **kwargs):
            self.remotes = types.SimpleNamespace(origin=types.SimpleNamespace(pull=lambda *a, **k: None))

        @staticmethod
        def clone_from(*args, **kwargs):
            return None

    class DummyGitCommandError(Exception):
        pass

    git_module.Repo = DummyRepo
    git_module.exc = types.SimpleNamespace(GitCommandError=DummyGitCommandError)
    sys.modules["git"] = git_module


class _ExtractReviewsLoader(importlib.abc.Loader):
    def create_module(self, spec):
        return None

    def exec_module(self, module):
        def extract_review_points_from_html(content):
            return []

        def extract_all_review_points(content):
            return []

        def is_redfish_related(title, content):
            return False

        module.extract_review_points_from_html = extract_review_points_from_html
        module.extract_all_review_points = extract_all_review_points
        module.is_redfish_related = is_redfish_related


_ORIGINAL_SPEC_FROM_FILE_LOCATION = importlib.util.spec_from_file_location


def _patched_spec_from_file_location(name, location, *args, **kwargs):
    if name == "extract_reviews" and location and not os.path.exists(location):
        return importlib.machinery.ModuleSpec(
            name=name,
            loader=_ExtractReviewsLoader(),
            origin="synthetic://extract_reviews",
        )
    return _ORIGINAL_SPEC_FROM_FILE_LOCATION(name, location, *args, **kwargs)


importlib.util.spec_from_file_location = _patched_spec_from_file_location
