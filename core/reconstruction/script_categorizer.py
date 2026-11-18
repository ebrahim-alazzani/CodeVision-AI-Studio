"""
ScriptCategorizer — CodeVision Extractor v5.0 Architecture Categorizer

Automatically analyzes reconstructed C# classes and organizes them into clean,
standardized Unity folder hierarchies based on class names, keywords, and responsibilities.

Author: Eng. Ibrahim Anas Al-Azzani
        CyberPro for Technical & Engineering Works
"""

import re
from pathlib import Path
from typing import Dict, List, Optional


class ScriptCategorizer:
    """Categorizes code scripts into project directory structures across languages."""

    # Multi-language & generic architecture category mapping rules (Keyword regex -> Folder Name)
    CATEGORY_RULES = [
        (r'Controller|Handler|Router|Endpoint|Api', 'Controllers'),
        (r'Model|Entity|Schema|Type|Interface|Dto', 'Models'),
        (r'Service|Repository|Provider|Client|Manager', 'Services'),
        (r'UI|Menu|HUD|Canvas|MiniMap|Map|HealthBar|Score|Wanted|View|Component|Widget|Page', 'UI'),
        (r'Util|Helper|Common|Tool|Lib|Extension', 'Utils'),
        (r'Config|Setting|Env|Constant|Option', 'Config'),
        (r'Test|Spec|Mock|Fixture', 'Tests'),
        (r'Player|Locomotion|Movement|Character|Sprint|Stance', 'Player'),
        (r'Camera|Cinemachine|Orbit|Follow', 'Camera'),
        (r'AI|Spawner|Police|Officer|Enemy|NPC|Waypoint|Navigator', 'AI'),
        (r'Car|Vehicle|Drive|Wheel|Steering|Traffic', 'Vehicles'),
        (r'Shoot|Gun|Weapon|Bullet|Ammo|Rifle|Combat|Attack', 'Shooting'),
        (r'Audio|Sound|Music|SFX', 'Audio'),
        (r'Save|Data|Database|Storage', 'Data'),
    ]

    @classmethod
    def get_category(cls, class_name: str, code_content: str = "") -> str:
        """
        Determine the folder category for a given class/module name and optional code content.

        Args:
            class_name: The name of the class or module (e.g., 'PlayerMovement', 'AuthService').
            code_content: Full source code text.

        Returns:
            Folder name string (e.g., 'Controllers', 'Services', 'Player', 'General').
        """
        # 1. Match against Class / File Name first
        for pattern, folder in cls.CATEGORY_RULES:
            if re.search(pattern, class_name, re.IGNORECASE):
                return folder

        # 2. Match against Code Content if class name is neutral
        if code_content:
            for pattern, folder in cls.CATEGORY_RULES:
                if re.search(pattern, code_content, re.IGNORECASE):
                    return folder

        return 'General'

    @classmethod
    def organize_export(cls, scripts_dict: Dict[str, str], output_dir: Path, extension: str = ".cs") -> Dict[str, Path]:
        """
        Export scripts into categorized subdirectories under output_dir/ProjectScripts.

        Args:
            scripts_dict: Dictionary mapping class_name/file_name -> formatted_code.
            output_dir: Base output directory Path.
            extension: File extension to apply if filename has none (e.g. '.py', '.ts', '.cs').

        Returns:
            Dict mapping class_name -> file_path where written.
        """
        written_files = {}
        base_dir = output_dir / "ProjectScripts"
        base_dir.mkdir(parents=True, exist_ok=True)

        ext = extension if extension.startswith(".") else f".{extension}"

        for class_name, code in scripts_dict.items():
            category = cls.get_category(class_name, code)
            cat_dir = base_dir / category
            cat_dir.mkdir(parents=True, exist_ok=True)

            # Avoid double extension
            if "." in class_name:
                filename = class_name
            else:
                filename = f"{class_name}{ext}"

            file_path = cat_dir / filename
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(code)

            written_files[class_name] = file_path

        return written_files
