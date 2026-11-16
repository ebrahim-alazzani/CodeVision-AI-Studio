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
    """Categorizes C# scripts into Unity project directory structures."""

    # Default category mapping rules (Keyword regex -> Folder Name)
    CATEGORY_RULES = [
        (r'Player|Locomotion|Movement|Character|Sprint|Stance', 'Player'),
        (r'Camera|Cinemachine|Orbit|Follow', 'Camera'),
        (r'AI|Spawner|Police|Officer|Enemy|NPC|Waypoint|Navigator', 'AI'),
        (r'UI|Menu|HUD|Canvas|MiniMap|Map|HealthBar|Score|Wanted', 'UI'),
        (r'Car|Vehicle|Drive|Wheel|Steering|Traffic', 'Vehicles'),
        (r'Shoot|Gun|Weapon|Bullet|Ammo|Rifle|Combat|Attack', 'Shooting'),
        (r'Audio|Sound|Music|SFX', 'Audio'),
        (r'Save|Data|Database|Storage|Config|Setting', 'Data'),
    ]

    @classmethod
    def get_category(cls, class_name: str, code_content: str = "") -> str:
        """
        Determine the folder category for a given class name and optional code content.

        Args:
            class_name: The name of the C# class (e.g., 'PlayerMovement').
            code_content: Full source code text of the class.

        Returns:
            Folder name string (e.g., 'Player', 'Camera', 'General').
        """
        # 1. Match against Class Name first
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
    def organize_export(cls, scripts_dict: Dict[str, str], output_dir: Path) -> Dict[str, Path]:
        """
        Export scripts into categorized subdirectories under output_dir/ProjectScripts.

        Args:
            scripts_dict: Dictionary mapping class_name -> formatted_code.
            output_dir: Base output directory Path.

        Returns:
            Dict mapping class_name -> file_path where written.
        """
        written_files = {}
        base_dir = output_dir / "ProjectScripts"
        base_dir.mkdir(parents=True, exist_ok=True)

        for class_name, code in scripts_dict.items():
            category = cls.get_category(class_name, code)
            cat_dir = base_dir / category
            cat_dir.mkdir(parents=True, exist_ok=True)

            file_path = cat_dir / f"{class_name}.cs"
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(code)

            written_files[class_name] = file_path

        return written_files
