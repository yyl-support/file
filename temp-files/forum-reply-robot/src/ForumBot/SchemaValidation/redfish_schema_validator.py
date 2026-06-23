#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Redfish Schema 验证器模块

提供 JSON Schema 验证功能，包括：
- Schema 文件加载
- 属性类型验证
- 引用解析
- 错误记录
"""

# version：1.0.30

import json
import logging
import re
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from redfish_common import ValidationResult, SchemaValidationError, save_json


logger = logging.getLogger(__name__)

GITCODE_SCHEMA_BASE_URL = (
    "https://raw.gitcode.com/openUBMC/rackmount/raw/main/"
    "interface_config/redfish/static_resource/redfish/v1/"
    "schemastore/en/oem/openubmc/json_schema/"
)

# SchemaFiles 根下子目录：
# - dmtf: redfish.dmtf.org 官方 JSON Schema
# - rackmount/jsonschemas: rackmount 仓库 jsonschemas 目录下的 JsonSchemaFile 指针等（非 DMTF 标记）
# - rackmount/oem/openubmc[/json_schema]: OEM；与线上一致时文件在 json_schema/ 子目录
SCHEMA_SUBDIR_DMTF = "dmtf"
SCHEMA_SUBDIR_RACKMOUNT_JSONSCHEMAS = Path("rackmount") / "jsonschemas"
SCHEMA_SUBDIR_OEM_OPENUBMC = Path("rackmount") / "oem" / "openubmc"
SCHEMA_SUBDIR_OEM_OPENUBMC_JSON_SCHEMA = (
    Path("rackmount") / "oem" / "openubmc" / "json_schema"
)


class JSONSchemaValidator:
    """JSON Schema 验证器用于 Redfish 资源"""

    def __init__(self, schema_directory: str, no_oem: bool = False):
        """
        初始化验证器

        Args:
            schema_directory: Schema 文件目录
            no_oem: 是否跳过 OEM 检查
        """
        self._schema_directory = Path(schema_directory)
        self._dmtf_dir = self._schema_directory / SCHEMA_SUBDIR_DMTF
        self._rackmount_jsonschemas_dir = (
            self._schema_directory / SCHEMA_SUBDIR_RACKMOUNT_JSONSCHEMAS
        )
        self._oem_openubmc_dir = self._schema_directory / SCHEMA_SUBDIR_OEM_OPENUBMC
        self._oem_json_schema_dir = (
            self._schema_directory / SCHEMA_SUBDIR_OEM_OPENUBMC_JSON_SCHEMA
        )
        self._no_oem = no_oem
        self._pass_count = 0
        self._warn_count = 0
        self._fail_count = 0
        self._skip_count = 0
        self._errors = []
        self._warnings = []
        self._schemas = {}
        self._definitions = {}
        self._dmtf_stem_index: Dict[str, str] = {}
        self._oem_stem_paths: Dict[str, Path] = {}
        # 最近一次 validate() 的 schema 来源说明（写入 test_log / schema_validation）
        self.schema_check_meta: Dict[str, Any] = {}
        self._load_schemas()

    @staticmethod
    def _index_schema_stems(directory: Path) -> Dict[str, str]:
        """小写 stem -> 目录中实际文件名 stem（同名校验时取排序第一个）。"""
        out: Dict[str, str] = {}
        if not directory.is_dir():
            return out
        for p in sorted(directory.glob("*.json")):
            if p.name == "info.json":
                continue
            k = p.stem.lower()
            if k not in out:
                out[k] = p.stem
        return out

    @staticmethod
    def _index_schema_paths(directory: Path) -> Dict[str, Path]:
        """小写 stem -> 该目录下的 schema 文件路径（同名取排序最后一个，便于后写覆盖）。"""
        out: Dict[str, Path] = {}
        if not directory.is_dir():
            return out
        for p in sorted(directory.glob("*.json")):
            if p.name == "info.json":
                continue
            out[p.stem.lower()] = p
        return out

    def _schema_bundle_dirs(self) -> List[Path]:
        """
        已配置的 schema 子目录。
        加载顺序：DMTF → rackmount/jsonschemas → openubmc 根 → openubmc/json_schema（同名后者覆盖）。
        """
        dirs: List[Path] = []
        if self._dmtf_dir.is_dir():
            dirs.append(self._dmtf_dir)
        if self._rackmount_jsonschemas_dir.is_dir():
            dirs.append(self._rackmount_jsonschemas_dir)
        oem = self._oem_openubmc_dir
        if oem.is_dir():
            dirs.append(oem)
        if self._oem_json_schema_dir.is_dir():
            dirs.append(self._oem_json_schema_dir)
        return dirs

    def _iter_schema_json_files(self) -> List[Path]:
        """
        列出待加载的 schema 文件。
        若存在 dmtf/、rackmount/jsonschemas/、rackmount/oem/openubmc[/json_schema]/ 中任一目录则仅从上述加载；
        否则回退为 SchemaFiles 根目录下扁平 *.json（兼容旧布局）。
        """
        bundles = self._schema_bundle_dirs()
        files: List[Path] = []
        if bundles:
            for d in bundles:
                files.extend(
                    p
                    for p in sorted(d.glob("*.json"))
                    if p.name != "info.json"
                )
            return files
        root = self._schema_directory
        return [
            p
            for p in sorted(root.glob("*.json"))
            if p.name != "info.json"
        ]

    def _load_schemas(self) -> None:
        """加载所有 JSON schema 文件"""
        self._dmtf_stem_index = self._index_schema_stems(self._dmtf_dir)
        self._oem_stem_paths = self._index_schema_paths(self._oem_openubmc_dir)
        self._oem_stem_paths.update(self._index_schema_paths(self._oem_json_schema_dir))
        for schema_file in self._iter_schema_json_files():
            try:
                with open(schema_file, 'r', encoding='utf-8') as f:
                    schema_data = json.load(f)
                    self._schemas[schema_file.stem] = schema_data
                    if "definitions" in schema_data:
                        self._definitions.update(schema_data["definitions"])
            except Exception as e:
                logger.warning(f"Failed to load schema file {schema_file}: {e}")

    def _read_schema_file(self, directory: Path, stem: str) -> Optional[Dict[str, Any]]:
        path = directory / f"{stem}.json"
        if not path.is_file():
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to read schema {path}: {e}")
            return None

    # ------------------------------------------------------------------
    # 按来源分别查找 schema
    # ------------------------------------------------------------------

    @staticmethod
    def _build_schema_candidates(full_type: str, base_type: str) -> List[str]:
        """构建 schema 候选名列表，包含 Hw 前缀变体作为回退。

        优先级：原名(带版本) → 原名(不带版本) → Hw前缀(带版本) → Hw前缀(不带版本)
        例如 NtpService.v1_0_0 / NtpService → HwNtpService.v1_0_0 / HwNtpService
        """
        candidates: List[str] = []
        if full_type != base_type:
            candidates.append(full_type)
        candidates.append(base_type)

        hw_extras: List[str] = []
        for cand in candidates:
            if not cand.lower().startswith("hw"):
                hw_extras.append(f"Hw{cand}")
        candidates.extend(hw_extras)
        return candidates

    def _resolve_schema_from_dmtf(
        self, full_type: str, base_type: str
    ) -> tuple[Optional[Dict[str, Any]], Optional[str], Optional[str], Optional[Path]]:
        """尝试从 dmtf/ 目录查找 schema。"""
        candidates = self._build_schema_candidates(full_type, base_type)

        if self._dmtf_stem_index:
            for cand in candidates:
                stem = self._dmtf_stem_index.get(cand.lower())
                if not stem:
                    continue
                data = self._read_schema_file(self._dmtf_dir, stem)
                if data is not None:
                    return data, stem, "dmtf", self._dmtf_dir / f"{stem}.json"
        return None, None, None, None

    def _resolve_schema_from_oem(
        self, full_type: str, base_type: str
    ) -> tuple[Optional[Dict[str, Any]], Optional[str], Optional[str], Optional[Path]]:
        """尝试从 oem/openubmc[/json_schema]/ 目录查找 schema。"""
        candidates = self._build_schema_candidates(full_type, base_type)

        if self._oem_stem_paths:
            for cand in candidates:
                path = self._oem_stem_paths.get(cand.lower())
                if path is None or not path.is_file():
                    continue
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    return data, path.stem, "oem", path
                except Exception as e:
                    logger.warning(f"Failed to read OEM schema {path}: {e}")
        return None, None, None, None

    def _resolve_schema_legacy(
        self, full_type: str, base_type: str
    ) -> tuple[Optional[Dict[str, Any]], Optional[str], Optional[str], Optional[Path]]:
        """回退到 SchemaFiles 根目录下扁平布局查找（仅当无 bundle 子目录时）。"""
        if self._schema_bundle_dirs():
            return None, None, None, None
        candidates = self._build_schema_candidates(full_type, base_type)
        for cand in candidates:
            for sn, sd in self._schemas.items():
                if sn.lower() == cand.lower():
                    leg = self._schema_directory / f"{sn}.json"
                    return sd, sn, "legacy", leg if leg.is_file() else None
        return None, None, None, None

    def _resolve_primary_schema(
        self, full_type: str, base_type: str
    ) -> tuple[Optional[Dict[str, Any]], Optional[str], Optional[str], Optional[Path]]:
        """向后兼容：按 dmtf → oem → legacy 优先级返回单个 schema。"""
        result = self._resolve_schema_from_dmtf(full_type, base_type)
        if result[0] is not None:
            return result
        result = self._resolve_schema_from_oem(full_type, base_type)
        if result[0] is not None:
            return result
        return self._resolve_schema_legacy(full_type, base_type)

    # ------------------------------------------------------------------
    # 将原始 schema 解析到可校验的 properties 层级
    # ------------------------------------------------------------------

    def _resolve_to_properties(
        self,
        schema: Dict[str, Any],
        schema_filename: str,
        primary_source: str,
        entry_path: Optional[Path],
    ) -> tuple[Optional[Dict[str, Any]], Dict[str, Any], Optional[str]]:
        """
        处理 JsonSchemaFile 指针 / $ref / anyOf，返回包含 properties 的 schema。

        Returns:
            (resolved_schema, meta, skip_reason)
            - resolved_schema: 含 properties/required 的字典；解析失败时为 None
            - meta: 来源元信息
            - skip_reason: 跳过原因（None 表示成功）
        """
        entry_cat, entry_zh = self._classify_schema_location(entry_path)
        entry_rel = self._path_relative_to_schema_root(entry_path)
        meta: Dict[str, Any] = {
            "entry_resolution": primary_source,
            "entry_schema_stem": schema_filename,
            "entry_schema_path_relative": entry_rel,
            "entry_schema_category": entry_cat,
            "entry_schema_category_label_zh": entry_zh,
        }

        # -- JsonSchemaFile（指向性文件）--
        if self._is_json_schema_file_pointer(schema):
            resolved_schema, def_path, def_origin, remote_basename = (
                self._resolve_json_schema_file_pointer(schema, schema_filename or "")
            )
            if resolved_schema is not None:
                schema = resolved_schema
                if def_origin == "local" and def_path is not None:
                    dc, dzh = self._classify_schema_location(def_path)
                    def_rel = self._path_relative_to_schema_root(def_path)
                    meta["definition_schema_path_relative"] = def_rel
                    meta["definition_schema_category"] = dc
                    meta["definition_schema_category_label_zh"] = dzh
                    meta["validation_summary_zh"] = (
                        f"入口 JsonSchemaFile：{entry_zh}"
                        f"（{entry_rel or schema_filename + '.json'}）；"
                        f"实际用于属性校验的定义来自：{dzh}（{def_rel}）"
                    )
                elif def_origin == "remote":
                    meta["definition_resolved_via"] = "remote_gitcode"
                    meta["remote_schema_basename"] = remote_basename
                    meta["definition_schema_category_label_zh"] = (
                        "远程 OEM schema（GitCode openUBMC 仓库）"
                    )
                    meta["validation_summary_zh"] = (
                        f"入口 JsonSchemaFile：{entry_zh}"
                        f"（{entry_rel or schema_filename + '.json'}）；"
                        f"实际用于属性校验的定义来自远程：{remote_basename}"
                    )
            else:
                skip_reason = (
                    f"JsonSchemaFile {schema_filename}.json is a pointer document but no actual "
                    f"JSON Schema definition (with 'definitions'/'properties') was found locally. "
                    f"Schema validation skipped for this source."
                )
                meta["validation_summary_zh"] = (
                    f"入口 JsonSchemaFile：{entry_zh}"
                    f"（{entry_rel or schema_filename + '.json'}）；"
                    "未能从本地或远程解析到用于属性校验的定义。"
                )
                return None, meta, skip_reason

        # -- 解析顶层 $ref --
        if "$ref" in schema:
            ref_schema = self._resolve_ref(schema["$ref"])
            if ref_schema:
                schema = ref_schema
            else:
                return None, meta, f"Unable to resolve reference: {schema['$ref']}"

        # -- 处理 anyOf --
        if "anyOf" in schema:
            for option in schema["anyOf"]:
                if "properties" in option:
                    schema = option
                    break

        # -- validation_summary_zh --
        if "validation_summary_zh" not in meta:
            stem = meta.get("entry_schema_stem") or ""
            erel = meta.get("entry_schema_path_relative")
            ezh = meta.get("entry_schema_category_label_zh", "schema")
            meta["validation_summary_zh"] = (
                f"静态校验直接依据：{ezh}"
                + (f"（{erel}）" if erel else (f"（{stem}.json）" if stem else ""))
            )

        return schema, meta, None

    def _resolve_ref(self, ref: str) -> Optional[Dict[str, Any]]:
        """
        解析 $ref 到实际的 schema 定义

        Args:
            ref: 引用路径

        Returns:
            解析后的 schema 定义
        """
        if not ref:
            return None

        # 内部引用: #/definitions/xxx
        if ref.startswith("#/definitions/"):
            def_name = ref.replace("#/definitions/", "")
            return self._definitions.get(def_name)

        # 外部引用: http://... or https://...
        elif ref.startswith("http://") or ref.startswith("https://"):
            parts = ref.split("#")
            if len(parts) == 2:
                schema_name = parts[0].split("/")[-1].replace(".json", "")
                def_path = parts[1]
                if def_path.startswith("/definitions/"):
                    def_name = def_path.replace("/definitions/", "", 1)
                else:
                    def_name = def_path

                # 大小写不敏感搜索 schema
                found_schema_name = None
                for sn in self._schemas.keys():
                    if sn.lower() == schema_name.lower():
                        found_schema_name = sn
                        break

                if found_schema_name:
                    schema_data = self._schemas[found_schema_name]
                    logger.debug(f"Resolving $ref: {ref} -> {found_schema_name}.json#/definitions/{def_name}")
                    if "definitions" in schema_data:
                        return schema_data["definitions"].get(def_name)

            logger.warning(f"External reference not fully supported: {ref}")
            return None

        # 相对引用: file.json#/xxx
        elif ".json#/" in ref:
            parts = ref.split("#/")
            schema_name = parts[0].replace(".json", "")
            def_path = "#/definitions/" + parts[1] if len(parts) > 1 else ""

            # 大小写不敏感搜索 schema
            found_schema_name = None
            for sn in self._schemas.keys():
                if sn.lower() == schema_name.lower():
                    found_schema_name = sn
                    break

            if found_schema_name:
                schema_data = self._schemas[found_schema_name]
                logger.debug(f"Resolving $ref: {ref} -> {found_schema_name}.json#/definitions/{parts[1]}")
                if "definitions" in schema_data:
                    return schema_data["definitions"].get(parts[1])

            logger.warning(f"External reference not fully supported: {ref}")
            return None

        return None

    def _get_type_from_odata_type(self, odata_type: str) -> tuple[Optional[str], Optional[str]]:
        """
        从 @odata.type 提取类型名和版本

        Args:
            odata_type: @odata.type 值

        Returns:
            (base_type, full_type) 元组
            例如: "#Drive.v1_21_0.Drive" -> ("Drive", "Drive.v1_21_0")
        """
        if not odata_type or not isinstance(odata_type, str):
            return None, None

        if odata_type.startswith("#"):
            odata_type = odata_type[1:]

        parts = odata_type.split(".")
        base_type = parts[0]

        # 提取版本号
        if len(parts) >= 2:
            if len(parts) >= 3 and parts[1].startswith('v'):
                full_type = f"{parts[0]}.{parts[1]}"
            else:
                full_type = base_type
        else:
            full_type = base_type

        return base_type, full_type

    @staticmethod
    def _schema_field_to_entity_name(schema_value: str) -> str:
        """
        从 JsonSchemaFile 资源的 Schema 字段解析实体名。
        例如 #PerformanceCollection.v1_0_0.PerformanceCollection -> PerformanceCollection
        """
        if not schema_value or not isinstance(schema_value, str):
            return ""
        s = schema_value.strip()
        if s.startswith("#"):
            s = s[1:]
        parts = [p for p in s.split(".") if p]
        return parts[-1] if parts else ""

    def _is_json_schema_file_pointer(self, schema: Dict[str, Any]) -> bool:
        """是否为 Redfish JsonSchemaFile（仅含 Location 指针、无资源 properties）。"""
        odata_type = schema.get("@odata.type", "")
        if isinstance(odata_type, str) and "JsonSchemaFile" in odata_type:
            return True
        if schema.get("Location") and schema.get("Schema") and not schema.get("properties"):
            return True
        return False

    def _fetch_remote_schema(self, filename: str) -> Optional[Dict[str, Any]]:
        """
        从 GitCode 远程仓库获取 schema 定义文件。
        filename 为 Location URI 中的文件名（如 PerformanceCollection.v1_0_0.json），
        自动转小写拼接远程 URL。
        """
        remote_name = filename.lower()
        url = GITCODE_SCHEMA_BASE_URL + remote_name
        logger.info(f"Trying remote schema fetch: {url}")
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "RedfishSchemaValidator/1.0"})
            # URL is built from a fixed HTTPS GitCode schema base URL.
            with urllib.request.urlopen(req, timeout=15) as resp:  # nosec
                data = json.loads(resp.read().decode("utf-8"))
            if isinstance(data, dict) and ("definitions" in data or "properties" in data):
                logger.info(f"Remote schema fetched successfully: {remote_name}")
                return data
            logger.debug(f"Remote file {remote_name} has no definitions/properties, skipped.")
        except urllib.error.HTTPError as e:
            logger.debug(f"Remote schema not found ({e.code}): {url}")
        except Exception as e:
            logger.debug(f"Remote schema fetch failed: {url} -> {e}")
        return None

    def _find_schema_path_by_basename(self, basename: str) -> Optional[Path]:
        """在 schema 目录中按文件名（大小写不敏感）查找。"""
        if not basename:
            return None
        want = basename.lower()
        search_dirs = self._schema_bundle_dirs()
        if not search_dirs:
            search_dirs = [self._schema_directory]
        for d in search_dirs:
            for p in d.glob("*.json"):
                if p.name.lower() == want:
                    return p
        return None

    def _path_relative_to_schema_root(self, path: Optional[Path]) -> Optional[str]:
        if path is None:
            return None
        try:
            return path.resolve().relative_to(self._schema_directory.resolve()).as_posix()
        except ValueError:
            return path.as_posix()

    def _classify_schema_location(
        self, path: Optional[Path]
    ) -> Tuple[str, str]:
        """
        根据文件相对 SchemaFiles 根的路径归类，返回 (category_key, 中文说明)。
        """
        if path is None:
            return ("unknown", "未知")
        try:
            rel = path.resolve().relative_to(self._schema_directory.resolve())
            parts = rel.parts
        except ValueError:
            return ("outside_schema_root", path.name)

        if not parts:
            return ("unknown", "未知")
        top = parts[0].lower()
        if top == "dmtf":
            return ("dmtf_official", "DMTF 官方 schema（SchemaFiles/dmtf）")
        if top == "rackmount" and len(parts) >= 2:
            second = parts[1].lower()
            if second == "oem":
                return ("oem_openubmc", "rackmount OEM 自定义（rackmount/oem/openubmc）")
            if second == "jsonschemas":
                return (
                    "rackmount_jsonschemas",
                    "rackmount/jsonschemas（JsonSchemaFile 指针目标等）",
                )
            return ("rackmount_other", "rackmount 目录下 schema")
        return ("other", rel.as_posix())

    def _resolve_json_schema_file_pointer(
        self, pointer_schema: Dict[str, Any], schema_filename: str
    ) -> Tuple[Optional[Dict[str, Any]], Optional[Path], str, str]:
        """
        若当前文件为 JsonSchemaFile，则根据 Location.Uri 加载本地或远程 JSON，
        并从 definitions 中取 Schema 字段对应的实体定义作为校验用 schema。

        Returns:
            (resolved_schema, local_definition_path, origin, remote_basename)
            origin 为 \"local\" | \"remote\" | \"\"；远程时 path 为 None，basename 为文件名。
        """
        entity = self._schema_field_to_entity_name(pointer_schema.get("Schema", ""))
        if not entity:
            logger.warning(
                f"JsonSchemaFile pointer {schema_filename}.json has no usable Schema field; skip resolve."
            )
            return None, None, "", ""

        locations = pointer_schema.get("Location")
        if not isinstance(locations, list):
            return None, None, "", ""

        source_path = self._find_schema_path_by_basename(f"{schema_filename}.json")

        for entry in locations:
            if not isinstance(entry, dict):
                continue
            uri = entry.get("Uri") or entry.get("URI")
            if not uri:
                continue
            basename = Path(str(uri).replace("\\", "/")).name
            path = self._find_schema_path_by_basename(basename)
            if not path:
                logger.debug(f"Pointer target not in schema dir: {basename}")
                continue

            if source_path and path.resolve() == source_path.resolve():
                logger.debug(
                    f"Skipping self-referencing pointer: {schema_filename}.json -> {basename}"
                )
                continue

            try:
                with open(path, "r", encoding="utf-8") as f:
                    target = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load pointer target {path}: {e}")
                continue

            if not isinstance(target, dict):
                continue

            if self._is_json_schema_file_pointer(target):
                logger.debug(
                    f"Skipping pointer-to-pointer: {schema_filename}.json -> {basename}"
                )
                continue

            if "definitions" in target and isinstance(target["definitions"], dict):
                self._definitions.update(target["definitions"])

            defs = target.get("definitions") or {}
            if entity in defs:
                logger.info(
                    f"Resolved JsonSchemaFile pointer {schema_filename}.json -> "
                    f"{path.name} definitions['{entity}']"
                )
                return defs[entity], path, "local", ""

            if target.get("properties"):
                logger.info(
                    f"Resolved JsonSchemaFile pointer {schema_filename}.json -> "
                    f"{path.name} (root properties)"
                )
                return target, path, "local", ""

            if isinstance(defs, dict) and len(defs) == 1:
                sole = next(iter(defs.values()))
                if isinstance(sole, dict):
                    logger.info(
                        f"Resolved JsonSchemaFile pointer {schema_filename}.json -> "
                        f"{path.name} (sole definition)"
                    )
                    return sole, path, "local", ""

            logger.warning(
                f"Loaded {path.name} but could not map Schema entity '{entity}' to definitions."
            )

        # 本地解析全部失败，尝试从 GitCode 远程获取
        tried_remote = set()
        for entry in locations:
            if not isinstance(entry, dict):
                continue
            uri = entry.get("Uri") or entry.get("URI")
            if not uri:
                continue
            basename = Path(str(uri).replace("\\", "/")).name
            if basename.lower() in tried_remote:
                continue
            tried_remote.add(basename.lower())

            remote_data = self._fetch_remote_schema(basename)
            if remote_data is None:
                continue

            if "definitions" in remote_data and isinstance(remote_data["definitions"], dict):
                self._definitions.update(remote_data["definitions"])

            defs = remote_data.get("definitions") or {}
            if entity in defs:
                logger.info(
                    f"Resolved pointer {schema_filename}.json via remote -> "
                    f"{basename} definitions['{entity}']"
                )
                return defs[entity], None, "remote", basename

            if remote_data.get("properties"):
                logger.info(
                    f"Resolved pointer {schema_filename}.json via remote -> "
                    f"{basename} (root properties)"
                )
                return remote_data, None, "remote", basename

        return None, None, "", ""

    def _record_error(self, error_type: str, message: str, property_path: Optional[str] = None) -> None:
        """记录错误信息"""
        error_entry = {
            "type": error_type,
            "message": message
        }
        if property_path:
            error_entry["property"] = property_path
        self._errors.append(error_entry)
        self._fail_count += 1

    def _record_warning(self, warning_type: str, message: str, property_path: Optional[str] = None) -> None:
        """记录警告信息"""
        warning_entry = {
            "type": warning_type,
            "message": message
        }
        if property_path:
            warning_entry["property"] = property_path
        self._warnings.append(warning_entry)
        self._warn_count += 1

    def _validate_property(
        self,
        prop_name: str,
        prop_value: Any,
        prop_schema: Dict[str, Any],
        prop_path: str
    ) -> None:
        """验证单个属性"""
        if not prop_schema:
            logger.warning(f"Unknown Property: '{prop_path}' is not defined in schema.")
            self._warn_count += 1
            return

        # 解析 $ref
        if "$ref" in prop_schema:
            ref_schema = self._resolve_ref(prop_schema["$ref"])
            if ref_schema:
                prop_schema = ref_schema
            else:
                error_msg = f"Schema Error: Unable to resolve reference: {prop_schema['$ref']}"
                logger.error(error_msg)
                self._record_error("Schema Error", error_msg, prop_path)
                return

        prop_type = prop_schema.get("type")
        is_nullable = False

        # 处理类型列表
        if isinstance(prop_type, list):
            if "null" in prop_type:
                is_nullable = True
            prop_type = [t for t in prop_type if t != "null"]
            if len(prop_type) == 1:
                prop_type = prop_type[0]
            elif len(prop_type) == 0:
                prop_type = None

        # 处理 null 值
        if prop_value is None:
            if is_nullable:
                logger.debug(f"Property '{prop_path}' is valid (null allowed).")
                self._pass_count += 1
            else:
                error_msg = f"Null Error: Property '{prop_path}' contains null, but null is not allowed."
                logger.error(error_msg)
                self._record_error("Null Error", error_msg, prop_path)
            return

        if not prop_type:
            logger.debug(f"Property '{prop_path}' is valid (no type constraint).")
            self._pass_count += 1
            return

        # 枚举值验证
        if "enum" in prop_schema:
            enum_values = prop_schema["enum"]
            if prop_value not in enum_values:
                error_msg = f"Property Value Error: Property '{prop_path}' value '{prop_value}' is not in allowed values: {enum_values}"
                logger.error(error_msg)
                self._record_error("Property Value Error", error_msg, prop_path)
            else:
                logger.debug(f"Property '{prop_path}' is valid.")
                self._pass_count += 1
            return

        # 类型验证
        type_checks = {
            "string": lambda v: isinstance(v, str),
            "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
            "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
            "boolean": lambda v: isinstance(v, bool),
            "object": lambda v: isinstance(v, dict),
            "array": lambda v: isinstance(v, list),
        }

        if prop_type in type_checks:
            if type_checks[prop_type](prop_value):
                logger.debug(f"Property '{prop_path}' is valid.")
                self._pass_count += 1
            else:
                error_msg = f"Property Type Error: Property '{prop_path}' is expected to be {prop_type}, but found '{type(prop_value).__name__}'."
                logger.error(error_msg)
                self._record_error("Property Type Error", error_msg, prop_path)
                return

        # 对象嵌套验证
        if prop_type == "object":
            nested_schema = prop_schema.get("properties", {})
            required_props = prop_schema.get("required", [])
            self._validate_object(prop_value, nested_schema, required_props, prop_path)

        # 数组元素验证
        elif prop_type == "array":
            items_schema = prop_schema.get("items", {})
            if items_schema and isinstance(prop_value, list):
                for i, item in enumerate(prop_value):
                    item_path = f"{prop_path}/{i}"
                    self._validate_property(str(i), item, items_schema, item_path)

    def _validate_object(
        self,
        payload: Dict[str, Any],
        schema_props: Dict[str, Any],
        required_props: List[str],
        prop_path: str = ""
    ) -> None:
        """验证对象属性"""
        if not schema_props:
            return

        # 验证存在的属性
        for prop_name, prop_value in payload.items():
            # 跳过 OEM 属性
            if prop_name == "Oem" and self._no_oem:
                logger.debug("Skip: OEM extension checking is disabled.")
                self._skip_count += 1
                continue

            # 跳过注解属性
            if prop_name.startswith("@") or prop_name.startswith("#"):
                continue

            current_path = f"{prop_path}/{prop_name}" if prop_path else prop_name
            prop_schema = schema_props.get(prop_name)
            self._validate_property(prop_name, prop_value, prop_schema, current_path)

        # 检查必需属性
        for prop_name in required_props:
            if prop_name not in payload:
                current_path = f"{prop_path}/{prop_name}" if prop_path else prop_name
                error_msg = f"Required Property Error: Property '{current_path}' is mandatory, but not present in the payload."
                logger.error(error_msg)
                self._record_error("Required Property Error", error_msg, current_path)

    def validate(self, uri: str, payload: Dict[str, Any]) -> ValidationResult:
        """
        验证 payload 是否符合 schema 定义（同时校验 DMTF 和 OEM 两个来源的 schema）。

        若 DMTF 和 OEM 均存在同类型的 schema，将合并两者的 properties 后统一校验；
        若某一侧缺失，会在结果中给出提示。

        Args:
            uri: 资源 URI
            payload: 要验证的 payload

        Returns:
            验证结果对象
        """
        result = ValidationResult()
        self.schema_check_meta = {}

        logger.info(f"Validating URI: {uri}")
        if self._schema_bundle_dirs():
            logger.info(
                f"Schema directory: {self._schema_directory} "
                f"(DMTF: {SCHEMA_SUBDIR_DMTF}/；"
                f"OEM: {SCHEMA_SUBDIR_OEM_OPENUBMC_JSON_SCHEMA.as_posix()}/ "
                f"与 {SCHEMA_SUBDIR_OEM_OPENUBMC.as_posix()}/；"
                f"$ref/指针可解析 {SCHEMA_SUBDIR_RACKMOUNT_JSONSCHEMAS.as_posix()}/)"
            )
        else:
            logger.info(f"Schema directory: {self._schema_directory} (legacy flat layout)")

        if not isinstance(payload, dict):
            error_msg = "Resource Error: Resource response does not contain a JSON object."
            logger.error(error_msg)
            result.result = "error"
            result.add_error("Resource Error", error_msg)
            return result

        # 检查 @odata.type
        odata_type = payload.get("@odata.type")
        if not odata_type:
            error_msg = "Required Property Error: Property '@odata.type' is mandatory, but not present in the payload."
            logger.error(error_msg)
            result.result = "error"
            result.add_error("Required Property Error", error_msg)
            return result

        base_type, full_type = self._get_type_from_odata_type(odata_type)

        if not base_type:
            error_msg = f"Schema Error: Unable to extract type name from @odata.type: {odata_type}"
            logger.error(error_msg)
            result.result = "error"
            result.add_error("Schema Error", error_msg)
            return result

        # ===== 同时从 DMTF 和 OEM 解析 schema =====
        dmtf_raw, dmtf_filename, _, dmtf_path = self._resolve_schema_from_dmtf(
            full_type, base_type
        )
        oem_raw, oem_filename, _, oem_path = self._resolve_schema_from_oem(
            full_type, base_type
        )

        has_dmtf = dmtf_raw is not None
        has_oem = oem_raw is not None

        self.schema_check_meta["schema_root"] = self._schema_directory.resolve().as_posix()
        self.schema_check_meta["dmtf_schema_found"] = has_dmtf
        self.schema_check_meta["oem_schema_found"] = has_oem

        # 两个来源均未找到 → 回退旧布局
        if not has_dmtf and not has_oem:
            leg_raw, leg_filename, leg_source, leg_path = self._resolve_schema_legacy(
                full_type, base_type
            )
            if leg_raw is None:
                warn_msg = (
                    f"Schema file not found under {SCHEMA_SUBDIR_DMTF}/ or "
                    f"{SCHEMA_SUBDIR_OEM_OPENUBMC_JSON_SCHEMA.as_posix()}/ / "
                    f"{SCHEMA_SUBDIR_OEM_OPENUBMC.as_posix()}/ for type '{base_type}' "
                    f"(tried '{full_type}' and '{base_type}'). Static check skipped."
                )
                logger.warning(warn_msg)
                result.add_warning("Schema Not Found", warn_msg)
                result.result = "skip"
                return result
            schemas_raw = [(leg_raw, leg_filename, leg_source, leg_path)]
        else:
            schemas_raw: List[tuple] = []
            if has_dmtf:
                schemas_raw.append((dmtf_raw, dmtf_filename, "dmtf", dmtf_path))
            if has_oem:
                schemas_raw.append((oem_raw, oem_filename, "oem", oem_path))

            # 单侧缺失提示
            if has_dmtf and not has_oem:
                warn_msg = (
                    f"OEM 中不包含类型 '{base_type}' 的 schema，"
                    f"仅在 DMTF 中找到（{dmtf_filename}.json）。"
                )
                logger.warning(warn_msg)
                result.add_warning("OEM Schema Not Found", warn_msg)
            elif has_oem and not has_dmtf:
                warn_msg = (
                    f"DMTF 中不包含类型 '{base_type}' 的 schema，"
                    f"仅在 OEM 中找到（{oem_filename}.json）。"
                )
                logger.warning(warn_msg)
                result.add_warning("DMTF Schema Not Found", warn_msg)

        self.schema_check_meta["validated_sources"] = [s[2] for s in schemas_raw]

        # ===== 逐来源解析到 properties，合并后统一校验 =====
        merged_props: Dict[str, Any] = {}
        merged_required: List[str] = []
        primary_meta_set = False

        for raw_schema, filename, source, epath in schemas_raw:
            resolved, meta, skip_reason = self._resolve_to_properties(
                raw_schema, filename, source, epath
            )
            if resolved is not None:
                src_props = resolved.get("properties", {})
                merged_props.update(src_props)
                merged_required.extend(resolved.get("required", []))
                logger.info(
                    f"[{source.upper()}] Schema resolved: {filename}.json "
                    f"→ {len(src_props)} properties"
                )
            else:
                warn_msg = (
                    f"[{source.upper()}] Schema 解析跳过: {skip_reason}"
                )
                logger.warning(warn_msg)
                result.add_warning(f"{source.upper()} Schema Skip", skip_reason or "")

            if not primary_meta_set and meta:
                self.schema_check_meta.update(meta)
                primary_meta_set = True
            elif meta:
                self.schema_check_meta[f"{source}_meta"] = meta

        if not merged_props:
            warn_msg = (
                "Schema validation produced no usable properties from any source; "
                "result marked skip."
            )
            logger.info(warn_msg)
            result.add_warning("Schema Check Skipped", warn_msg)
            result.result = "skip"
            return result

        # ===== 执行属性校验 =====
        merged_required_unique = list(set(merged_required))
        logger.info(
            f"Validating against merged schema: "
            f"{len(merged_props)} properties, {len(merged_required_unique)} required"
        )
        self._validate_object(payload, merged_props, merged_required_unique)

        # ===== 判断最终结果 =====
        substantive = self._pass_count + self._warn_count + self._fail_count
        if substantive == 0:
            warn_msg = (
                "Schema validation produced no property checks "
                "(e.g. empty properties/required or only skipped keys); result marked skip."
            )
            logger.info(warn_msg)
            result.add_warning("Schema Check Skipped", warn_msg)
            result.result = "skip"
        else:
            result.result = "pass" if self._fail_count == 0 else "fail"

        # 合并各来源的 validation_summary_zh
        summaries = []
        if primary_meta_set:
            primary_summary = self.schema_check_meta.get("validation_summary_zh")
            if primary_summary:
                summaries.append(primary_summary)
        for src_key in [k for k in self.schema_check_meta if k.endswith("_meta")]:
            src_summary = self.schema_check_meta[src_key].get("validation_summary_zh")
            if src_summary:
                src_label = src_key.replace("_meta", "").upper()
                summaries.append(f"[{src_label}] {src_summary}")
        if len(summaries) > 1:
            self.schema_check_meta["validation_summary_zh"] = "；".join(summaries)

        return result

    # ==================== 属性访问 ====================

    @property
    def pass_count(self) -> int:
        return self._pass_count

    @property
    def warn_count(self) -> int:
        return self._warn_count

    @property
    def fail_count(self) -> int:
        return self._fail_count

    @property
    def skip_count(self) -> int:
        return self._skip_count

    @property
    def errors(self) -> List[Dict[str, str]]:
        """获取所有错误信息列表"""
        return self._errors

    @property
    def warnings(self) -> List[Dict[str, str]]:
        """获取所有警告信息列表"""
        return self._warnings


def validate_static_schema(
    payload: Dict[str, Any],
    schema_directory: str,
    uri: str = "/redfish/v1",
    no_oem_check: bool = False,
    save_result: bool = False,
    output_file: Optional[str] = None
) -> Dict[str, Any]:
    """
    验证 Redfish Payload 的静态 Schema

    Args:
        payload: Payload JSON 数据对象
        schema_directory: Schema 文件目录路径
        uri: URI（仅用于显示）
        no_oem_check: 是否跳过 OEM 检查
        save_result: 是否保存结果到文件
        output_file: 输出文件路径（可选）

    Returns:
        验证结果字典
    """
    validator = JSONSchemaValidator(schema_directory, no_oem_check)

    if not uri or uri == "/redfish/v1":
        uri = payload.get("@odata.id", "/redfish/v1")

    # 执行验证
    validation_result = validator.validate(uri, payload)

    # 获取资源类型
    odata_type = payload.get("@odata.type", "")
    resource_type = f"#{odata_type.split('.')[-2]}" if "." in odata_type else "#Unknown"

    # 构建错误详情
    static_validation_errors = []
    for error in validator.errors:
        error_entry = {"message": error.get("message", "")}
        if "property" in error:
            error_entry["property"] = error["property"]
        static_validation_errors.append(error_entry)

    # 构建警告详情
    static_validation_warnings = []
    for warning in validator.warnings:
        warning_entry = {"message": warning.get("message", "")}
        if "property" in warning:
            warning_entry["property"] = warning["property"]
        static_validation_warnings.append(warning_entry)

    # 生成修复建议
    static_validation_advices = []
    for error in validator.errors:
        advice_msg = _generate_advice_from_error(error)
        static_validation_advices.append({
            "message": advice_msg,
            "property": error.get("property", "")
        })

    # 合并警告和建议
    all_static_advices = static_validation_warnings + static_validation_advices

    # 计算统计
    total_checks = validator.pass_count + validator.warn_count + validator.fail_count + validator.skip_count

    # 构建结果字典
    result = {
        "uri": uri,
        "resource_type": resource_type,
        "total_checks_num": total_checks,
        "failed_checks_num": validator.fail_count,
        "warning_checks_num": validator.warn_count,
        "schema_check": dict(validator.schema_check_meta),
        "error_details": {
            "STATIC_VALIDATION": static_validation_errors,
            "MODEL_VALIDATION": []
        },
        "advice_details": {
            "STATIC_VALIDATION": all_static_advices,
            "MODEL_VALIDATION": []
        },
        "result": validation_result.result
    }

    # 保存结果
    if save_result and output_file:
        save_json(result, output_file)
        result["output_file"] = output_file

    return result


def _generate_advice_from_error(error: Dict[str, str]) -> str:
    """从错误信息生成修复建议"""
    error_msg = error.get("message", "")
    error_type = error.get("type", "")
    property_name = error.get("property", "")

    # 属性类型错误
    if "Property Type Error" in error_type or "expected to be" in error_msg:
        match = re.search(r"expected to be a (\w+), but found '(\w+)'", error_msg)
        if match:
            expected_type = match.group(1)
            actual_type = match.group(2)
            if property_name:
                return f"将属性 '{property_name}' 的值从 {actual_type} 类型改为 {expected_type} 类型"
            else:
                return f"将属性值从 {actual_type} 类型改为 {expected_type} 类型"

    # 必需属性错误
    elif "Required Property Error" in error_type:
        if property_name:
            return f"添加必需属性 '{property_name}'"
        else:
            return "检查并添加所有必需属性"

    # Null 错误
    elif "Null Error" in error_type:
        if property_name:
            return f"属性 '{property_name}' 不允许为 null，请提供有效值"
        else:
            return "该属性不允许为 null，请提供有效值"

    # Schema 错误
    elif "Schema Error" in error_type:
        return "检查资源定义是否符合 Schema 规范"

    # 默认建议
    if property_name:
        return f"请检查属性 '{property_name}' 是否符合 Redfish 规范"
    else:
        return "请检查资源是否符合 Redfish 规范"


def generate_schema_advice_from_error(error: Dict[str, str]) -> str:
    """
    供 method2 / end_to_end_check 等将 Schema 校验失败合并进 ``rule_compliance.error_details`` 时使用，
    与 ``validate_static_schema`` 中对每条 ``validator.errors`` 生成的建议文案一致（内部即 ``_generate_advice_from_error``）。
    """
    return _generate_advice_from_error(error)
