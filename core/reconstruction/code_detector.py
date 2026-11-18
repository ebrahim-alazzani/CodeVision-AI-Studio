"""
General Code Structure and Entry Point Detector for Multi-Language Pipelines.

Detects code constructs, file structures, and entry points across multiple programming
languages (Python, TypeScript, JavaScript, C++, C#, Rust, Go, Java, PHP, Dart,
Swift, Kotlin, SQL) using the extensible LanguageRegistry.

Part of CodeVision Phase 2 Multi-Language Architecture.
"""

import os
import re
from dataclasses import dataclass, field
from pathlib import PurePath
from typing import Dict, List, Optional, Set, Tuple, Union

from languages.builtin import create_default_registry
from languages.models import LanguageMatch, LanguageProfile
from languages.registry import LanguageRegistry


@dataclass
class CodeStructure:
    """Represents detected structural elements of a code snippet or file."""
    language: str
    primary_name: str
    file_name: str
    entry_points: List[str] = field(default_factory=list)
    classes: List[str] = field(default_factory=list)
    interfaces: List[str] = field(default_factory=list)
    functions: List[str] = field(default_factory=list)
    namespaces: List[str] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    confidence: float = 0.0
    evidence: List[str] = field(default_factory=list)


class CodeDetector:
    """Universal code entity and entry-point detector for multi-language pipelines."""

    # Language alias normalization
    LANGUAGE_ALIASES: Dict[str, str] = {
        "c#": "csharp",
        "cs": "csharp",
        "csharp": "csharp",
        "c++": "cpp",
        "cpp": "cpp",
        "cxx": "cpp",
        "py": "python",
        "python": "python",
        "python3": "python",
        "ts": "typescript",
        "typescript": "typescript",
        "js": "javascript",
        "javascript": "javascript",
        "node": "javascript",
        "rs": "rust",
        "rust": "rust",
        "go": "go",
        "golang": "go",
        "java": "java",
        "kt": "kotlin",
        "kotlin": "kotlin",
        "dart": "dart",
        "swift": "swift",
        "php": "php",
        "rb": "ruby",
        "ruby": "ruby",
        "sql": "sql",
        "c": "c",
    }

    # Breadcrumb file path pattern (IDE headers, tabs, file trees)
    _BREADCRUMB_PATTERN = re.compile(
        r'(?:>|/|\\|\b)([A-Za-z0-9_.\-]+?\.(?:cs|py|pyw|ts|tsx|js|jsx|mjs|cjs|cpp|cc|cxx|hpp|hh|c|h|rs|go|java|kt|kts|dart|swift|php|rb|sql))\b',
        re.IGNORECASE
    )

    # OCR cleanups for common identifier misreads
    _NAME_CORRECTIONS = [
        (r'^Gam[a-z]*anager$', 'GameManager'),
        (r'^Gan[a-z]*anager$', 'GameManager'),
        (r'^GaneManager$', 'GameManager'),
        (r'^Cam[a-z]*anager$', 'CameraManager'),
        (r'^Input[a-z]*anager$', 'InputManager'),
        (r'^Imput[a-z]*ager$', 'InputManager'),
        (r'^mputManager$', 'InputManager'),
        (r'^PlayerMover[a-z]*$', 'PlayerMovement'),
        (r'^CarC[a-z]*mera[a-z]*Contro[a-z]*$', 'CarCameraController'),
        (r'^CarContro[a-z]*$', 'CarController'),
        (r'^ShootingContro[a-z0-9]*$', 'ShootingController'),
        (r'^PoliceO[a-z]*ficer$', 'PoliceOfficer'),
        (r'^Wantedtevel$', 'WantedLevel'),
        (r'^WaypointE[a-z]*ditor$', 'WaypointEditor'),
        (r'^Main[a-z]*enu[a-z]*anager$', 'MainMenuManager'),
        (r'^Pause[a-z]*enu$', 'PauseMenu'),
        (r'^AlSpawner$', 'AISpawner'),
    ]

    # Non-meaningful identifier tokens to exclude
    _FALSE_POSITIVES: Set[str] = {
        "MonoBehaviour",
        "ScriptableObject",
        "Editor",
        "Program",
        "Script",
        "Object",
        "Class",
        "Function",
        "Def",
        "Interface",
        "Struct",
        "Const",
        "Var",
        "Let",
        "Export",
        "Default",
        "Import",
        "Package",
        "Return",
    }

    def __init__(self, registry: Optional[LanguageRegistry] = None) -> None:
        self._registry = registry or create_default_registry()

    @property
    def registry(self) -> LanguageRegistry:
        return self._registry

    def normalize_language_id(self, lang: Optional[str]) -> str:
        """Map user-supplied name or extension alias to registered language ID."""
        if not lang or lang.strip().lower() == "auto":
            return "auto"
        clean = lang.strip().lower()
        return self.LANGUAGE_ALIASES.get(clean, clean)

    def detect_language(self, source: str = "", filename: str = "") -> Optional[LanguageMatch]:
        """Detect language using the underlying LanguageRegistry."""
        return self._registry.detect(filename=filename or None, source=source)

    def detect_structure(
        self,
        lines: Union[List[str], str],
        language: Optional[str] = None,
        filename: Optional[str] = None
    ) -> CodeStructure:
        """
        Detect file structure, classes, functions, entry points, and suggested filename.
        Works across Python, TypeScript/JS, C++, Rust, Go, C#, Java, Dart, Swift, Kotlin, PHP, SQL.
        """
        raw_lines = lines if isinstance(lines, list) else lines.splitlines()
        text = "\n".join(raw_lines)
        stripped_lines = [ln.strip() for ln in raw_lines if ln.strip()]

        # 1. Resolve Language
        resolved_lang = self.normalize_language_id(language)
        evidence_list: List[str] = []
        lang_match: Optional[LanguageMatch] = None

        # Check breadcrumbs first for strong filename & extension evidence
        breadcrumb_file = self._find_breadcrumb_filename(raw_lines)
        effective_filename = filename or breadcrumb_file

        if resolved_lang == "auto" or not resolved_lang:
            if effective_filename:
                lang_match = self._registry.detect(filename=effective_filename, source=text)
            else:
                lang_match = self._registry.detect(source=text)

            if lang_match:
                resolved_lang = lang_match.profile.language_id
                evidence_list.extend(lang_match.evidence)
            else:
                resolved_lang = "generic"
        else:
            profile = self._registry.get(resolved_lang)
            if profile:
                evidence_list.append(f"specified:{resolved_lang}")
            else:
                resolved_lang = self.LANGUAGE_ALIASES.get(resolved_lang, resolved_lang)

        # 2. Extract structural entities according to language
        entry_points: List[str] = []
        classes: List[str] = []
        interfaces: List[str] = []
        functions: List[str] = []
        namespaces: List[str] = []
        imports: List[str] = []

        if resolved_lang == "python":
            self._scan_python(raw_lines, entry_points, classes, functions, imports)
        elif resolved_lang in ("typescript", "javascript"):
            self._scan_typescript_javascript(raw_lines, entry_points, classes, interfaces, functions, imports)
        elif resolved_lang in ("cpp", "c"):
            self._scan_cpp(raw_lines, entry_points, classes, functions, namespaces, imports)
        elif resolved_lang == "rust":
            self._scan_rust(raw_lines, entry_points, classes, interfaces, functions, namespaces, imports)
        elif resolved_lang == "go":
            self._scan_go(raw_lines, entry_points, classes, interfaces, functions, namespaces, imports)
        elif resolved_lang == "csharp":
            self._scan_csharp(raw_lines, entry_points, classes, interfaces, functions, namespaces, imports)
        else:
            self._scan_generic(raw_lines, entry_points, classes, interfaces, functions, namespaces, imports)

        # 3. Determine Primary Symbol and Suggested Filename
        primary_name, suggested_file = self._determine_names(
            resolved_lang=resolved_lang,
            effective_filename=effective_filename,
            entry_points=entry_points,
            classes=classes,
            interfaces=interfaces,
            functions=functions,
            namespaces=namespaces
        )

        # 4. Compute Confidence Mathematically
        profile = self._registry.get(resolved_lang)
        confidence = self._compute_confidence(
            profile=profile,
            text=text,
            entry_points=entry_points,
            classes=classes,
            interfaces=interfaces,
            functions=functions,
            imports=imports,
            lang_match=lang_match,
            has_breadcrumb=bool(breadcrumb_file)
        )

        return CodeStructure(
            language=resolved_lang,
            primary_name=primary_name,
            file_name=suggested_file,
            entry_points=entry_points,
            classes=classes,
            interfaces=interfaces,
            functions=functions,
            namespaces=namespaces,
            imports=imports,
            confidence=round(confidence, 3),
            evidence=evidence_list
        )

    def detect_entry_points(self, lines: Union[List[str], str], language: Optional[str] = None) -> List[str]:
        """Convenience method to return detected entry points."""
        structure = self.detect_structure(lines, language=language)
        return structure.entry_points

    def detect_primary_symbol(self, lines: Union[List[str], str], language: Optional[str] = None) -> str:
        """Convenience method to return the primary symbol name."""
        structure = self.detect_structure(lines, language=language)
        return structure.primary_name

    def detect_file_name(
        self,
        lines: Union[List[str], str],
        language: Optional[str] = None,
        fallback_stem: str = "ExtractedCode"
    ) -> str:
        """Convenience method to return the recommended file name."""
        structure = self.detect_structure(lines, language=language)
        return structure.file_name or f"{fallback_stem}.txt"

    def detect_class_name(self, all_lines: List[str]) -> str:
        """Drop-in enhancement for ClassDetector.detect_class_name."""
        structure = self.detect_structure(all_lines)
        if structure.classes:
            return structure.classes[0]
        if structure.primary_name and structure.primary_name not in ("main", "script", "app", "index", "ExtractedScript"):
            return structure.primary_name
        return "ExtractedScript"

    def detect_frame_class(self, cleaned_lines: List[str], raw_text: str = "") -> Optional[str]:
        """Drop-in enhancement for ClassDetector.detect_frame_class."""
        lines = []
        if raw_text:
            lines.extend(raw_text.splitlines())
        lines.extend(cleaned_lines)

        structure = self.detect_structure(lines)
        if structure.classes:
            return structure.classes[0]
        if structure.primary_name and structure.primary_name not in ("main", "script", "app", "index", "ExtractedScript"):
            return structure.primary_name
        return None

    def normalize_name(self, name: str) -> str:
        """Clean and normalize OCR-scanned identifiers."""
        cleaned = re.sub(r'[^A-Za-z0-9_]', '', name or "")
        if not cleaned:
            return ""
        for pattern, replacement in self._NAME_CORRECTIONS:
            if re.match(pattern, cleaned, re.IGNORECASE):
                return replacement
        return cleaned

    normalize_class_name = normalize_name

    def is_valid_name(self, name: str) -> bool:
        """Validate whether an identifier name is non-empty, well-formed, and not a keyword."""
        if not name or name in self._FALSE_POSITIVES:
            return False
        if len(name) < 2 or len(name) > 64:
            return False
        if not re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', name):
            return False
        letters = re.findall(r'[A-Za-z]', name)
        if letters and len(letters) > 10:
            upper_ratio = sum(1 for c in letters if c.isupper()) / len(letters)
            if upper_ratio > 0.85:
                return False
        return True

    is_valid_class_name = is_valid_name

    # -------------------------------------------------------------------------
    # Language-Specific Scanners
    # -------------------------------------------------------------------------

    def _scan_python(
        self,
        lines: List[str],
        entry_points: List[str],
        classes: List[str],
        functions: List[str],
        imports: List[str]
    ) -> None:
        for line in lines:
            stripped = line.strip()
            # Entry points
            if re.search(r'if\s+__name__\s*==\s*[\'"]__main__[\'"]\s*:', stripped):
                entry_points.append("if __name__ == '__main__':")
            elif re.match(r'def\s+main\s*\([^)]*\)\s*:', stripped):
                entry_points.append("def main(...)")
                if "main" not in functions:
                    functions.append("main")

            # Classes
            m_class = re.match(r'class\s+([A-Za-z_][A-Za-z0-9_]*)(?:\s*\([^)]*\))?\s*:', stripped)
            if m_class:
                c_name = self.normalize_name(m_class.group(1))
                if self.is_valid_name(c_name) and c_name not in classes:
                    classes.append(c_name)

            # Functions
            m_func = re.match(r'def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(', stripped)
            if m_func:
                f_name = self.normalize_name(m_func.group(1))
                if self.is_valid_name(f_name) and f_name not in functions:
                    functions.append(f_name)

            # Imports
            if re.match(r'^(?:import\s+[\w.]+|from\s+[\w.]+\s+import)', stripped):
                imports.append(stripped)

    def _scan_typescript_javascript(
        self,
        lines: List[str],
        entry_points: List[str],
        classes: List[str],
        interfaces: List[str],
        functions: List[str],
        imports: List[str]
    ) -> None:
        for line in lines:
            stripped = line.strip()
            # Entry points / Exports
            if re.search(r'\bexport\s+default\b', stripped):
                entry_points.append(stripped)
            if re.search(r'\bfunction\s+main\s*\(', stripped):
                entry_points.append("function main(...)")

            # Classes
            m_class = re.search(r'\bclass\s+([A-Za-z_][A-Za-z0-9_]*)', stripped)
            if m_class:
                c_name = self.normalize_name(m_class.group(1))
                if self.is_valid_name(c_name) and c_name not in classes:
                    classes.append(c_name)

            # Interfaces and Types
            m_iface = re.search(r'\binterface\s+([A-Za-z_][A-Za-z0-9_]*)', stripped)
            if m_iface:
                i_name = self.normalize_name(m_iface.group(1))
                if self.is_valid_name(i_name) and i_name not in interfaces:
                    interfaces.append(i_name)

            m_type = re.search(r'\btype\s+([A-Za-z_][A-Za-z0-9_]*)\s*=', stripped)
            if m_type:
                t_name = self.normalize_name(m_type.group(1))
                if self.is_valid_name(t_name) and t_name not in interfaces:
                    interfaces.append(t_name)

            # Functions
            m_func = re.search(r'\b(?:function\s+([A-Za-z_][A-Za-z0-9_]*)|const\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>)', stripped)
            if m_func:
                fn = self.normalize_name(m_func.group(1) or m_func.group(2) or "")
                if self.is_valid_name(fn) and fn not in functions:
                    functions.append(fn)

            # Imports
            if re.match(r'^(?:import\s+|const\s+.+\s*=\s*require\()', stripped):
                imports.append(stripped)

    def _scan_cpp(
        self,
        lines: List[str],
        entry_points: List[str],
        classes: List[str],
        functions: List[str],
        namespaces: List[str],
        imports: List[str]
    ) -> None:
        for line in lines:
            stripped = line.strip()
            # Entry points
            if re.search(r'\bint\s+main\s*\(', stripped) or re.search(r'\bvoid\s+main\s*\(', stripped):
                entry_points.append("int main(...)")

            # Namespaces
            m_ns = re.search(r'\bnamespace\s+([A-Za-z_][A-Za-z0-9_]*)', stripped)
            if m_ns:
                ns = self.normalize_name(m_ns.group(1))
                if self.is_valid_name(ns) and ns not in namespaces:
                    namespaces.append(ns)

            # Classes and Structs
            m_class = re.search(r'\b(?:class|struct)\s+([A-Za-z_][A-Za-z0-9_]*)', stripped)
            if m_class:
                c_name = self.normalize_name(m_class.group(1))
                if self.is_valid_name(c_name) and c_name not in classes:
                    classes.append(c_name)

            # Functions
            m_fn = re.search(r'\b(?:void|int|float|double|bool|auto|std::string)\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(', stripped)
            if m_fn:
                fn = self.normalize_name(m_fn.group(1))
                if self.is_valid_name(fn) and fn not in functions and fn != "main":
                    functions.append(fn)

            # Includes
            if stripped.startswith("#include"):
                imports.append(stripped)

    def _scan_rust(
        self,
        lines: List[str],
        entry_points: List[str],
        classes: List[str],
        interfaces: List[str],
        functions: List[str],
        namespaces: List[str],
        imports: List[str]
    ) -> None:
        for line in lines:
            stripped = line.strip()
            # Entry point
            if re.search(r'\bfn\s+main\s*\(', stripped):
                entry_points.append("fn main(...)")

            # Structs and Enums
            m_struct = re.search(r'\b(?:pub\s+)?(?:struct|enum)\s+([A-Za-z_][A-Za-z0-9_]*)', stripped)
            if m_struct:
                st = self.normalize_name(m_struct.group(1))
                if self.is_valid_name(st) and st not in classes:
                    classes.append(st)

            # Traits
            m_trait = re.search(r'\b(?:pub\s+)?trait\s+([A-Za-z_][A-Za-z0-9_]*)', stripped)
            if m_trait:
                tr = self.normalize_name(m_trait.group(1))
                if self.is_valid_name(tr) and tr not in interfaces:
                    interfaces.append(tr)

            # Impls
            m_impl = re.search(r'\bimpl(?:\s+<[^>]+>)?\s+(?:(\w+)\s+for\s+)?([A-Za-z_][A-Za-z0-9_]*)', stripped)
            if m_impl:
                target = self.normalize_name(m_impl.group(2))
                if self.is_valid_name(target) and target not in classes:
                    classes.append(target)

            # Functions
            m_fn = re.search(r'\b(?:pub\s+)?fn\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(', stripped)
            if m_fn:
                fn = self.normalize_name(m_fn.group(1))
                if self.is_valid_name(fn) and fn not in functions and fn != "main":
                    functions.append(fn)

            # Modules
            m_mod = re.search(r'\b(?:pub\s+)?mod\s+([A-Za-z_][A-Za-z0-9_]*)', stripped)
            if m_mod:
                mod = self.normalize_name(m_mod.group(1))
                if self.is_valid_name(mod) and mod not in namespaces:
                    namespaces.append(mod)

            # Use
            if re.match(r'^(?:pub\s+)?use\s+', stripped):
                imports.append(stripped)

    def _scan_go(
        self,
        lines: List[str],
        entry_points: List[str],
        classes: List[str],
        interfaces: List[str],
        functions: List[str],
        namespaces: List[str],
        imports: List[str]
    ) -> None:
        for line in lines:
            stripped = line.strip()
            # Package
            m_pkg = re.match(r'package\s+([A-Za-z_][A-Za-z0-9_]*)', stripped)
            if m_pkg:
                pkg = self.normalize_name(m_pkg.group(1))
                if self.is_valid_name(pkg) and pkg not in namespaces:
                    namespaces.append(pkg)

            # Entry point
            if re.search(r'\bfunc\s+main\s*\(\s*\)', stripped):
                entry_points.append("func main()")

            # Structs
            m_struct = re.search(r'\btype\s+([A-Za-z_][A-Za-z0-9_]*)\s+struct\b', stripped)
            if m_struct:
                st = self.normalize_name(m_struct.group(1))
                if self.is_valid_name(st) and st not in classes:
                    classes.append(st)

            # Interfaces
            m_iface = re.search(r'\btype\s+([A-Za-z_][A-Za-z0-9_]*)\s+interface\b', stripped)
            if m_iface:
                iface = self.normalize_name(m_iface.group(1))
                if self.is_valid_name(iface) and iface not in interfaces:
                    interfaces.append(iface)

            # Functions
            m_fn = re.search(r'\bfunc\s+(?:\([^)]+\)\s*)?([A-Za-z_][A-Za-z0-9_]*)\s*\(', stripped)
            if m_fn:
                fn = self.normalize_name(m_fn.group(1))
                if self.is_valid_name(fn) and fn not in functions and fn != "main":
                    functions.append(fn)

            # Imports
            if stripped.startswith("import"):
                imports.append(stripped)

    def _scan_csharp(
        self,
        lines: List[str],
        entry_points: List[str],
        classes: List[str],
        interfaces: List[str],
        functions: List[str],
        namespaces: List[str],
        imports: List[str]
    ) -> None:
        for line in lines:
            stripped = line.strip()
            # Entry points
            if re.search(r'\bstatic\s+(?:async\s+Task|void|int)\s+Main\s*\(', stripped):
                entry_points.append("static void Main(...)")

            # Namespaces
            m_ns = re.search(r'\bnamespace\s+([A-Za-z_][A-Za-z0-9_.]*)', stripped)
            if m_ns:
                ns = m_ns.group(1).strip()
                if ns and ns not in namespaces:
                    namespaces.append(ns)

            # Classes and Structs
            m_class = re.search(r'\b(?:public|private|protected|internal)?\s*(?:class|struct)\s+([A-Za-z_][A-Za-z0-9_]*)', stripped)
            if m_class:
                c_name = self.normalize_name(m_class.group(1))
                if self.is_valid_name(c_name) and c_name not in classes:
                    classes.append(c_name)

            # Interfaces
            m_iface = re.search(r'\b(?:public|private|protected|internal)?\s*interface\s+([A-Za-z_][A-Za-z0-9_]*)', stripped)
            if m_iface:
                i_name = self.normalize_name(m_iface.group(1))
                if self.is_valid_name(i_name) and i_name not in interfaces:
                    interfaces.append(i_name)

            # Usings
            if stripped.startswith("using ") and stripped.endswith(";"):
                imports.append(stripped)

    def _scan_generic(
        self,
        lines: List[str],
        entry_points: List[str],
        classes: List[str],
        interfaces: List[str],
        functions: List[str],
        namespaces: List[str],
        imports: List[str]
    ) -> None:
        for line in lines:
            stripped = line.strip()
            # General class
            m_class = re.search(r'\bclass\s+([A-Za-z_][A-Za-z0-9_]*)', stripped)
            if m_class:
                c_name = self.normalize_name(m_class.group(1))
                if self.is_valid_name(c_name) and c_name not in classes:
                    classes.append(c_name)

            # General function
            m_fn = re.search(r'\b(?:def|func|function|fun|fn)\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(', stripped)
            if m_fn:
                fn = self.normalize_name(m_fn.group(1))
                if self.is_valid_name(fn) and fn not in functions:
                    functions.append(fn)

            # General entry
            if re.search(r'\b(?:main|Main)\s*\(', stripped):
                entry_points.append("main()")

    # -------------------------------------------------------------------------
    # Name Determination and Helpers
    # -------------------------------------------------------------------------

    def _find_breadcrumb_filename(self, lines: List[str]) -> Optional[str]:
        for line in lines:
            if '>' in line or 'Assets' in line or '/' in line or '\\' in line:
                m = self._BREADCRUMB_PATTERN.search(line)
                if m:
                    return m.group(1)
        return None

    PRIMARY_EXTENSIONS: Dict[str, str] = {
        "csharp": ".cs",
        "python": ".py",
        "typescript": ".ts",
        "javascript": ".js",
        "cpp": ".cpp",
        "c": ".c",
        "rust": ".rs",
        "go": ".go",
        "java": ".java",
        "kotlin": ".kt",
        "dart": ".dart",
        "swift": ".swift",
        "php": ".php",
        "ruby": ".rb",
        "sql": ".sql",
    }

    def _determine_names(
        self,
        resolved_lang: str,
        effective_filename: Optional[str],
        entry_points: List[str],
        classes: List[str],
        interfaces: List[str],
        functions: List[str],
        namespaces: List[str]
    ) -> Tuple[str, str]:
        profile = self._registry.get(resolved_lang)
        ext = self.PRIMARY_EXTENSIONS.get(
            resolved_lang,
            f".{profile.extensions[0].lstrip('.')}" if (profile and profile.extensions) else ".txt"
        )

        # If we have an exact breadcrumb filename, respect it
        if effective_filename:
            path_obj = PurePath(effective_filename)
            stem = path_obj.stem
            return stem, path_obj.name

        # Primary symbol preference: classes -> interfaces -> entry_points -> functions -> namespaces
        primary = ""
        suggested = ""

        if classes:
            primary = classes[0]
            if resolved_lang == "go":
                suggested = f"{primary.lower()}{ext}"
            else:
                suggested = f"{primary}{ext}"
        elif interfaces:
            primary = interfaces[0]
            suggested = f"{primary}{ext}"
        elif entry_points:
            primary = "main"
            suggested = f"main{ext}"
        elif functions:
            primary = functions[0]
            suggested = f"{primary}{ext}"
        elif namespaces:
            primary = namespaces[0]
            suggested = f"{primary}{ext}"
        else:
            primary = "ExtractedCode"
            suggested = f"ExtractedCode{ext}"

        return primary, suggested

    def _compute_confidence(
        self,
        profile: Optional[LanguageProfile],
        text: str,
        entry_points: List[str],
        classes: List[str],
        interfaces: List[str],
        functions: List[str],
        imports: List[str],
        lang_match: Optional[LanguageMatch],
        has_breadcrumb: bool
    ) -> float:
        """
        Mathematically derive confidence in [0.0, 1.0] from keyword matches,
        structural symbols, language match score, and presence of file breadcrumb.
        """
        if not text.strip():
            return 0.0

        structural_count = len(entry_points) + len(classes) + len(interfaces) + len(functions) + len(imports)
        if structural_count == 0 and not lang_match:
            return 0.0

        # 1. Structural score (0.0 to 0.4)
        structure_score = min(0.40, (len(entry_points) * 0.15) + (len(classes) * 0.15) + (len(functions) * 0.05) + (len(imports) * 0.05))

        # 2. Language match / keyword score (0.0 to 0.45)
        lang_score = 0.0
        if lang_match:
            lang_score = min(0.45, lang_match.confidence * 0.45)
        elif profile:
            matched_kws = sum(
                1 for kw in profile.keywords
                if re.search(r"(?<!\w)" + re.escape(kw) + r"(?!\w)", text.lower())
            )
            kw_ratio = matched_kws / max(1, len(profile.keywords))
            lang_score = min(0.45, kw_ratio * 0.60)

        # 3. Breadcrumb bonus (0.0 to 0.14)
        breadcrumb_score = 0.14 if has_breadcrumb else 0.0

        total = structure_score + lang_score + breadcrumb_score
        return max(0.0, min(0.99, total))
