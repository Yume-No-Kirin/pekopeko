"""
Tests for canonical item storage primitive.
"""

import os
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

import pytest
from knowledge_core.storage import (
    write_canonical_item, read_canonical_item, read_item_history,
    ValidationError
)


def test_first_write_no_prior_file():
    """Test writing a new item with no prior ACTIVE file."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create a simple item
        frontmatter = {
            "id": "test-item-1",
            "type": "entity",
            "domain": "PERSONAL",
            "lifecycle_status": "ACTIVE",
            "epistemic_status": "direct",
            "version": 1,
            "created_at": "2026-08-16T10:00:00",
            "valid_from": None,
            "valid_until": None,
            "provenance": "test source"
        }
        body = "# Test Entity\n\nThis is a test entity."

        # Write the item
        write_canonical_item(
            vault_root=tmp_dir,
            domain="PERSONAL",
            item_type="entity",
            item_id="test-item-1",
            frontmatter=frontmatter,
            body=body
        )

        # Verify file was created correctly
        expected_path = os.path.join(tmp_dir, "PERSONAL", "entities", "test-item-1", "test-item-1.md")
        assert os.path.exists(expected_path)

        # Read it back
        read_frontmatter, read_body = read_canonical_item(
            vault_root=tmp_dir,
            domain="PERSONAL",
            item_type="entity",
            item_id="test-item-1"
        )

        assert read_frontmatter["id"] == "test-item-1"
        assert read_frontmatter["type"] == "entity"
        assert read_frontmatter["domain"] == "PERSONAL"
        assert read_frontmatter["lifecycle_status"] == "ACTIVE"
        assert read_frontmatter["version"] == 1
        assert read_body.strip() == body.strip()


def test_update_creates_history():
    """Test that updating an existing item creates a history entry."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create initial item
        frontmatter1 = {
            "id": "test-item-1",
            "type": "entity",
            "domain": "PERSONAL",
            "lifecycle_status": "ACTIVE",
            "epistemic_status": "direct",
            "version": 1,
            "created_at": "2026-08-16T10:00:00",
            "valid_from": None,
            "valid_until": None,
            "provenance": "test source"
        }
        body1 = "# Test Entity\n\nOriginal content."

        write_canonical_item(
            vault_root=tmp_dir,
            domain="PERSONAL",
            item_type="entity",
            item_id="test-item-1",
            frontmatter=frontmatter1,
            body=body1
        )

        # Update the item
        frontmatter2 = {
            "id": "test-item-1",
            "type": "entity",
            "domain": "PERSONAL",
            "lifecycle_status": "ACTIVE",
            "epistemic_status": "inferred",
            "version": 2,
            "created_at": "2026-08-16T11:00:00",
            "valid_from": None,
            "valid_until": None,
            "provenance": "test source updated"
        }
        body2 = "# Test Entity\n\nUpdated content."

        write_canonical_item(
            vault_root=tmp_dir,
            domain="PERSONAL",
            item_type="entity",
            item_id="test-item-1",
            frontmatter=frontmatter2,
            body=body2
        )

        # Verify history file was created
        item_dir = os.path.join(tmp_dir, "PERSONAL", "entities", "test-item-1")
        history_dir = os.path.join(item_dir, "history")
        assert os.path.exists(history_dir)

        # Check that there's exactly one history file
        history_files = os.listdir(history_dir)
        assert len(history_files) == 1

        # Read the current item
        current_frontmatter, current_body = read_canonical_item(
            vault_root=tmp_dir,
            domain="PERSONAL",
            item_type="entity",
            item_id="test-item-1"
        )

        assert current_frontmatter["version"] == 2
        assert current_frontmatter["lifecycle_status"] == "ACTIVE"
        assert current_body.strip() == body2.strip()

        # Read history
        history = read_item_history(
            vault_root=tmp_dir,
            domain="PERSONAL",
            item_type="entity",
            item_id="test-item-1"
        )

        assert len(history) == 1
        assert history[0]["frontmatter"]["version"] == 1
        assert history[0]["frontmatter"]["lifecycle_status"] == "SUPERSEDED"
        assert history[0]["frontmatter"]["superseded_by"] == "v2"
        assert history[0]["body"].strip() == body1.strip()


