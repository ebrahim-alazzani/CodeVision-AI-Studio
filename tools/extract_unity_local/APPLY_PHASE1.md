# Apply phase 1

Copy the `languages/`, `tests/`, and `docs/` directories into the CodeVision
project root. Existing extractor modules are intentionally untouched.

From the project root, run:

```powershell
python -m unittest discover -s tests -v
```

Example:

```python
from languages.builtin import create_default_registry

registry = create_default_registry()
match = registry.detect("lesson/main.py")
if match:
    print(match.profile.display_name, match.confidence, match.evidence)
```
