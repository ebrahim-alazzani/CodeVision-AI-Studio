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
        (r'UI|Menu|HUD|Canvas|MiniMap|Map|HealthBar|Score|Wanted|View|Component|Widget|Page|Screen|Layout|Template', 'UI'),
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
        Supports Flutter/Dart (lib/screens, lib/widgets, pubspec.yaml),
        Unity/C# (Assets/Scripts, .csproj, .sln), Python (src/, pyproject.toml),
        and TypeScript/Web (src/, package.json).

        Args:
            scripts_dict: Dictionary mapping class_name/file_name -> formatted_code.
            output_dir: Base output directory Path.
            extension: File extension to apply if filename has none (e.g. '.py', '.dart', '.cs').

        Returns:
            Dict mapping class_name -> file_path where written.
        """
        written_files = {}
        base_dir = output_dir / "ProjectScripts"
        base_dir.mkdir(parents=True, exist_ok=True)

        ext = extension if extension.startswith(".") else f".{extension}"
        is_flutter = ext == ".dart" or any("Widget" in code or "package:flutter" in code for code in scripts_dict.values())
        is_csharp = ext == ".cs" or any("MonoBehaviour" in code or "using System" in code for code in scripts_dict.values())
        is_python = ext in (".py", ".pyw") or any("def " in code and "import " in code for code in scripts_dict.values())

        # Determine target source root
        if is_flutter:
            src_root = base_dir / "lib"
            # Auto-scaffold pubspec.yaml if missing
            pubspec = base_dir / "pubspec.yaml"
            if not pubspec.exists():
                pubspec.write_text(
                    "name: reconstructed_flutter_app\n"
                    "description: Reconstructed by CodeVision AI Studio\n"
                    "publish_to: 'none'\n"
                    "version: 1.0.0+1\n\n"
                    "environment:\n"
                    "  sdk: '>=3.0.0 <4.0.0'\n\n"
                    "dependencies:\n"
                    "  flutter:\n"
                    "    sdk: flutter\n"
                    "  cupertino_icons: ^1.0.6\n\n"
                    "flutter:\n"
                    "  uses-material-design: true\n",
                    encoding="utf-8"
                )
        elif is_csharp:
            src_root = base_dir / "Assets" / "Scripts"
            # Auto-scaffold .csproj
            csproj = base_dir / "ReconstructedApp.csproj"
            if not csproj.exists():
                csproj.write_text(
                    '<Project Sdk="Microsoft.NET.Sdk">\n'
                    '  <PropertyGroup>\n'
                    '    <OutputType>Library</OutputType>\n'
                    '    <TargetFramework>net9.0</TargetFramework>\n'
                    '    <ImplicitUsings>enable</ImplicitUsings>\n'
                    '    <Nullable>enable</Nullable>\n'
                    '  </PropertyGroup>\n'
                    '</Project>\n',
                    encoding="utf-8"
                )
        elif is_python:
            src_root = base_dir / "src"
            req = base_dir / "requirements.txt"
            if not req.exists():
                req.write_text("# CodeVision Reconstructed Python Project\n", encoding="utf-8")
        else:
            src_root = base_dir

        src_root.mkdir(parents=True, exist_ok=True)

        for class_name, code in scripts_dict.items():
            category = cls.get_category(class_name, code)
            
            # Map categories to idiomatic language folder names
            if is_flutter:
                folder_name = "screens" if category in ("UI", "General") and ("Screen" in class_name or "Page" in class_name or "Layout" in class_name) else ("widgets" if category == "UI" else category.lower())
            else:
                folder_name = category

            cat_dir = src_root / folder_name
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

        # If Flutter, ensure a starter lib/main.dart exists if none extracted
        if is_flutter:
            main_dart = src_root / "main.dart"
            if not main_dart.exists():
                main_dart.write_text(
                    "import 'package:flutter/material.dart';\n\n"
                    "void main() {\n"
                    "  runApp(const MaterialApp(home: Scaffold(body: Center(child: Text('CodeVision Reconstructed App')))));\n"
                    "}\n",
                    encoding="utf-8"
                )
                written_files["main.dart"] = main_dart

        return written_files
