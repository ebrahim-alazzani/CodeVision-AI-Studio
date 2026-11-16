import re
from typing import List

class SyntaxFixer:
    """
    Intelligent post-processor for extracted C# code.
    Fixes parenthesis matching, missing semicolons, brace balancing, and standard C# indentation.
    """

    def fix_script(self, code_lines: List[str]) -> List[str]:
        if not code_lines:
            return []

        fixed_lines = []
        for line in code_lines:
            line_str = line.strip()
            if not line_str:
                fixed_lines.append("")
                continue

            # Fix unclosed if/while/for/foreach parens
            line_str = self._fix_unclosed_control_parens(line_str)
            # Fix missing trailing semicolons
            line_str = self._fix_missing_semicolon(line_str)

            fixed_lines.append(line_str)

        # Balance class/method braces and re-indent
        fixed_lines = self._balance_braces_and_indent(fixed_lines)
        return fixed_lines

    def _fix_unclosed_control_parens(self, line: str) -> str:
        control_keywords = r'\b(if|while|for|foreach)\b'
        match = re.search(control_keywords, line)
        if match:
            open_parens = line.count('(')
            close_parens = line.count(')')
            if open_parens > close_parens:
                # Add missing closing parenthesis before opening brace or at line end
                if line.endswith('{'):
                    line = line[:-1].rstrip() + ')' * (open_parens - close_parens) + ' {'
                else:
                    line = line + ')' * (open_parens - close_parens)
        return line

    def _fix_missing_semicolon(self, line: str) -> str:
        # Don't add semicolon to comments, directives, attributes, keywords, braces
        if line.startswith('//') or line.startswith('#') or line.startswith('[') or line.startswith('using') or line.startswith('namespace'):
            return line
        if line.endswith('{') or line.endswith('}') or line.endswith(';') or line.endswith(':'):
            return line
        if re.search(r'\b(if|while|for|foreach|else|switch|case|default|class|struct|interface|enum|public|private|protected|internal|void|float|int|bool|string|Vector2|Vector3|Quaternion|Transform|Rigidbody|Animator)\b.*\(', line) and not '=' in line and not line.endswith(';'):
            # Looks like a method declaration or control structure
            return line

        # If it looks like an assignment, field declaration, return, or method call, ensure trailing semicolon
        if '=' in line or line.startswith('return') or line.endswith(')') or re.search(r'\b(Destroy|Instantiate|Debug\.Log|GetComponent|AddForce|SetBool|SetFloat|SetTrigger|PlayTargetAnim)\b', line):
            if not line.endswith(';') and not line.endswith('{') and not line.endswith('}'):
                return line + ';'

        return line

    def _balance_braces_and_indent(self, lines: List[str]) -> List[str]:
        open_count = sum(l.count('{') for l in lines)
        close_count = sum(l.count('}') for l in lines)

        # If missing closing braces, append them at the end
        if open_count > close_count:
            lines.extend(['}'] * (open_count - close_count))

        formatted = []
        indent_level = 0

        for line in lines:
            stripped = line.strip()
            if not stripped:
                formatted.append("")
                continue

            # Decrease indent before printing if line starts with closing brace
            closing_at_start = stripped.startswith('}')
            if closing_at_start:
                indent_level = max(0, indent_level - 1)

            indent_str = "    " * indent_level
            formatted.append(f"{indent_str}{stripped}")

            # Adjust indent level based on net braces in line (if not already handled at start)
            if not closing_at_start:
                net_braces = stripped.count('{') - stripped.count('}')
                indent_level = max(0, indent_level + net_braces)

        return formatted
