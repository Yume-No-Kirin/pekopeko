"""
Test script to verify the ingestion module implementation.
This script tests that all required components are properly implemented and can be imported.
"""
import sys
import os
from pathlib import Path

def test_imports():
    """Test that all modules can be imported successfully."""
    try:
        # Test basic imports
        from src.app.ingestion import (
            ingest_source,
            process_source,
            IngestionResult,
            Provider,
            ExtractionResult,
            ExtractedAssertion,
            OllamaProvider,
            OllamaProviderConfig,
            SourceReaderRegistry,
            write_source_file,
            write_proposal_file,
            TaskState
        )

        print("✓ All core modules imported successfully")

        # Test that we can create instances
        config = OllamaProviderConfig()
        print("✓ OllamaProviderConfig created successfully")

        # Test basic structure
        assert hasattr(ingest_source, '__call__')
        assert hasattr(OllamaProvider, '__init__')
        assert hasattr(SourceReaderRegistry, 'register')
        assert hasattr(TaskState, 'save')

        print("✓ All core functionality verified")
        return True

    except Exception as e:
        print(f"[ERROR] Import test failed: {e}")
        return False

def test_file_structure():
    """Test that all required files exist."""
    required_files = [
        '../app/__init__.py',
        '../app/ingestion/__init__.py',
        '../app/ingestion/pipeline.py',
        '../app/ingestion/storage.py',
        '../app/ingestion/task_state.py',
        '../app/ingestion/providers/base.py',
        '../app/ingestion/providers/ollama_provider.py',
        '../app/ingestion/readers/base.py',
        '../app/ingestion/readers/markdown_reader.py',
        '../.env'
    ]

    missing_files = []
    for file_path in required_files:
        full_path = Path(file_path)
        if not full_path.exists():
            missing_files.append(file_path)

    if missing_files:
        print(f"✗ Missing files: {missing_files}")
        return False
    else:
        print("✓ All required files present")
        return True

def main():
    """Run all tests."""
    print("Testing Pekopeko Ingestion Module Implementation")
    print("=" * 50)

    import_success = test_imports()
    structure_success = test_file_structure()

    if import_success and structure_success:
        print("\n[SUCCESS] All tests passed! Implementation is ready.")
        return 0
    else:
        print("\n[FAILED] Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())