from types import SimpleNamespace

import pytest

from src.ForumBot.SchemaValidation.redfish_uri_generator import (
    URIGenerationError,
    URIGenerator,
)


def test_parse_json_from_response_supports_markdown_fence():
    generator = URIGenerator(api_key="k", base_url="https://api.example.com", model="m")

    result = generator.parse_json_from_response("""
    ```json
    {"@odata.id": "/redfish/v1/Systems/1"}
    ```
    """)

    assert result == {"@odata.id": "/redfish/v1/Systems/1"}


def test_generate_returns_parsed_json(monkeypatch):
    generator = URIGenerator(api_key="k", base_url="https://api.example.com", model="m")

    class FakeLLM:
        def invoke(self, prompt):
            return SimpleNamespace(content='{"@odata.id": "/redfish/v1/Systems/1"}')

    monkeypatch.setattr(generator, "_create_llm", lambda: FakeLLM())

    result = generator.generate({"title": "rp", "content": "desc"})

    assert result == {"@odata.id": "/redfish/v1/Systems/1"}


def test_generate_raises_uri_generation_error_on_api_failure(monkeypatch):
    generator = URIGenerator(api_key="k", base_url="https://api.example.com", model="m")

    class FakeLLM:
        def invoke(self, prompt):
            raise RuntimeError("quota exceeded")

    monkeypatch.setattr(generator, "_create_llm", lambda: FakeLLM())

    with pytest.raises(URIGenerationError, match="API"):
        generator.generate({"title": "rp", "content": "desc"})


def test_parse_json_from_response_supports_embedded_object():
    generator = URIGenerator(api_key="k", base_url="https://api.example.com", model="m")

    result = generator.parse_json_from_response('prefix {"@odata.id": "/redfish/v1/Managers/1"} suffix')

    assert result == {"@odata.id": "/redfish/v1/Managers/1"}


def test_generate_returns_none_for_unparseable_response(monkeypatch):
    generator = URIGenerator(api_key="k", base_url="https://api.example.com", model="m")

    class FakeLLM:
        def invoke(self, prompt):
            return SimpleNamespace(content="not-json")

    monkeypatch.setattr(generator, "_create_llm", lambda: FakeLLM())

    assert generator.generate({"title": "rp", "content": "desc"}) is None


def test_generate_saves_output_file_when_requested(monkeypatch, tmp_path):
    generator = URIGenerator(api_key="k", base_url="https://api.example.com", model="m")
    saved = {}

    class FakeLLM:
        def invoke(self, prompt):
            return SimpleNamespace(content='{"@odata.id": "/redfish/v1/Systems/1"}')

    monkeypatch.setattr(generator, "_create_llm", lambda: FakeLLM())
    monkeypatch.setattr(
        "src.ForumBot.SchemaValidation.redfish_uri_generator.save_json",
        lambda data, output_file: saved.update({"data": data, "output_file": output_file}),
    )

    output_file = tmp_path / "sample.json"
    result = generator.generate({"title": "rp", "content": "desc"}, str(output_file))

    assert result == {"@odata.id": "/redfish/v1/Systems/1"}
    assert saved["output_file"] == str(output_file)


def test_build_prompt_includes_review_point_content():
    generator = URIGenerator(api_key="k", base_url="https://api.example.com", model="m")

    prompt = generator.build_prompt({"title": "Demo", "content": "Need a Redfish schema sample"})

    assert "Need a Redfish schema sample" in prompt


def test_create_llm_passes_expected_arguments(monkeypatch):
    captured = {}

    class FakeChatOpenAI:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setattr("src.ForumBot.SchemaValidation.redfish_uri_generator.ChatOpenAI", FakeChatOpenAI)
    generator = URIGenerator(api_key="k", base_url="https://api.example.com", model="m")

    llm = generator._create_llm()

    assert isinstance(llm, FakeChatOpenAI)
    assert captured["model"] == "m"
    assert captured["api_key"] == "k"
    assert captured["base_url"] == "https://api.example.com"
    assert captured["max_retries"] == 0


def test_generate_raises_uri_generation_error_with_structured_api_failure(monkeypatch):
    generator = URIGenerator(api_key="k", base_url="https://api.example.com", model="m")

    class FakeLLM:
        def invoke(self, prompt):
            raise RuntimeError('{"status":"429","msg":"quota","body":"x","error_code":"Limit"}')

    monkeypatch.setattr(generator, "_create_llm", lambda: FakeLLM())

    with pytest.raises(URIGenerationError):
        generator.generate({"title": "rp", "content": "desc"})
