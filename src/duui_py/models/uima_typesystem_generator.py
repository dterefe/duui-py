from __future__ import annotations

import argparse
import keyword
import re
import shutil
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict
import xml.etree.ElementTree as ET

NS = {"u": "http://uima.apache.org/resourceSpecifier"}


@dataclass
class FeatureDef:
    name: str
    range_type: str
    element_type: str | None = None


@dataclass
class TypeDef:
    name: str
    supertype: str
    features: Dict[str, FeatureDef] = field(default_factory=dict)


def _text(node: ET.Element | None) -> str:
    if node is None or node.text is None:
        return ""
    return node.text.strip()


def _is_uima_typesystem(root: ET.Element) -> bool:
    tag = root.tag
    return tag.endswith("typeSystemDescription") and "uima.apache.org/resourceSpecifier" in tag


def collect_types_from_path(source_root: Path) -> tuple[dict[str, TypeDef], int]:
    parsed_files = 0
    merged: dict[str, TypeDef] = {}

    for xml_file in sorted(source_root.rglob("*.xml")):
        try:
            root = ET.parse(xml_file).getroot()
        except Exception:
            continue

        if not _is_uima_typesystem(root):
            continue

        parsed_files += 1
        for td in root.findall("u:types/u:typeDescription", NS):
            type_name = _text(td.find("u:name", NS))
            supertype = _text(td.find("u:supertypeName", NS)) or "uima.cas.TOP"
            if not type_name:
                continue

            if type_name not in merged:
                merged[type_name] = TypeDef(name=type_name, supertype=supertype, features={})

            # Keep first seen supertype, merge features across duplicates.
            tdef = merged[type_name]

            for fd in td.findall("u:features/u:featureDescription", NS):
                fname = _text(fd.find("u:name", NS))
                if not fname:
                    continue
                frange = _text(fd.find("u:rangeTypeName", NS)) or "uima.cas.TOP"
                felem = _text(fd.find("u:elementType", NS)) or None
                if fname not in tdef.features:
                    tdef.features[fname] = FeatureDef(name=fname, range_type=frange, element_type=felem)

    return merged, parsed_files


def _sanitize_identifier(name: str) -> str:
    out = re.sub(r"[^0-9a-zA-Z_]", "_", name)
    if not out:
        out = "field"
    if out[0].isdigit():
        out = f"f_{out}"
    if keyword.iskeyword(out):
        out = f"{out}_"
    return out


def _module_key_for_type(type_name: str) -> tuple[str, ...]:
    parts = type_name.split(".")
    if len(parts) <= 1:
        return ("_root",)

    package = parts[:-1]

    # Drop generic Internet-style roots for cleaner Python package layout.
    if len(package) >= 2 and package[0] == "com" and package[1] == "github":
        package = package[2:]
    while package and package[0] in {"org", "com"}:
        package = package[1:]

    if not package:
        return ("_root",)

    return tuple(_sanitize_identifier(p) for p in package)


def _class_name_for_type(type_name: str, used: dict[str, int]) -> str:
    base = _sanitize_identifier(type_name.split(".")[-1])
    if base and base[0].islower():
        base = base[:1].upper() + base[1:]

    n = used[base]
    used[base] += 1
    if n == 0:
        return base

    parts = [_sanitize_identifier(p) for p in type_name.split(".") if p]
    suffix = "_".join(parts[-3:])
    candidate = f"{base}_{suffix}"
    if used[candidate] == 0:
        used[candidate] += 1
        return candidate

    idx = used[base]
    candidate = f"{base}_{idx}"
    used[candidate] += 1
    return candidate


PRIMITIVE_MAP = {
    "uima.cas.String": "str",
    "uima.cas.Boolean": "bool",
    "uima.cas.Byte": "int",
    "uima.cas.Short": "int",
    "uima.cas.Integer": "int",
    "uima.cas.Long": "int",
    "uima.cas.Float": "float",
    "uima.cas.Double": "float",
}