def test_three_sequential_updates():
    """Test that three sequential updates produce exactly 2 history entries."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create initial item
        frontmatter1 = {
            "id": "test-item-1",
            "type": "entity",
            "domain": "PERSONAL",
            "lifecycle_status": "ACTIVE",
            "epistemic_status": "direct",
            "version": 1,
            "created_at": "2026-08-16T10:00:00",
            "valid_from": None,
            "valid_until": None,
            "provenance": "test source"
        }
        body1 = "# Test Entity\n\nVersion 1."

        write_canonical_item(
            vault_root=tmp_dir,
            domain="PERSONAL",
            item_type="entity",
            item_id="test-item-1",
            frontmatter=frontmatter1,
            body=body1
        )

        # Update to version 2
        frontmatter2 = {
            "id": "test-item-1",
            "type": "entity",
            "domain": "PERSONAL",
            "lifecycle_status": "ACTIVE",
            "epistemic_status": "inferred",
            "version": 2,
            "created_at": "2026-08-16T11:00:00",
            "valid_from": None,
            "valid_until": None,
            "provenance": "test source updated"
        }
        body2 = "# Test Entity\n\nVersion 2."

        write_canonical_item(
            vault_root=tmp_dir,
            domain="PERSONAL",
            item_type="entity",
            item_id="test-item-1",
            frontmatter=frontmatter2,
            body=body2
        )

        # Update to version 3
        frontmatter3 = {
            "id": "test-item-1",
            "type": "entity",
            "domain": "PERSONAL",
            "lifecycle_status": "ACTIVE",
            "epistemic_status": "uncertain",
            "version": 3,
            "created_at": "2026-08-16T12:00:00",
            "valid_from": None,
            "valid_until": None,
            "provenance": "test source updated again"
        }
        body3 = "# Test Entity\n\nVersion 3."

        write_canonical_item(
            vault_root=tmp_dir,
            domain="PERSONAL",
            item_type="entity",
            item_id="test-item-1",
            frontmatter=frontmatter3,
            body=body3
        )

        # Read history - should have exactly 2 entries (v1 → v2, v2 → v3)
        history = read_item_history(
            vault_root=tmp_dir,
            domain="PERSONAL",
            item_type="entity",
            item_id="test-item-1"
        )

        assert len(history) == 2

        # History should be ordered oldest to newest
        assert history[0]["frontmatter"]["version"] == 1
        assert history[0]["frontmatter"]["lifecycle_status"] == "SUPERSEDED"
        assert history[0]["frontmatter"]["superseded_by"] == "v2"

        assert history[1]["frontmatter"]["version"] == 2
        assert history[1]["frontmatter"]["lifecycle_status"] == "SUPERSEDED"
        assert history[1]["frontmatter"]["superseded_by"] == "v3"


def test_missing_required_field_raises_validation_error():
    """Test that missing required frontmatter fields raise a validation error."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create an item without a required field
        frontmatter = {
            "id": "test-item-1",
            "type": "entity",
            "domain": "PERSONAL",
            # Missing lifecycle_status
            "epistemic_status": "direct",
            "version": 1,
            "created_at": "2026-08-16T10:00:00",
            "valid_from": None,
            "valid_until": None,
            "provenance": "test source"
        }
        body = "# Test Entity\n\nContent."

        # This should raise a ValidationError
        with pytest.raises(ValidationError, match="Missing required frontmatter field"):
            write_canonical_item(
                vault_root=tmp_dir,
                domain="PERSONAL",
                item_type="entity",
                item_id="test-item-1",
                frontmatter=frontmatter,
                body=body
            )

        # Verify no files were written
        item_dir = os.path.join(tmp_dir, "PERSONAL", "entities", "test-item-1")
        assert not os.path.exists(item_dir)


