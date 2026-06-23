import json
from pathlib import Path

import pytest

from src.ForumBot.SchemaValidation.redfish_schema_validator import (
    JSONSchemaValidator,
    _generate_advice_from_error,
    validate_static_schema,
)


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def write_schema(tmp_path):
    schema = {
        "properties": {
            "@odata.type": {"type": "string"},
            "Name": {"type": "string"},
        },
        "required": ["@odata.type", "Name"],
    }
    schema_file = tmp_path / "Service.json"
    schema_file.write_text(json.dumps(schema), encoding="utf-8")
    return schema_file


def test_validate_static_schema_pass(tmp_path):
    write_schema(tmp_path)
    payload = {
        "@odata.type": "#Service.v1_0_0.Service",
        "@odata.id": "/redfish/v1/Service",
        "Name": "Test Service",
    }

    result = validate_static_schema(payload, str(tmp_path))

    assert result["result"] == "pass"
    assert result["failed_checks_num"] == 0
    assert result["error_details"]["STATIC_VALIDATION"] == []


def test_validate_static_schema_missing_required_property(tmp_path):
    write_schema(tmp_path)
    payload = {
        "@odata.type": "#Service.v1_0_0.Service",
        "@odata.id": "/redfish/v1/Service",
    }

    result = validate_static_schema(payload, str(tmp_path))

    assert result["result"] == "fail"
    assert result["failed_checks_num"] >= 1
    assert result["error_details"]["STATIC_VALIDATION"]


def test_validator_supports_nested_object_array_and_nullable_types(tmp_path):
    schema = {
        "properties": {
            "@odata.type": {"type": "string"},
            "Name": {"type": "string"},
            "Metrics": {
                "type": "object",
                "properties": {
                    "Count": {"type": "integer"},
                    "OptionalValue": {"type": ["string", "null"]},
                },
                "required": ["Count"],
            },
            "Ids": {"type": "array", "items": {"type": "integer"}},
        },
        "required": ["@odata.type", "Name", "Metrics", "Ids"],
    }
    (tmp_path / "Service.json").write_text(json.dumps(schema), encoding="utf-8")
    validator = JSONSchemaValidator(str(tmp_path))

    result = validator.validate(
        "/redfish/v1/Service",
        {
            "@odata.type": "#Service.v1_0_0.Service",
            "@odata.id": "/redfish/v1/Service",
            "Name": "svc",
            "Metrics": {"Count": 2, "OptionalValue": None},
            "Ids": [1, 2],
        },
    )

    assert result.result == "pass"
    assert validator.pass_count >= 5
    assert validator.fail_count == 0


def test_validator_records_unknown_property_and_skips_oem(tmp_path):
    schema = {
        "properties": {
            "@odata.type": {"type": "string"},
            "Name": {"type": "string"},
        },
        "required": ["@odata.type", "Name"],
    }
    (tmp_path / "Service.json").write_text(json.dumps(schema), encoding="utf-8")
    validator = JSONSchemaValidator(str(tmp_path), no_oem=True)

    result = validator.validate(
        "/redfish/v1/Service",
        {
            "@odata.type": "#Service.v1_0_0.Service",
            "@odata.id": "/redfish/v1/Service",
            "Name": "svc",
            "UnknownField": 1,
            "Oem": {"Vendor": "x"},
        },
    )

    assert result.result == "pass"
    assert validator.warn_count == 1
    assert validator.skip_count == 1
    assert validator.warnings == []


def test_validator_handles_missing_odata_type_and_non_dict_payload(tmp_path):
    (tmp_path / "Service.json").write_text(json.dumps({"properties": {}}), encoding="utf-8")
    validator = JSONSchemaValidator(str(tmp_path))

    bad_payload_result = validator.validate("/redfish/v1/Service", [])
    missing_type_result = validator.validate("/redfish/v1/Service", {"Name": "svc"})

    assert bad_payload_result.result == "error"
    assert missing_type_result.result == "error"
    assert missing_type_result.errors[0]["type"] == "Required Property Error"