ARRAY_MAP = {
    "uima.cas.StringArray": "list[str]",
    "uima.cas.BooleanArray": "list[bool]",
    "uima.cas.ByteArray": "list[int]",
    "uima.cas.ShortArray": "list[int]",
    "uima.cas.IntegerArray": "list[int]",
    "uima.cas.LongArray": "list[int]",
    "uima.cas.FloatArray": "list[float]",
    "uima.cas.DoubleArray": "list[float]",
    "uima.cas.FSArray": "list[UimaValue]",
    "uima.cas.StringList": "list[str]",
    "uima.cas.IntegerList": "list[int]",
    "uima.cas.FloatList": "list[float]",
    "uima.cas.FSList": "list[UimaValue]",
}


def _py_type_for_range(range_type: str) -> str:
    if range_type in PRIMITIVE_MAP:
        return PRIMITIVE_MAP[range_type]
    if range_type in ARRAY_MAP:
        # Keep FS containers flexible for {"$ref": id} items.
        if range_type in {"uima.cas.FSArray", "uima.cas.FSList"}:
            return "list[UimaValue]"
        return ARRAY_MAP[range_type]
    # Keep non-primitive feature values reference-safe.
    return "UimaValue"


def _base_class_for_supertype(supertype: str) -> str:
    # Only special handling: UIMA base hierarchy.
    if supertype == "uima.tcas.Annotation" or supertype.startswith("uima.tcas"):
        return "Annotation"
    if supertype in {"uima.cas.TOP", "uima.cas.AnnotationBase"}:
        return "FeatureStructure"
    # Non-UIMA supertypes are feature structures by default to avoid cross-module coupling.
    return "FeatureStructure"