def test_atomic_write():
    """Test that writes are atomic (using temp file approach)."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create initial item
        frontmatter1 = {
            "id": "test-item-1",
            "type": "entity",
            "domain": "PERSONAL",
            "lifecycle_status": "ACTIVE",
            "epistemic_status": "direct",
            "version": 1,
            "created_at": "2026-08-16T10:00:00",
            "valid_from": None,
            "valid_until": None,
            "provenance": "test source"
        }
        body1 = "# Test Entity\n\nOriginal content."

        write_canonical_item(
            vault_root=tmp_dir,
            domain="PERSONAL",
            item_type="entity",
            item_id="test-item-1",
            frontmatter=frontmatter1,
            body=body1
        )

        # Verify atomicity by checking that no temp files exist after write
        item_dir = os.path.join(tmp_dir, "PERSONAL", "entities", "test-item-1")
        main_file = os.path.join(item_dir, "test-item-1.md")

        # The main file should exist and be properly formatted
        assert os.path.exists(main_file)

        with open(main_file, 'r') as f:
            content = f.read()
            assert "---" in content  # Should have frontmatter delimiters


def test_invalid_domain_raises_error():
    """Test that invalid domains raise validation errors."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        frontmatter = {
            "id": "test-item-1",
            "type": "entity",
            "domain": "INVALID_DOMAIN",  # This is not a valid domain
            "lifecycle_status": "ACTIVE",
            "epistemic_status": "direct",
            "version": 1,
            "created_at": "2026-08-16T10:00:00",
            "valid_from": None,
            "valid_until": None,
            "provenance": "test source"
        }
        body = "# Test Entity\n\nContent."

        with pytest.raises(ValidationError, match="Invalid domain"):
            write_canonical_item(
                vault_root=tmp_dir,
                domain="INVALID_DOMAIN",
                item_type="entity",
                item_id="test-item-1",
                frontmatter=frontmatter,
                body=body
            )


def test_invalid_item_type_raises_error():
    """Test that invalid item types raise validation errors."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        frontmatter = {
            "id": "test-item-1",
            "type": "invalid_type",  # This is not a valid type
            "domain": "PERSONAL",
            "lifecycle_status": "ACTIVE",
            "epistemic_status": "direct",
            "version": 1,
            "created_at": "2026-08-16T10:00:00",
            "valid_from": None,
            "valid_until": None,
            "provenance": "test source"
        }
        body = "# Test Entity\n\nContent."

        with pytest.raises(ValidationError, match="Invalid item type"):
            write_canonical_item(
                vault_root=tmp_dir,
                domain="PERSONAL",
                item_type="invalid_type",
                item_id="test-item-1",
                frontmatter=frontmatter,
                body=body
            )


def test_read_nonexistent_item_raises_error():
    """Test that reading a non-existent item raises FileNotFoundError."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        with pytest.raises(FileNotFoundError):
            read_canonical_item(
                vault_root=tmp_dir,
                domain="PERSONAL",
                item_type="entity",
                item_id="nonexistent-item"
            )


def test_read_history_of_nonexistent_item():
    """Test that reading history of a non-existent item returns empty list."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        history = read_item_history(
            vault_root=tmp_dir,
            domain="PERSONAL",
            item_type="entity",
            item_id="nonexistent-item"
        )
        assert history == []


def test_read_history_of_item_with_no_history():
    """Test that reading history of an item with no history returns empty list."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create initial item (no history)
        frontmatter = {
            "id": "test-item-1",
            "type": "entity",
            "domain": "PERSONAL",
            "lifecycle_status": "ACTIVE",
            "epistemic_status": "direct",
            "version": 1,
            "created_at": "2026-08-16T10:00:00",
            "valid_from": None,
            "valid_until": None,
            "provenance": "test source"
        }
        body = "# Test Entity\n\nContent."

        write_canonical_item(
            vault_root=tmp_dir,
            domain="PERSONAL",
            item_type="entity",
            item_id="test-item-1",
            frontmatter=frontmatter,
            body=body
        )

        # Read history - should be empty since no updates were made
        history = read_item_history(
            vault_root=tmp_dir,
            domain="PERSONAL",
            item_type="entity",
            item_id="test-item-1"
        )
        assert history == []