def test_validator_resolves_local_and_external_refs_and_anyof(tmp_path):
    other_schema = {
        "definitions": {"Common": {"type": "string"}}
    }
    service_schema = {
        "$ref": "#/definitions/Root",
        "definitions": {
            "Root": {
                "anyOf": [
                    {
                        "properties": {
                            "@odata.type": {"type": "string"},
                            "Name": {"$ref": "Other.json#/Common"},
                        },
                        "required": ["@odata.type", "Name"],
                    }
                ]
            }
        },
    }
    (tmp_path / "Other.json").write_text(json.dumps(other_schema), encoding="utf-8")
    (tmp_path / "Service.json").write_text(json.dumps(service_schema), encoding="utf-8")
    validator = JSONSchemaValidator(str(tmp_path))

    result = validator.validate(
        "/redfish/v1/Service",
        {"@odata.type": "#Service.v1_0_0.Service", "Name": "svc"},
    )

    assert result.result == "pass"
    assert validator._resolve_ref("#/definitions/Root") is not None
    assert validator._resolve_ref("Other.json#/Common") == {"type": "string"}


def test_validate_static_schema_can_save_result_and_generate_advice(tmp_path):
    write_schema(tmp_path)
    output_file = tmp_path / "result.json"
    payload = {
        "@odata.type": "#Service.v1_0_0.Service",
        "@odata.id": "/redfish/v1/Service",
    }

    result = validate_static_schema(payload, str(tmp_path), save_result=True, output_file=str(output_file))

    assert result["result"] == "fail"
    assert output_file.exists()
    assert result["advice_details"]["STATIC_VALIDATION"]


def test_generate_advice_from_error_variants():
    assert "Count" in _generate_advice_from_error(
        {
            "type": "Property Type Error",
            "message": "Property Type Error: Property 'Count' is expected to be a integer, but found 'str'.",
            "property": "Count",
        }
    )
    assert _generate_advice_from_error({"type": "Schema Error", "message": "bad schema"})


def test_schema_directory_helpers_and_bundle_iteration(tmp_path):
    write_json(tmp_path / "dmtf" / "Service.v1_0_0.json", {"properties": {"Name": {"type": "string"}}})
    write_json(tmp_path / "dmtf" / "info.json", {"ignored": True})
    write_json(tmp_path / "rackmount" / "jsonschemas" / "Collection.json", {"definitions": {"X": {}}})
    write_json(tmp_path / "rackmount" / "oem" / "openubmc" / "HwService.json", {"properties": {"Mode": {"type": "string"}}})
    write_json(
        tmp_path / "rackmount" / "oem" / "openubmc" / "json_schema" / "OemService.json",
        {"properties": {"Vendor": {"type": "string"}}},
    )

    validator = JSONSchemaValidator(str(tmp_path))

    assert validator._dmtf_stem_index["service.v1_0_0"] == "Service.v1_0_0"
    assert validator._oem_stem_paths["hwservice"].name == "HwService.json"
    assert validator._oem_stem_paths["oemservice"].name == "OemService.json"
    assert [path.name for path in validator._schema_bundle_dirs()] == [
        "dmtf",
        "jsonschemas",
        "openubmc",
        "json_schema",
    ]
    assert sorted(path.name for path in validator._iter_schema_json_files()) == [
        "Collection.json",
        "HwService.json",
        "OemService.json",
        "Service.v1_0_0.json",
    ]


def test_schema_resolution_helpers_cover_legacy_and_classification(tmp_path):
    service_schema = {"properties": {"Name": {"type": "string"}}, "required": ["Name"]}
    write_json(tmp_path / "Service.json", service_schema)
    validator = JSONSchemaValidator(str(tmp_path))

    assert JSONSchemaValidator._build_schema_candidates("Service.v1_0_0", "Service") == [
        "Service.v1_0_0",
        "Service",
        "HwService.v1_0_0",
        "HwService",
    ]
    assert validator._read_schema_file(tmp_path, "Service") == service_schema
    assert validator._resolve_primary_schema("Service.v1_0_0", "Service")[1:3] == ("Service", "legacy")
    assert validator._find_schema_path_by_basename("Service.json") == tmp_path / "Service.json"
    assert validator._path_relative_to_schema_root(tmp_path / "Service.json") == "Service.json"
    assert validator._classify_schema_location(tmp_path / "Service.json")[0] == "other"
    assert validator._classify_schema_location(Path("C:/outside/Service.json"))[0] == "outside_schema_root"