def generate_models(source_root: Path, output_root: Path, clear_output: bool = True) -> dict[str, int]:
    types_by_name, parsed_files = collect_types_from_path(source_root)

    class_name_used: dict[str, int] = defaultdict(int)
    type_to_class: dict[str, str] = {}
    type_to_module: dict[str, tuple[str, ...]] = {}
    module_to_types: dict[tuple[str, ...], list[str]] = defaultdict(list)

    for tname in sorted(types_by_name):
        type_to_class[tname] = _class_name_for_type(tname, class_name_used)
        mkey = _module_key_for_type(tname)
        type_to_module[tname] = mkey
        module_to_types[mkey].append(tname)

    _effective_feature_cache: dict[str, dict[str, FeatureDef]] = {}

    def _effective_features(type_name: str, visiting: set[str] | None = None) -> dict[str, FeatureDef]:
        if type_name in _effective_feature_cache:
            return _effective_feature_cache[type_name]

        if visiting is None:
            visiting = set()
        if type_name in visiting:
            # Guard against malformed cyclic type graphs.
            return {}
        visiting.add(type_name)

        tdef = types_by_name[type_name]
        merged: dict[str, FeatureDef] = {}
        supertype = tdef.supertype
        if supertype in types_by_name:
            merged.update(_effective_features(supertype, visiting))
        merged.update(tdef.features)
        _effective_feature_cache[type_name] = merged
        visiting.remove(type_name)
        return merged

    if clear_output and output_root.exists():
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    # Write one module per namespace directory: <ns>/types.py
    for mkey, type_names in sorted(module_to_types.items()):
        mod_dir = output_root.joinpath(*mkey)
        mod_dir.mkdir(parents=True, exist_ok=True)
        # Ensure every intermediate namespace directory is a Python package.
        rel = mod_dir.relative_to(output_root)
        current = output_root
        for part in rel.parts:
            current = current / part
            init_file = current / "__init__.py"
            if not init_file.exists():
                init_file.write_text("", encoding="utf-8")

        lines: list[str] = []
        lines.append('"""Auto-generated UIMA models for namespace: ' + ".".join(mkey) + '."""')
        lines.append("")
        lines.append("from __future__ import annotations")
        lines.append("")
        lines.append("from typing import ClassVar, Optional")
        lines.append("from pydantic import Field")
        lines.append("")
        lines.append("from duui_py.models.uima import Annotation, FeatureStructure, UimaValue")
        lines.append("")

        exported_classes: list[str] = []
        type_pairs: list[tuple[str, str]] = []

        for tname in sorted(type_names):
            tdef = types_by_name[tname]
            cls = type_to_class[tname]
            base = _base_class_for_supertype(tdef.supertype)
            exported_classes.append(cls)
            type_pairs.append((tname, cls))

            lines.append(f"class {cls}({base}):")
            all_features = _effective_features(tname)
            feature_names = tuple(sorted(all_features))
            feature_fields = tuple(
                (_sanitize_identifier(fname), fname) for fname in sorted(all_features)
            )
            lines.append(f"    __duui_type_name__: ClassVar[str] = \"{tname}\"")
            lines.append(f"    __duui_feature_names__: ClassVar[tuple[str, ...]] = {feature_names!r}")
            lines.append(
                "    __duui_feature_fields__: ClassVar[tuple[tuple[str, str], ...]] = "
                f"{feature_fields!r}"
            )
            lines.append(f"    type: str = \"{tname}\"")
            if not all_features:
                lines.append("    pass")
                lines.append("")
                continue

            for fname, fdef in sorted(all_features.items(), key=lambda kv: kv[0]):
                pyname = _sanitize_identifier(fname)
                ftype = _py_type_for_range(fdef.range_type)
                if pyname == fname:
                    lines.append(f"    {pyname}: Optional[{ftype}] = None")
                else:
                    lines.append(
                        f"    {pyname}: Optional[{ftype}] = Field(default=None, alias=\"{fname}\")"
                    )
            lines.append("")

        lines.append("UIMA_TYPE_TO_CLASS = {")
        for tname, cls in type_pairs:
            lines.append(f"    \"{tname}\": {cls},")
        lines.append("}")
        lines.append("")
        lines.append("__all__ = [")
        for cls in exported_classes:
            lines.append(f"    \"{cls}\",")
        lines.append("    \"UIMA_TYPE_TO_CLASS\",")
        lines.append("]")
        lines.append("")

        (mod_dir / "types.py").write_text("\n".join(lines), encoding="utf-8")
        (mod_dir / "__init__.py").write_text("from .types import *  # noqa: F401,F403\n", encoding="utf-8")

    # Root package loader with dynamic registry aggregation.
    root_lines = [
        '"""Auto-generated namespace-mapped UIMA model package."""',
        "",
        "from __future__ import annotations",
        "",
        "import importlib",
        "import pkgutil",
        "",
        "UIMA_TYPE_TO_CLASS = {}",
        "for modinfo in pkgutil.walk_packages(__path__, prefix=__name__ + '.'):",
        "    if not modinfo.name.endswith('.types'):",
        "        continue",
        "    mod = importlib.import_module(modinfo.name)",
        "    UIMA_TYPE_TO_CLASS.update(getattr(mod, 'UIMA_TYPE_TO_CLASS', {}))",
        "",
        "def get_uima_model_class(type_name: str):",
        "    return UIMA_TYPE_TO_CLASS.get(type_name)",
        "",
        "__all__ = ['UIMA_TYPE_TO_CLASS', 'get_uima_model_class']",
        "",
    ]
    (output_root / "__init__.py").write_text("\n".join(root_lines), encoding="utf-8")

    return {
        "parsed_xml_files": parsed_files,
        "unique_types": len(types_by_name),
        "namespace_modules": len(module_to_types),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate namespace-mapped Pydantic models from UIMA XMLs")
    parser.add_argument("source_path", type=Path, help="Root path to recursively scan for UIMA typesystem XMLs")
    parser.add_argument("output_path", type=Path, help="Output package directory for generated Python modules")
    parser.add_argument("--no-clear", action="store_true", help="Do not clear output directory before generation")
    args = parser.parse_args()

    stats = generate_models(args.source_path, args.output_path, clear_output=not args.no_clear)
    print(f"parsed_xml_files={stats['parsed_xml_files']}")
    print(f"unique_types={stats['unique_types']}")
    print(f"namespace_modules={stats['namespace_modules']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