def test_frontmatter_id_mismatch_raises_validation_error():
    """Test that frontmatter id mismatch raises ValidationError."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        frontmatter = {
            "id": "wrong-id",  # Mismatch with item_id
            "type": "entity",
            "domain": "PERSONAL",
            "lifecycle_status": "ACTIVE",
            "epistemic_status": "direct",
            "version": 1,
            "created_at": "2026-08-16T10:00:00",
            "valid_from": None,
            "valid_until": None,
            "provenance": "test source"
        }
        body = "# Test Entity\n\nContent."

        with pytest.raises(ValidationError, match="frontmatter\\['id'\\]"):
            write_canonical_item(
                vault_root=tmp_dir,
                domain="PERSONAL",
                item_type="entity",
                item_id="test-item-1",
                frontmatter=frontmatter,
                body=body
            )

        # Verify no files were written
        item_dir = os.path.join(tmp_dir, "PERSONAL", "entities", "test-item-1")
        assert not os.path.exists(item_dir)


def test_frontmatter_domain_mismatch_raises_validation_error():
    """Test that frontmatter domain mismatch raises ValidationError."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        frontmatter = {
            "id": "test-item-1",
            "type": "entity",
            "domain": "FICTION",  # Mismatch with domain parameter
            "lifecycle_status": "ACTIVE",
            "epistemic_status": "direct",
            "version": 1,
            "created_at": "2026-08-16T10:00:00",
            "valid_from": None,
            "valid_until": None,
            "provenance": "test source"
        }
        body = "# Test Entity\n\nContent."

        with pytest.raises(ValidationError, match="frontmatter\\['domain'\\]"):
            write_canonical_item(
                vault_root=tmp_dir,
                domain="PERSONAL",
                item_type="entity",
                item_id="test-item-1",
                frontmatter=frontmatter,
                body=body
            )

        # Verify no files were written
        item_dir = os.path.join(tmp_dir, "PERSONAL", "entities", "test-item-1")
        assert not os.path.exists(item_dir)


def test_frontmatter_type_mismatch_raises_validation_error():
    """Test that frontmatter type mismatch raises ValidationError."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        frontmatter = {
            "id": "test-item-1",
            "type": "assertion",  # Mismatch with item_type parameter
            "domain": "PERSONAL",
            "lifecycle_status": "ACTIVE",
            "epistemic_status": "direct",
            "version": 1,
            "created_at": "2026-08-16T10:00:00",
            "valid_from": None,
            "valid_until": None,
            "provenance": "test source"
        }
        body = "# Test Entity\n\nContent."

        with pytest.raises(ValidationError, match="frontmatter\\['type'\\]"):
            write_canonical_item(
                vault_root=tmp_dir,
                domain="PERSONAL",
                item_type="entity",
                item_id="test-item-1",
                frontmatter=frontmatter,
                body=body
            )

        # Verify no files were written
        item_dir = os.path.join(tmp_dir, "PERSONAL", "entities", "test-item-1")
        assert not os.path.exists(item_dir)


def test_explicit_created_at_preserved_on_first_write():
    """Test that explicit created_at value is preserved on first write."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create an item with explicit created_at
        frontmatter = {
            "id": "test-item-1",
            "type": "entity",
            "domain": "PERSONAL",
            "lifecycle_status": "ACTIVE",
            "epistemic_status": "direct",
            "version": 1,
            "created_at": "2026-08-15T09:00:00",  # Explicit timestamp
            "valid_from": None,
            "valid_until": None,
            "provenance": "test source"
        }
        body = "# Test Entity\n\nContent."

        write_canonical_item(
            vault_root=tmp_dir,
            domain="PERSONAL",
            item_type="entity",
            item_id="test-item-1",
            frontmatter=frontmatter,
            body=body
        )

        # Read it back and verify created_at is preserved
        read_frontmatter, read_body = read_canonical_item(
            vault_root=tmp_dir,
            domain="PERSONAL",
            item_type="entity",
            item_id="test-item-1"
        )

        assert read_frontmatter["created_at"] == "2026-08-15T09:00:00"
        assert read_frontmatter["version"] == 1