def test_read_schema_file_returns_none_for_invalid_json(tmp_path):
    schema_dir = tmp_path / "dmtf"
    schema_dir.mkdir(parents=True)
    (schema_dir / "Broken.json").write_text("{not-json", encoding="utf-8")
    validator = JSONSchemaValidator(str(tmp_path))

    assert validator._read_schema_file(schema_dir, "Broken") is None


@pytest.mark.parametrize(
    ("target_name", "target_data", "schema_value", "expected_origin", "expected_name"),
    [
        (
            "PerformanceCollection.json",
            {"definitions": {"PerformanceCollection": {"properties": {"Name": {"type": "string"}}}}},
            "#PerformanceCollection.v1_0_0.PerformanceCollection",
            "local",
            "PerformanceCollection.json",
        ),
        (
            "RootOnly.json",
            {"properties": {"Name": {"type": "string"}}},
            "#RootOnly.v1_0_0.RootOnly",
            "local",
            "RootOnly.json",
        ),
        (
            "SingleDefinition.json",
            {"definitions": {"Only": {"properties": {"Name": {"type": "string"}}}}},
            "#Any.v1_0_0.Entity",
            "local",
            "SingleDefinition.json",
        ),
    ],
)
def test_resolve_json_schema_file_pointer_local_variants(
    tmp_path, target_name, target_data, schema_value, expected_origin, expected_name
):
    write_json(tmp_path / target_name, target_data)
    write_json(tmp_path / "Source.json", {"Location": [{"Uri": target_name}], "Schema": schema_value})
    validator = JSONSchemaValidator(str(tmp_path))

    resolved, path, origin, remote_name = validator._resolve_json_schema_file_pointer(
        {"Location": [{"Uri": target_name}], "Schema": schema_value},
        "Source",
    )

    assert resolved is not None
    assert path.name == expected_name
    assert origin == expected_origin
    assert remote_name == ""


def test_resolve_json_schema_file_pointer_remote_and_unresolved_paths(tmp_path, monkeypatch):
    validator = JSONSchemaValidator(str(tmp_path))
    remote_calls = []

    def fake_fetch(name):
        remote_calls.append(name)
        if name == "Remote.json":
            return {"definitions": {"RemoteEntity": {"properties": {"Name": {"type": "string"}}}}}
        return None

    monkeypatch.setattr(validator, "_fetch_remote_schema", fake_fetch)

    resolved, path, origin, remote_name = validator._resolve_json_schema_file_pointer(
        {
            "Location": [{"Uri": "Remote.json"}],
            "Schema": "#RemoteEntity.v1_0_0.RemoteEntity",
        },
        "Source",
    )
    unresolved = validator._resolve_json_schema_file_pointer(
        {
            "Location": [{"Uri": "Missing.json"}],
            "Schema": "#Missing.v1_0_0.Missing",
        },
        "Source",
    )

    assert resolved["properties"]["Name"]["type"] == "string"
    assert path is None
    assert origin == "remote"
    assert remote_name == "Remote.json"
    assert unresolved == (None, None, "", "")
    assert remote_calls == ["Remote.json", "Missing.json"]


