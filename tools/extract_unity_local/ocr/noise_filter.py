"""
IDE / Visual Studio noise filter and OCR typo corrector.

Responsible for:
1. Removing IDE UI elements (menus, status bars, breadcrumbs, autocomplete).
2. Stripping OCR-injected line numbers and cursor artifacts.
3. Correcting common OCR misreadings of C# / Unity keywords.

Follows Single Responsibility Principle — only handles text cleaning.
"""

import re
from typing import Optional, List, Tuple


class NoiseFilter:
    """Filters IDE noise and corrects OCR typos from extracted text."""

    # ─── OCR Typo Correction Rules ─────────────────────────────────
    # Format: (regex_pattern, replacement_string)
    OCR_CORRECTIONS: List[Tuple[str, str]] = [
        # Unity / C# keywords & Namespaces
        (r'\bUnityéngine\b',                'UnityEngine'),
        (r'\bUnityengine\b',                'UnityEngine'),
        (r'\bMonoBchaviour\b',              'MonoBehaviour'),
        (r'\bMonofehaviour\b',              'MonoBehaviour'),
        (r'\bNonoBehaviour\b',              'MonoBehaviour'),
        (r'\bHonodchaviour\b',              'MonoBehaviour'),
        (r'\bHonotehaviour\b',              'MonoBehaviour'),
        (r'\bMonoiehaviour\b',              'MonoBehaviour'),
        (r'\bMonodchaviour\b',              'MonoBehaviour'),
        (r'\bMono¥chavio\b',                'MonoBehaviour'),
        (r'\bSystem\.Ccollections\b',       'System.Collections'),
        (r'\bSystem\.collections\b',        'System.Collections'),
        (r'\bSystem\.Collections\.\s*Generic\b', 'System.Collections.Generic'),

        # Header attribute
        (r'\[f[a-z]*Header\(',          '[Header('),
        (r'\[fleader\(',                '[Header('),
        (r'\[fileader\(',               '[Header('),
        (r'\[fieader\(',                '[Header('),
        (r'\[fHeader\(',                '[Header('),

        # Common OCR typos for Managers & Classes
        (r'\bganeHanager\b',            'gameManager'),
        (r'\bGamelianager\b',           'GameManager'),
        (r'\bGametianager\b',           'GameManager'),
        (r'\bGanetanager\b',            'GameManager'),
        (r'\bganettanager\b',           'gameManager'),
        (r'\bganellanager\b',           'gameManager'),
        (r'\bgamevianager\b',           'gameManager'),
        (r'\binpuptlanager\b',          'inputManager'),
        (r'\btnputManager\b',           'inputManager'),
        (r'\bInputtanager\b',           'InputManager'),
        (r'\bFindObjectOfTypectnputsanager\b', 'FindObjectOfType<InputManager>'),
        (r'\bFindobjectot Typeccamerianager\b', 'FindObjectOfType<CameraManager>'),
        (r'\bFandoojectottype<GameMianager>\b', 'FindObjectOfType<GameManager>'),
        (r'\bFandoojectotiype<GameManager>\b', 'FindObjectOfType<GameManager>'),
        (r'\bFingupjectut lype<anamatormanager>\b', 'FindObjectOfType<AnimatorManager>'),
        (r'\banjmatorManager\b',        'animatorManager'),
        (r'\banimatorMenager\b',        'animatorManager'),
        (r'\bFindobjectofType\b',       'FindObjectOfType'),
        (r'\bFindobjectOfType\b',       'FindObjectOfType'),
        (r'\bFindObjectoftype\b',       'FindObjectOfType'),

        # GameObject / Prefab OCR Typos
        (r'\bGaneObject\b',             'GameObject'),
        (r'\bGameobject(?!Prefab)',     'GameObject'),
        (r'\bGame0bject\b',             'GameObject'),
        (r'\bgameob ject\b',            'gameObject'),
        (r'\bgame0bject\b',             'gameObject'),
        (r'\bEamObject\b',              'camObject'),
        (r'\bEanObJeet\b',              'camObject'),
        (r'\bcanObject\b',              'camObject'),
        (r'\bcamobject\b',              'camObject'),
        (r'\bcambject\b',               'camObject'),
        (r'\bcamdbject\b',              'camObject'),
        (r'\bpistolGamedbject\b',       'pistolGameObject'),
        (r'\bakmGamedbject\b',          'akmGameObject'),
        (r'\bm416Gamedbject\b',         'm416GameObject'),
        (r'\bpistolGamecbject\b',       'pistolGameObject'),
        (r'\bpistolGamebject\b',        'pistolGameObject'),
        (r'\bpilstolGameObject\b',      'pistolGameObject'),
        (r'\bpistolGameobjectPrefab\b', 'pistolGameObjectPrefab'),
        (r'\bakmGameObjectPrefab\b',    'akmGameObjectPrefab'),
        (r'\bm416GameObjectPrefab\b',   'm416GameObjectPrefab'),
        (r'\bpistorrrefab\b',          'pistolPrefab'),
        (r'\bpistorPrefab\b',           'pistolPrefab'),
        (r'\bmai6Prefab\b',            'm416Prefab'),
        (r'\bmaigprefab\b',            'm416Prefab'),
        (r'\bmai6prefab\b',            'm416Prefab'),
        (r'\bmaisprefab\b',            'm416Prefab'),
        (r'\bm4iepbjectPrefab\b',      'm416GameObjectPrefab'),
        (r'\bm4i6Prefab\b',            'm416Prefab'),
        (r'\bpaseelPrefab\b',          'm416Prefab'),

        # Bool field & variable OCR typos
        (r'\briflelactive\b',          'rifle1Active'),
        (r'\brifletactive\b',          'rifle1Active'),
        (r'\briflelaActive\b',         'rifle1Active'),
        (r'\bniflgaActive\b',          'rifle1Active'),
        (r'\brifleiActive\b',          'rifle1Active'),
        (r'\brifleiactive\b',          'rifle1Active'),
        (r'\bPifletActive\b',          'rifle1Active'),
        (r'\brifletctive\b',           'rifle1Active'),
        (r'\brifletdctive\b',          'rifle1Active'),
        (r'\brifletaActive\b',         'rifle1Active'),
        (r'\briflezactive\b',          'rifle2Active'),
        (r'\briflezActive\b',          'rifle2Active'),
        (r'\bmifleaActivel\b',         'rifle2Active'),
        (r'\briflezactives\b',         'rifle2Active'),
        (r'\braflezactive\b',          'rifle2Active'),
        (r'\briflesactive\b',          'rifle3Active'),
        (r'\brifle3active\b',          'rifle3Active'),
        (r'\bniflesactive\b',          'rifle3Active'),
        (r'\briflesActive\b',          'rifle3Active'),
        (r'\bpiFlgsActivel\b',         'rifle3Active'),
        (r'\bRAlRLEsAEEIVe!\b',        'rifle3Active'),
        (r'\bInifle2active\b',         '!rifle2Active'),
        (r'\bIrifle1Active\b',         '!rifle1Active'),
        (r'\bIrifle2Active\b',         '!rifle2Active'),
        (r'\bIrifle3Active\b',         '!rifle3Active'),
        (r'\blrifle1Active\b',         '!rifle1Active'),
        (r'\blrifle2Active\b',         '!rifle2Active'),
        (r'\blrifle3Active\b',         '!rifle3Active'),
        (r'\bIdestinationReached\b',    '!destinationReached'),

        # Camera & UI Text OCR Typos
        (r'\bcanera\b',                 'camera'),
        (r'\bCanera\b',                 'Camera'),
        (r'\bsecondaryCanera\b',        'secondaryCamera'),
        (r'\bplayertoney\b',            'playerMoney'),
        (r'\bplayertoneyText\b',        'playerMoneyText'),
        (r'\bplayerMoneyText\.text\b',  'playerMoneyText.text'),
        (r'\bm416Inage\b',              'm416Image'),
        (r'\bmai6tmage\b',              'm416Image'),
        (r'\bma16Image\b',              'm416Image'),
        (r'\bma16tmage\b',              'm416Image'),
        (r'\bndi6Image\b',              'm416Image'),
        (r'\bpistollImage\b',           'pistolImage'),
        (r'\bFistImage\b',              'fistImage'),
        (r'\bpissdon3area\b',           'mission3Area'),
        (r'\bfnissdon3area\b',          'mission3Area'),
        (r'\bnissdon3area\b',           'mission3Area'),

        # Methods / Functions OCR Typos
        (r'\bsetactive\(',              'SetActive('),
        (r'\bSetactive\(',              'SetActive('),
        (r'\bsetgool\(',                'SetBool('),
        (r'\bSetGool\(',                'SetBool('),
        (r'\bGetcomponent\b',           'GetComponent'),
        (r'\bSetmai16\(\)',             'SetM416()'),
        (r'\bsetnaas\(\)',              'SetM416()'),
        (r'\bSetma16\(\)',              'SetM416()'),
        (r'\bSetaKH\(\)',               'SetAKM()'),
        (r'\bSetaKn\(\)',               'SetAKM()'),
        (r'\bNovecamera\(\)',           'MoveCamera()'),

        # Header attribute fixes
        (r'\[Header\("Player Money and kills"\)/\]\]',
         '[Header("Player Money and Kills")]'),
        (r'\[Header\("Player Money and kilf"\)\]\)',
         '[Header("Player Money and Kills")]'),

        # Common Unity/C# OCR glitches & Operators
        (r'GetComponent\s+<',           'GetComponent<'),
        (r'inputManager\. vertical Input', 'inputManager.verticalInput'),
        (r'horizontalinput',            'horizontalInput'),
        (r'verticalinput',              'verticalInput'),
        (r'verticaltnput',              'verticalInput'),
        (r'moveanount',                 'moveAmount'),
        (r'issprinting',                'isSprinting'),
        (r'istnteracting',              'isInteracting'),
        (r'targetDiffection',           'targetDirection'),
        (r'movenentVelocity',           'movementVelocity'),
        (r'HandleAli',                  'HandleAll'),
        (r'HandleAl1',                  'HandleAll'),
        (r'LookRotation\s+\(',          'LookRotation('),
        (r'transform\. forward',        'transform.forward'),
        (r'playerRigidbody\. velocity', 'playerRigidbody.velocity'),
        (r'\|\s*=',                     '!='),
        (r'I\s*=',                      '!='),
        (r'1\s*=',                      '!='),
    ]

    # ─── IDE UI Noise Patterns (lines matching these are discarded) ──
    UI_NOISE_PATTERNS: List[str] = [
        r'^.*File\s+Edit.*Selection.*View.*$',
        r'^\s*﻿?>\s+file\s+Edit.*$',
        r'^.*Restricted\s+Mode.*$',
        r'^.*Spaces:\d+.*$',
        r'^.*UTF-8.*CRLF.*$',
        r'^.*Ln\s*\d+.*Col\s*\d+.*$',
        r'^.*Button Handler \(Script\).*$',
        r'^.*Tag \(Unite Layer Dateuit.*$',
        r'^.*MonoBehaviour Unity MonoBehaviour.*$',
        r'^.*fact xunit Test!.*$',
        r'^.*using sel 4 a Alga lpNvonoaas.*$',
        r'^.*abe\.\s*a\s*=\s*B.*$',
        r'^.*rch\.\s*deme\s*=.*$',
        r'^.*namespace FileScopedNamespace.*$',

        # VS autocomplete / intellisense suggestions
        r'^.*OnParticlecollision.*MonoBehaviour.*$',
        r'^.*OnApplicationPause.*$',
        r'^.*OnApplicationFocus.*$',
        r'^.*OnPlayerDisconnected.*$',
        r'^.*OnParticleTrigger.*$',
        r'^.*OnPostRender.*$',
        r'^.*OnPreCull.*$',
        r'^.*OnPreRender.*$',
        r'^.*OnRenderObject.*$',
        r'^.*OnAudioFilterRead.*$',
        r'^.*OnAnimatorIK.*$',
        r'^.*MonoBehaviour\s+On\w+.*$',
        r'^.*MonoBehaviour\s+Reset.*$',
        r'^.*Honotehaviour\s+onapplication.*$',

        # IDE tab / breadcrumb / random garble
        r'^\s*\(C\)\s+©\s+Game.*$',
        r'^\s*\(Q\)\s+©\s+Same.*$',
        r'^\s*\(D\)\s+©\s+Game.*$',
        r'^\s*we\s+ee\s+re.*$',
        r'^\s*ere\s+i\}.*$',
        r'^\s*Py\s+oem.*$',
        r'^\s*Py\s+OSS.*$',
        r'^\s*wy\s+Cee.*$',
        r'^\s*wy\s+Cer.*$',
        r'^\s*wy\)\s+Cer.*$',
        r'^\s*wy\)\s+Pere.*$',
        r'^\s*ft\s+\|e\s+artinn.*$',
        r'^\s*E:\s+>\s+Unity.*$',
        r'^.*[Oo]nrender[Ii]mage.*$',
        r'^.*WE[BDG]?\s+O[Rri].*$',
        r'^.*abc\s+GameObject.*$',
        r'^\s*@\s+.*$',

        # Breadcrumb paths
        r'^\s*E:\s*>\s*UnityProjects.*$',
    ]

    # ─── C# Code Keywords (used to anchor prefix removal) ──────────
    _CODE_KEYWORDS = (
        r'using|public|private|protected|internal|class|struct|enum|'
        r'void|bool|int|float|string|double|var|return|if|else|for|'
        r'foreach|while|switch|case|break|new|static|override|virtual|'
        r'\[Header|\[SerializeField|\[Tooltip|namespace|abstract|sealed'
    )

    # ─── C# Structural Tokens (never discard these) ────────────────
    _STRUCTURAL_TOKENS = {'{', '}', '};', 'else', 'else {', '} else {', '} else'}

    def clean_line(self, line: str) -> Optional[str]:
        """
        Clean a single OCR line.

        Returns cleaned line string, or None if the line is noise.
        """
        line = self._normalize_symbols(line)

        # 1. Check UI noise patterns
        for pat in self.UI_NOISE_PATTERNS:
            if re.search(pat, line, re.IGNORECASE):
                return None

        if self._looks_like_editor_tabs(line):
            return None

        cleaned = line

        # 2. Remove random prefix garble before C# keywords
        cleaned = self._trim_to_code_anchor(cleaned)
        cleaned = re.sub(
            rf'^\s*[\W_a-z]{{1,4}}\s+(?=({self._CODE_KEYWORDS}))',
            '', cleaned, flags=re.IGNORECASE
        )

        # 3. Strip OCR line numbers (e.g. "p 1 using..." or "2 7 [Header...")
        cleaned = re.sub(r'^\s*(?:[a-z]{1,2}\s+)?(?:\d+\s+)+', '', cleaned)
        cleaned = re.sub(r'^\s*\d+\s+', '', cleaned)
        cleaned = cleaned.strip()

        # 4. Remove trailing cursor/IDE characters
        cleaned = re.sub(r'\s*[|I@]\s*$', '', cleaned)
        cleaned = re.sub(r'\s+(?:fod|cs|a|i|zm|os|se|Ww|fu|Bp|pil|bt|ju)\s*$', '', cleaned)
        cleaned = re.sub(r'\s+(?:i\}|==|=|a|-)$', '', cleaned)

        # Allow structural braces through immediately
        cleaned = cleaned.strip()
        if cleaned in self._STRUCTURAL_TOKENS:
            return cleaned

        if not cleaned or len(cleaned) < 2:
            return None

        # 5. Re-check noise on cleaned line
        for pat in self.UI_NOISE_PATTERNS:
            if re.search(pat, cleaned, re.IGNORECASE):
                return None

        # 6. Apply OCR corrections
        for typo, fix in self.OCR_CORRECTIONS:
            cleaned = re.sub(typo, fix, cleaned, flags=re.IGNORECASE)

        cleaned = self._trim_to_code_anchor(cleaned)
        cleaned = self._fix_common_syntax_noise(cleaned)
        cleaned = self._trim_trailing_noise(cleaned)

        if not self._is_code_like(cleaned):
            return None

        return cleaned

    def clean_frame_text(self, raw_text: str) -> List[str]:
        """
        Clean all lines from one frame's OCR output.

        Returns deduplicated list of cleaned code lines.
        """
        cleaned_lines = []
        for raw_line in raw_text.splitlines():
            result = self.clean_line(raw_line)
            if result:
                # Avoid consecutive duplicate lines within same frame
                if not cleaned_lines or cleaned_lines[-1] != result:
                    cleaned_lines.append(result)
        return cleaned_lines

    def _normalize_symbols(self, line: str) -> str:
        replacements = {
            "â€œ": "\"",
            "â€": "\"",
            "â€˜": "'",
            "â€™": "'",
            "Â©": " ",
            "ï»¿": "",
            "â€”": " ",
        }
        for bad, good in replacements.items():
            line = line.replace(bad, good)
        return line

    def _looks_like_editor_tabs(self, line: str) -> bool:
        return len(re.findall(r'\b\w+\.cs\b', line, re.IGNORECASE)) >= 2

    def _trim_to_code_anchor(self, line: str) -> str:
        match = re.search(
            rf'({self._CODE_KEYWORDS}|[A-Za-z_][A-Za-z0-9_\.]*\s*[=.;(])',
            line,
            re.IGNORECASE,
        )
        if match and match.start() <= 18:
            return line[match.start():].strip()
        return line.strip()

    def _fix_common_syntax_noise(self, line: str) -> str:
        line = re.sub(r'\bPublic\b', 'public', line)
        line = re.sub(r'\bPrivate\b', 'private', line)
        line = re.sub(r'\bUnityEngines\b', 'UnityEngine;', line)
        line = re.sub(r'MonoBehaviour\s*[.;]+$', 'MonoBehaviour', line)
        line = re.sub(r'(MonoBehaviour)\s+\d+\s*$', r'\1', line)
        line = re.sub(r'\bSystem\.\s*collections\b', 'System.Collections', line, flags=re.IGNORECASE)
        line = re.sub(r'\bSystem\.Collections\.\s*Generic\b', 'System.Collections.Generic', line, flags=re.IGNORECASE)
        line = re.sub(r'(?<=\W)@(?=\.\d)', '0', line)
        line = re.sub(r'(?<=\d)[Â¢#](?=\W|$)', 'f', line)
        line = re.sub(r'\bSf\b', '5f', line)
        # Generic OCR negation typo fixes: replacing 'I', 'l', or '|' used in place of '!' in boolean expressions
        line = re.sub(r'(\bif\s*\(\s*)[I|l|\|]\s*([a-zA-Z_]\w*)', r'\1!\2', line)
        line = re.sub(r'(\(\s*)[I|l|\|]\s*([a-zA-Z_]\w*)', r'\1!\2', line)
        line = re.sub(r'(&&\s*)[I|l|\|]\s*([a-zA-Z_]\w*)', r'\1!\2', line)
        line = re.sub(r'(\|\|\s*)[I|l|\|]\s*([a-zA-Z_]\w*)', r'\1!\2', line)
        line = re.sub(r'\s+;', ';', line)
        line = re.sub(r'\s+\)', ')', line)
        line = re.sub(r'\(\s+', '(', line)
        return line.strip()

    def _trim_trailing_noise(self, line: str) -> str:
        stripped = line.strip()

        if ';' in stripped:
            return stripped[:stripped.rfind(';') + 1].strip()

        if stripped.startswith("[") and "]" in stripped:
            return stripped[:stripped.find("]") + 1].strip()

        method_match = re.match(
            r'^((?:public|private|protected|internal|static|override|virtual|'
            r'void|bool|int|float|string|double|var|Vector[234]|Quaternion|'
            r'Rigidbody|Transform|GameObject|Text|Image|Slider|Animator|'
            r'Collider|Collision)\b.*?\))\s+.+$',
            stripped,
            re.IGNORECASE,
        )
        if method_match:
            return method_match.group(1).strip()

        control_match = re.match(
            r'^((?:if|else if|for|foreach|while|switch)\s*\(.*?\))\s+.+$',
            stripped,
            re.IGNORECASE,
        )
        if control_match:
            return control_match.group(1).strip()

        return stripped

    def _is_code_like(self, line: str) -> bool:
        stripped = line.strip()

        # Always preserve structural tokens
        if stripped in self._STRUCTURAL_TOKENS:
            return True

        # Always preserve else/else if
        if re.match(r'^\s*else\s*(if\s*\(.*\))?\s*\{?\s*$', stripped, re.IGNORECASE):
            return True

        if len(stripped) > 140:
            return False

        noise_words = (
            "Open Execution", "Open Execut", "Add Component",
            "Perspective", "Inspector", "Hierarchy",
            "Console", "Scene", "New Layer", "Layout",
            "Navigation", "Regenerated",
        )
        if any(word.lower() in stripped.lower() for word in noise_words):
            return False

        if "..." in stripped:
            return False
        if re.search(r'\b(?:Mono|Hono|Nono|Monoie|Honolie)behaviour\s+On', stripped, re.IGNORECASE):
            return False

        non_ascii_count = sum(1 for c in stripped if ord(c) > 127)
        if len(stripped) > 8 and non_ascii_count / len(stripped) > 0.12:
            return False

        letters = re.findall(r'[A-Za-z]', stripped)
        if letters:
            upper_ratio = sum(1 for c in letters if c.isupper()) / len(letters)
            if len(letters) > 12 and upper_ratio > 0.85:
                return False

        class_match = re.search(r'\bclass\s+([A-Za-z_][A-Za-z0-9_]*)', stripped, re.IGNORECASE)
        if class_match and not self._valid_identifier(class_match.group(1)):
            return False

        if re.search(r'\b\w+\.cs\b', stripped, re.IGNORECASE):
            return False

        # ── Always accept these structural patterns ──
        structural_patterns = [
            # Method/function signatures: void Awake(), private void HandleMovement()
            r'^\s*(?:public|private|protected|internal|static|override|virtual|\s)*(?:void|bool|int|float|string|double|var|IEnumerator|Coroutine)\s+[A-Za-z_][A-Za-z0-9_]*\s*\(.*\)\s*\{?\s*$',
            # Variable/field declarations: InputManager inputManager;
            r'^\s*(?:public|private|protected|internal|static|\s)*(?:int|float|bool|string|double|var|Vector[234]|Quaternion|Rigidbody|Transform|GameObject|Text|Image|Slider|Animator|LayerMask|Collider|Collision|RaycastHit|AudioSource|Camera|[A-Z][A-Za-z0-9_<>\[\]]*)\s+[a-z_][A-Za-z0-9_]*\s*[;=]',
            # Using, namespace, return, break, continue
            r'^\s*(?:using|namespace|return|break|continue)\b',
            # Class declaration
            r'^\s*(?:public|private|protected|internal)?\s*class\s+[A-Za-z_][A-Za-z0-9_]*',
            # Attribute: [Header(...)], [SerializeField]
            r'^\s*\[[A-Za-z_][A-Za-z0-9_]*(?:\(.*\))?\]$',
            # Assignments: variable = ...; 
            r'^\s*[A-Za-z_][A-Za-z0-9_.]*\s*=.*[;)]\s*$',
            # Method calls: Method(); or obj.Method();
            r'^\s*[A-Za-z_][A-Za-z0-9_.]*\s*\(.*\)\s*;?\s*$',
            # Chained: obj.Method(args);
            r'^\s*[A-Za-z_][A-Za-z0-9_.]*\.[A-Za-z_][A-Za-z0-9_]*\s*\(',
            # Control flow: if(...), for(...), etc
            r'^\s*(?:if|else if|for|foreach|while|switch)\s*\(.+\)',
            # case X:
            r'^\s*case\s+.+:\s*$',
            # new Constructor()
            r'^\s*new\s+[A-Za-z_][A-Za-z0-9_<>]*\s*\(',
            # Header attributes with various forms
            r'^\s*\[Header\(',
            # public float walkingSpeed = 1f;
            r'^\s*(?:public|private|protected)\s+(?:static\s+)?(?:float|int|bool|string)\s+[A-Za-z_]',
        ]
        return any(re.search(pattern, stripped, re.IGNORECASE) for pattern in structural_patterns)

    def _is_valid_access_declaration(self, line: str) -> bool:
        type_pattern = (
            r'(?:int|float|bool|string|double|var|Vector[234]|Quaternion|'
            r'Rigidbody|Transform|GameObject|Text|Image|Slider|Animator|'
            r'LayerMask|Collider|Collision|RaycastHit|AudioSource|Camera|'
            r'[A-Z][A-Za-z0-9_<>.\[\]]*)'
        )
        patterns = [
            r'^\s*(?:public|private|protected|internal)\s+class\s+[A-Za-z_][A-Za-z0-9_]*(?:\s*:\s*[A-Za-z_][A-Za-z0-9_]*)?\s*$',
            rf'^\s*(?:public|private|protected|internal)\s+(?:static\s+)?(?:void|bool|int|float|string|double|{type_pattern})\s+[A-Za-z_][A-Za-z0-9_]*\s*\([^)]*\)\s*$',
            rf'^\s*(?:public|private|protected|internal)\s+(?:static\s+)?{type_pattern}\s+[A-Za-z_][A-Za-z0-9_]*(?:\s*[;=].*)?$',
        ]
        return any(re.match(pattern, line, re.IGNORECASE) for pattern in patterns)

    def _valid_identifier(self, name: str) -> bool:
        if len(name) < 3 or len(name) > 48:
            return False
        letters = re.findall(r'[A-Za-z]', name)
        if letters:
            upper_ratio = sum(1 for c in letters if c.isupper()) / len(letters)
            if len(letters) > 10 and upper_ratio > 0.75:
                return False
        return True
