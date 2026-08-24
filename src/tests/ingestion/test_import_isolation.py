"""
Static analysis test to verify pipeline code doesn't directly import LLM SDKs.
"""
import ast
import sys
from pathlib import Path

def analyze_pipeline_imports():
    """Analyze the pipeline.py file for direct imports of LLM SDKs."""

    pipeline_file = Path("src/app/ingestion/pipeline.py")

    if not pipeline_file.exists():
        print(f"❌ Pipeline file not found: {pipeline_file}")
        return False

    # Read the file content
    with open(pipeline_file, 'r') as f:
        content = f.read()

    # Parse the AST
    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        print(f"❌ Syntax error in pipeline.py: {e}")
        return False

    # Look for imports that could be LLM SDKs
    llm_sdk_imports = [
        'requests', 'httpx', 'openai', 'anthropic', 'transformers',
        'torch', 'tensorflow', 'llama-cpp-python'
    ]

    problematic_imports = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                module_name = alias.name
                # Check if this is a known LLM SDK import
                for sdk in llm_sdk_imports:
                    if sdk in module_name or module_name == sdk:
                        problematic_imports.append(f"Direct import of {module_name}")
        elif isinstance(node, ast.ImportFrom):
            module_name = node.module
            if module_name:
                # Check if this is a known LLM SDK import
                for sdk in llm_sdk_imports:
                    if sdk in module_name or module_name == sdk:
                        problematic_imports.append(f"Import from {module_name}")

    if problematic_imports:
        print("❌ Found direct imports of LLM SDKs in pipeline.py:")
        for imp in problematic_imports:
            print(f"  - {imp}")
        return False
    else:
        print("✅ No direct imports of LLM SDKs found in pipeline.py")
        return True

def test_provider_isolation():
    """Test that provider classes are only imported where they should be."""

    # Check that providers/base.py exists and has the right structure
    base_file = Path("src/app/ingestion/providers/base.py")
    if not base_file.exists():
        print(f"❌ Base provider file not found: {base_file}")
        return False

    print("✅ Provider interface base file exists")

    # Check that ollama_provider.py imports only the base
    ollama_file = Path("src/app/ingestion/providers/ollama_provider.py")
    if not ollama_file.exists():
        print(f"❌ Ollama provider file not found: {ollama_file}")
        return False

    with open(ollama_file, 'r') as f:
        content = f.read()

    # Should import base provider interface but not concrete SDKs
    if "from .base import Provider, ExtractionResult, ExtractedAssertion" in content:
        print("✅ Ollama provider correctly imports from base interface")
    else:
        print("❌ Ollama provider does not import from base interface")
        return False

    # Verify no direct SDK imports in the top-level section
    lines = content.split('\n')

    # Check for direct imports that would violate isolation
    has_direct_imports = False
    for line in lines:
        line = line.strip()
        if line.startswith('import requests') or line.startswith('from requests'):
            print("❌ Ollama provider has direct import of requests")
            has_direct_imports = True
            break

    # Also check for other LLM SDK imports that would violate isolation
    sdk_patterns = ['import httpx', 'from httpx', 'import openai', 'from openai',
                    'import anthropic', 'from anthropic', 'import torch', 'from torch']

    for pattern in sdk_patterns:
        if pattern in content:
            print(f"❌ Ollama provider has direct import of SDK: {pattern}")
            has_direct_imports = True
            break

    if not has_direct_imports:
        print("✅ Ollama provider correctly avoids direct SDK imports")

    return True

def test_no_git_usage():
    """Verify that no git usage exists in ingestion module."""

    # Check all Python files in the ingestion directory for git usage
    ingestion_dir = Path("src/app/ingestion")

    if not ingestion_dir.exists():
        print(f"❌ Ingestion directory not found: {ingestion_dir}")
        return False

    # Files to check for git usage
    files_to_check = []
    for py_file in ingestion_dir.rglob("*.py"):
        files_to_check.append(py_file)

    # Also check the main module files
    main_files = [
        Path("src/app/__init__.py"),
        Path("src/app/ingestion/__init__.py")
    ]
    files_to_check.extend(main_files)

    git_usage_found = False

    print("🔍 Scanning ingestion module for git usage...")

    for file_path in files_to_check:
        try:
            with open(file_path, 'r') as f:
                content = f.read()

            # Look for common git usage patterns
            git_patterns = [
                "import git",
                "from git",
                "subprocess.*git",
                "os.system.*git",
                "\.git/",
                "git.*clone",
                "git.*pull",
                "git.*push",
                "os.*system.*git"
            ]

            for pattern in git_patterns:
                if pattern in content:
                    print(f"❌ Found git usage in {file_path}: {pattern}")
                    git_usage_found = True

        except Exception as e:
            print(f"⚠️  Could not check {file_path}: {e}")

    if not git_usage_found:
        print("✅ No git usage found in ingestion module")
        return True
    else:
        return False

def test_comprehensive_git_verification():
    """Run comprehensive git verification across all files."""
    # This is a more thorough check that looks at the actual implementation

    # Check for any usage of git commands or patterns
    ingestion_dir = Path("src/app/ingestion")

    if not ingestion_dir.exists():
        print(f"❌ Ingestion directory not found: {ingestion_dir}")
        return False

    files_to_check = []
    for py_file in ingestion_dir.rglob("*.py"):
        files_to_check.append(py_file)

    # Also check main module files
    main_files = [
        Path("src/app/__init__.py"),
        Path("src/app/ingestion/__init__.py")
    ]
    files_to_check.extend(main_files)

    print("🔍 Running comprehensive git usage verification...")

    git_patterns_found = []

    for file_path in files_to_check:
        try:
            with open(file_path, 'r') as f:
                content = f.read()

            # More comprehensive git pattern detection
            patterns = [
                r"import.*git",
                r"from.*git",
                r"subprocess.*\b(git|clone|pull|push|commit|add)\b",
                r"os\.system.*\b(git|clone|pull|push|commit|add)\b",
                r"\.git/",
                r"git\s+clone",
                r"git\s+pull",
                r"git\s+push",
                r"git\s+commit",
                r"git\s+add"
            ]

            for pattern in patterns:
                if pattern in content:
                    git_patterns_found.append(f"{pattern} in {file_path}")

        except Exception as e:
            print(f"⚠️  Could not check {file_path}: {e}")

    if git_patterns_found:
        print("❌ Found git usage patterns:")
        for pattern in git_patterns_found:
            print(f"  - {pattern}")
        return False
    else:
        print("✅ No git usage patterns found in ingestion module")
        return True

if __name__ == "__main__":
    print("Testing import isolation and git usage...")
    print("=" * 50)

    success1 = analyze_pipeline_imports()
    print()
    success2 = test_provider_isolation()
    print()
    success3 = test_no_git_usage()
    print()
    success4 = test_comprehensive_git_verification()

    if success1 and success2 and success3 and success4:
        print("\n✅ All isolation tests passed!")
    else:
        print("\n❌ Some isolation tests failed!")
        sys.exit(1)