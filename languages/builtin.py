"""Initial language metadata pack; adding a profile needs no core edits."""

from .models import LanguageProfile
from .registry import LanguageRegistry


def create_default_registry() -> LanguageRegistry:
    profiles = [
        LanguageProfile("csharp", "C#", ("cs",), ("using", "namespace", "class", "public", "void"),
                        (r"\busing\s+[\w.]+\s*;", r"\bnamespace\s+[\w.]+", r"\b(class|struct|interface)\s+\w+")),
        LanguageProfile("python", "Python", ("py", "pyw"), ("def", "self", "import", "elif", "lambda"),
                        (r"^\s*def\s+\w+\s*\([^)]*\)\s*:", r"^\s*if\s+.+:\s*$", r"^\s*from\s+\S+\s+import\s+")),
        LanguageProfile("javascript", "JavaScript", ("js", "jsx", "mjs", "cjs"), ("const", "let", "var", "function", "console"),
                        (r"\bfunction\s+\w+\s*\(", r"\b(console|window|document)\.", r"=>")),
        LanguageProfile("typescript", "TypeScript", ("ts", "tsx"), ("interface", "type", "readonly", "implements"),
                        (r"\binterface\s+\w+", r"\b\w+\s*:\s*(string|number|boolean)\b", r"\bas\s+const\b")),
        LanguageProfile("java", "Java", ("java",), ("public", "static", "void", "package", "import"),
                        (r"\bpublic\s+(class|interface|enum)\s+\w+", r"\bSystem\.out\.print")),
        LanguageProfile("c", "C", ("c", "h"), ("#include", "printf", "sizeof", "typedef"),
                        (r"#\s*include\s*<[^>]+>", r"\bint\s+main\s*\(")),
        LanguageProfile("cpp", "C++", ("cc", "cpp", "cxx", "hpp", "hh", "hxx", "h"), ("namespace", "std", "template", "cout", "class"),
                        (r"#\s*include\s*<iostream>", r"\bstd::", r"\btemplate\s*<")),
        LanguageProfile("dart", "Dart", ("dart",), ("void", "final", "const", "widget", "import"),
                        (r"\bvoid\s+main\s*\(", r"\bclass\s+\w+\s+extends\s+")),
        LanguageProfile("go", "Go", ("go",), ("package", "func", "defer", "go", "chan"),
                        (r"^\s*package\s+\w+", r"\bfunc\s+(\([^)]*\)\s*)?\w+\s*\(")),
        LanguageProfile("rust", "Rust", ("rs",), ("fn", "let", "mut", "impl", "pub"),
                        (r"\bfn\s+\w+\s*\(", r"\blet\s+mut\s+", r"\bimpl\s+\w+")),
        LanguageProfile("php", "PHP", ("php",), ("echo", "namespace", "function", "public", "class"),
                        (r"<\?php", r"\$[A-Za-z_]\w*\s*=")),
        LanguageProfile("ruby", "Ruby", ("rb",), ("def", "end", "puts", "module", "require"),
                        (r"^\s*def\s+\w+", r"^\s*class\s+\w+", r"^\s*require\s+")),
        LanguageProfile("swift", "Swift", ("swift",), ("func", "let", "var", "guard", "import"),
                        (r"\bfunc\s+\w+\s*\(", r"\bguard\s+.+\s+else\b", r"\bimport\s+SwiftUI\b")),
        LanguageProfile("kotlin", "Kotlin", ("kt", "kts"), ("fun", "val", "var", "when", "object"),
                        (r"\bfun\s+(\w+\s*\([^)]*\)|main\s*\()", r"\bdata\s+class\s+\w+")),
        LanguageProfile("sql", "SQL", ("sql",), ("select", "from", "where", "insert", "create"),
                        (r"\bSELECT\b.+\bFROM\b", r"\bCREATE\s+TABLE\b")),
    ]
    return LanguageRegistry(profiles)