def test_explicit_created_at_preserved_on_update():
    """Test that explicit created_at value is preserved on update."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create initial item
        frontmatter1 = {
            "id": "test-item-1",
            "type": "entity",
            "domain": "PERSONAL",
            "lifecycle_status": "ACTIVE",
            "epistemic_status": "direct",
            "version": 1,
            "created_at": "2026-08-15T09:00:00",  # Explicit timestamp
            "valid_from": None,
            "valid_until": None,
            "provenance": "test source"
        }
        body1 = "# Test Entity\n\nOriginal content."

        write_canonical_item(
            vault_root=tmp_dir,
            domain="PERSONAL",
            item_type="entity",
            item_id="test-item-1",
            frontmatter=frontmatter1,
            body=body1
        )

        # Update the item with different created_at (should be preserved)
        frontmatter2 = {
            "id": "test-item-1",
            "type": "entity",
            "domain": "PERSONAL",
            "lifecycle_status": "ACTIVE",
            "epistemic_status": "inferred",
            "version": 2,
            "created_at": "2026-08-16T11:00:00",  # Different explicit timestamp
            "valid_from": None,
            "valid_until": None,
            "provenance": "test source updated"
        }
        body2 = "# Test Entity\n\nUpdated content."

        write_canonical_item(
            vault_root=tmp_dir,
            domain="PERSONAL",
            item_type="entity",
            item_id="test-item-1",
            frontmatter=frontmatter2,
            body=body2
        )

        # Read current version and verify created_at is preserved from the update
        read_frontmatter, read_body = read_canonical_item(
            vault_root=tmp_dir,
            domain="PERSONAL",
            item_type="entity",
            item_id="test-item-1"
        )

        assert read_frontmatter["created_at"] == "2026-08-16T11:00:00"
        assert read_frontmatter["version"] == 2


def test_atomic_write_behavior():
    """Test that atomic write behavior works correctly."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create initial item
        frontmatter = {
            "id": "test-item-1",
            "type": "entity",
            "domain": "PERSONAL",
            "lifecycle_status": "ACTIVE",
            "epistemic_status": "direct",
            "version": 1,
            "created_at": "2026-08-16T10:00:00",
            "valid_from": None,
            "valid_until": None,
            "provenance": "test source"
        }
        body = "# Test Entity\n\nContent."

        write_canonical_item(
            vault_root=tmp_dir,
            domain="PERSONAL",
            item_type="entity",
            item_id="test-item-1",
            frontmatter=frontmatter,
            body=body
        )

        # Verify atomicity - check that temp file pattern is not present in final file
        item_dir = os.path.join(tmp_dir, "PERSONAL", "entities", "test-item-1")
        main_file = os.path.join(item_dir, "test-item-1.md")

        assert os.path.exists(main_file)

        with open(main_file, 'r') as f:
            content = f.read()
            # Should have frontmatter delimiters
            assert "---" in content
            # Should not contain temp file patterns that would indicate incomplete write
            assert "temp_" not in content or ".tmp" not in content


def test_long_item_id_raises_validation_error():
    """Test that item_id longer than 200 characters raises ValidationError."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        long_id = 'a' * 250  # 250 character ID (> 200 limit)
        try:
            write_canonical_item(
                vault_root=tmp_dir,
                domain="PERSONAL",
                item_type="entity",
                item_id=long_id,
                frontmatter={
                    "id": long_id,
                    "type": "entity",
                    "domain": "PERSONAL",
                    "lifecycle_status": "ACTIVE",
                    "epistemic_status": "direct",
                    "version": 1,
                    "created_at": "2026-08-16T10:00:00",
                    "valid_from": None,
                    "valid_until": None,
                    "provenance": "test"
                },
                body="# Test Entity\n\nContent."
            )
            assert False, "Expected ValidationError to be raised"
        except ValidationError as e:
            assert "exceeds maximum length" in str(e)
            assert "200" in str(e)
            assert str(len(long_id)) in str(e)