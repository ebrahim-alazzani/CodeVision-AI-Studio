import unittest

from core.reconstruction.code_detector import CodeDetector, CodeStructure
from languages.builtin import create_default_registry


class CodeDetectorTests(unittest.TestCase):
    def setUp(self):
        self.detector = CodeDetector()

    def test_detect_python_structure(self):
        code = [
            "import os",
            "from pathlib import Path",
            "",
            "class NeuralNetwork:",
            "    def __init__(self, layers):",
            "        self.layers = layers",
            "",
            "    def train(self, data):",
            "        pass",
            "",
            "def main():",
            "    model = NeuralNetwork([64, 32, 1])",
            "    print('Ready')",
            "",
            "if __name__ == '__main__':",
            "    main()",
        ]
        structure = self.detector.detect_structure(code, language="python")
        self.assertEqual("python", structure.language)
        self.assertIn("NeuralNetwork", structure.classes)
        self.assertIn("train", structure.functions)
        self.assertTrue(any("main" in ep for ep in structure.entry_points))
        self.assertTrue(any("__main__" in ep for ep in structure.entry_points))
        self.assertEqual("NeuralNetwork.py", structure.file_name)
        self.assertGreater(structure.confidence, 0.4)
        self.assertLessEqual(structure.confidence, 1.0)

    def test_detect_typescript_structure(self):
        code = [
            "import { useState, useEffect } from 'react';",
            "",
            "export interface UserProfile {",
            "    id: string;",
            "    username: string;",
            "}",
            "",
            "export type AuthState = 'idle' | 'loading' | 'success';",
            "",
            "export default class AuthService {",
            "    async login(token: string): Promise<UserProfile> {",
            "        return { id: '1', username: 'admin' };",
            "    }",
            "}",
        ]
        structure = self.detector.detect_structure(code, language="typescript")
        self.assertEqual("typescript", structure.language)
        self.assertIn("AuthService", structure.classes)
        self.assertIn("UserProfile", structure.interfaces)
        self.assertTrue(any("export default" in ep for ep in structure.entry_points))
        self.assertEqual("AuthService.ts", structure.file_name)
        self.assertGreater(structure.confidence, 0.4)
        self.assertLessEqual(structure.confidence, 1.0)

    def test_detect_cpp_structure(self):
        code = [
            "#include <iostream>",
            "#include <vector>",
            "",
            "namespace Engine {",
            "    class VulkanRenderer {",
            "    public:",
            "        void initialize();",
            "    };",
            "}",
            "",
            "int main(int argc, char** argv) {",
            "    std::cout << 'Starting engine' << std::endl;",
            "    return 0;",
            "}",
        ]
        structure = self.detector.detect_structure(code, language="cpp")
        self.assertEqual("cpp", structure.language)
        self.assertIn("VulkanRenderer", structure.classes)
        self.assertIn("Engine", structure.namespaces)
        self.assertTrue(any("main" in ep for ep in structure.entry_points))
        self.assertTrue(structure.file_name.endswith(".cpp"))
        self.assertGreater(structure.confidence, 0.4)
        self.assertLessEqual(structure.confidence, 1.0)

    def test_detect_rust_structure(self):
        code = [
            "use std::collections::HashMap;",
            "",
            "pub struct NetworkRouter {",
            "    routes: HashMap<String, String>,",
            "}",
            "",
            "pub trait RouteHandler {",
            "    fn dispatch(&self, path: &str);",
            "}",
            "",
            "impl NetworkRouter {",
            "    pub fn new() -> Self {",
            "        Self { routes: HashMap::new() }",
            "    }",
            "}",
            "",
            "fn main() {",
            "    let router = NetworkRouter::new();",
            "    println!('Router running');",
            "}",
        ]
        structure = self.detector.detect_structure(code, language="rust")
        self.assertEqual("rust", structure.language)
        self.assertIn("NetworkRouter", structure.classes)
        self.assertIn("RouteHandler", structure.interfaces)
        self.assertTrue(any("fn main" in ep for ep in structure.entry_points))
        self.assertEqual("NetworkRouter.rs", structure.file_name)
        self.assertGreater(structure.confidence, 0.4)
        self.assertLessEqual(structure.confidence, 1.0)

    def test_detect_go_structure(self):
        code = [
            "package main",
            "",
            "import 'fmt'",
            "",
            "type HttpServer struct {",
            "    port int",
            "}",
            "",
            "type Handler interface {",
            "    Serve()",
            "}",
            "",
            "func (s *HttpServer) Start() {",
            "    fmt.Println('Listening on port', s.port)",
            "}",
            "",
            "func main() {",
            "    srv := &HttpServer{port: 8080}",
            "    srv.Start()",
            "}",
        ]
        structure = self.detector.detect_structure(code, language="go")
        self.assertEqual("go", structure.language)
        self.assertIn("HttpServer", structure.classes)
        self.assertIn("Handler", structure.interfaces)
        self.assertIn("main", structure.namespaces)
        self.assertTrue(any("func main" in ep for ep in structure.entry_points))
        self.assertEqual("httpserver.go", structure.file_name)
        self.assertGreater(structure.confidence, 0.4)
        self.assertLessEqual(structure.confidence, 1.0)

    def test_detect_csharp_structure(self):
        code = [
            "using System;",
            "",
            "namespace GameEngine {",
            "    public class PlayerController {",
            "        private float speed = 5.0f;",
            "        public void Update() {}",
            "    }",
            "}",
        ]
        structure = self.detector.detect_structure(code, language="csharp")
        self.assertEqual("csharp", structure.language)
        self.assertIn("PlayerController", structure.classes)
        self.assertIn("GameEngine", structure.namespaces)
        self.assertEqual("PlayerController.cs", structure.file_name)
        self.assertGreater(structure.confidence, 0.4)

    def test_auto_detect_without_language_spec(self):
        python_code = "def calculate_mean(values):\n    return sum(values) / len(values)\n\nif __name__ == '__main__':\n    pass"
        struct_py = self.detector.detect_structure(python_code, language="auto")
        self.assertEqual("python", struct_py.language)

        go_code = "package main\n\nimport \"fmt\"\n\nfunc main() {\n    fmt.Println(\"Go!\")\n}"
        struct_go = self.detector.detect_structure(go_code, language="auto")
        self.assertEqual("go", struct_go.language)

        rust_code = "fn main() {\n    let mut numbers = vec![1, 2, 3];\n    println!(\"{:?}\", numbers);\n}"
        struct_rs = self.detector.detect_structure(rust_code, language="auto")
        self.assertEqual("rust", struct_rs.language)

    def test_empty_or_gibberish_has_zero_confidence(self):
        empty_struct = self.detector.detect_structure([], language="auto")
        self.assertEqual(0.0, empty_struct.confidence)
        self.assertEqual("generic", empty_struct.language)

        gibberish = ["xyz123 abc 789", "=== ---- +++"]
        gib_struct = self.detector.detect_structure(gibberish, language="auto")
        self.assertEqual(0.0, gib_struct.confidence)

    def test_ide_breadcrumb_detects_file_and_language(self):
        breadcrumb_lines = [
            "> src > components > HeaderNavigation.tsx",
            "export const HeaderNavigation = () => { return <nav></nav>; };"
        ]
        structure = self.detector.detect_structure(breadcrumb_lines, language="auto")
        self.assertEqual("typescript", structure.language)
        self.assertEqual("HeaderNavigation.tsx", structure.file_name)
        self.assertGreater(structure.confidence, 0.2)


if __name__ == "__main__":
    unittest.main()