def test_pointer_helper_methods_and_pointer_detection(tmp_path):
    write_json(tmp_path / "dmtf" / "Service.v1_0_0.json", {"properties": {"Name": {"type": "string"}}})
    write_json(
        tmp_path / "rackmount" / "jsonschemas" / "Collection.json",
        {"definitions": {"Collection": {"properties": {"Members": {"type": "array"}}}}},
    )
    write_json(
        tmp_path / "rackmount" / "oem" / "openubmc" / "json_schema" / "OemThing.json",
        {"properties": {"Vendor": {"type": "string"}}},
    )
    validator = JSONSchemaValidator(str(tmp_path))

    assert validator._schema_field_to_entity_name("#PerformanceCollection.v1_0_0.PerformanceCollection") == "PerformanceCollection"
    assert validator._schema_field_to_entity_name("") == ""
    assert validator._is_json_schema_file_pointer({"@odata.type": "#JsonSchemaFile.v1_0_0.JsonSchemaFile"}) is True
    assert validator._is_json_schema_file_pointer({"Location": [{"Uri": "a.json"}], "Schema": "#Thing.v1_0_0.Thing"}) is True
    assert validator._is_json_schema_file_pointer({"properties": {"Name": {"type": "string"}}}) is False
    assert validator._classify_schema_location(tmp_path / "dmtf" / "Service.v1_0_0.json")[0] == "dmtf_official"
    assert validator._classify_schema_location(tmp_path / "rackmount" / "jsonschemas" / "Collection.json")[0] == "rackmount_jsonschemas"
    assert validator._classify_schema_location(tmp_path / "rackmount" / "oem" / "openubmc" / "json_schema" / "OemThing.json")[0] == "oem_openubmc"


def test_validate_merges_dmtf_and_oem_schema_and_records_meta(tmp_path):
    write_json(
        tmp_path / "dmtf" / "Service.v1_0_0.json",
        {
            "properties": {
                "@odata.type": {"type": "string"},
                "Name": {"type": "string"},
            },
            "required": ["@odata.type", "Name"],
        },
    )
    write_json(
        tmp_path / "rackmount" / "oem" / "openubmc" / "json_schema" / "HwService.json",
        {
            "properties": {
                "VendorField": {"type": "string"},
            },
            "required": ["VendorField"],
        },
    )
    validator = JSONSchemaValidator(str(tmp_path))

    result = validator.validate(
        "/redfish/v1/Service",
        {
            "@odata.type": "#Service.v1_0_0.Service",
            "Name": "svc",
            "VendorField": "vendor",
        },
    )

    assert result.result == "pass"
    assert validator.schema_check_meta["dmtf_schema_found"] is True
    assert validator.schema_check_meta["oem_schema_found"] is True
    assert validator.schema_check_meta["validated_sources"] == ["dmtf", "oem"]


def test_validate_skips_when_bundle_dirs_exist_but_no_schema_matches(tmp_path):
    (tmp_path / "dmtf").mkdir(parents=True)
    (tmp_path / "rackmount" / "oem" / "openubmc" / "json_schema").mkdir(parents=True)
    validator = JSONSchemaValidator(str(tmp_path))

    result = validator.validate(
        "/redfish/v1/Service",
        {"@odata.type": "#Service.v1_0_0.Service", "Name": "svc"},
    )

    assert result.result == "skip"
    assert result.warnings[0]["type"] == "Schema Not Found"


def test_validate_skips_when_json_schema_file_pointer_cannot_resolve_target(tmp_path):
    write_json(
        tmp_path / "dmtf" / "Service.v1_0_0.json",
        {
            "@odata.type": "#JsonSchemaFile.v1_0_0.JsonSchemaFile",
            "Schema": "#Service.v1_0_0.Service",
            "Location": [{"Uri": "MissingDefinition.json"}],
        },
    )
    validator = JSONSchemaValidator(str(tmp_path))

    result = validator.validate(
        "/redfish/v1/Service",
        {"@odata.type": "#Service.v1_0_0.Service", "Name": "svc"},
    )

    assert result.result == "skip"
    assert any(warning["type"].endswith("Schema Skip") for warning in result.warnings)


def test_validate_records_unresolved_ref_and_null_errors(tmp_path):
    write_json(
        tmp_path / "Service.json",
        {
            "properties": {
                "@odata.type": {"type": "string"},
                "Name": {"$ref": "#/definitions/Missing"},
                "Enabled": {"type": "boolean"},
            },
            "required": ["@odata.type", "Name", "Enabled"],
        },
    )
    validator = JSONSchemaValidator(str(tmp_path))

    result = validator.validate(
        "/redfish/v1/Service",
        {
            "@odata.type": "#Service.v1_0_0.Service",
            "Name": "svc",
            "Enabled": None,
        },
    )

    assert result.result == "fail"
    assert {error["type"] for error in validator.errors} == {"Schema Error", "Null Error"}
