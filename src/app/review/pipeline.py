"""
Proposal review workflow orchestration: list, retrieve, accept, reject.
"""
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from . import storage
from .errors import (
    DomainMismatchError,
    InvalidProposalStatusError,
    UnsupportedProposalTypeError,
    ValidationError,
)


@dataclass
class ProposalSummary:
    id: str
    domain: str
    proposal_status: str
    proposed_item_type: str
    epistemic_status: str
    created_at: str


@dataclass
class ProposalDetail:
    id: str
    domain: str
    frontmatter: dict[str, Any]
    body: str
    source_frontmatter: dict[str, Any]
    source_body: str


@dataclass
class AcceptResult:
    proposal_id: str
    assertion_id: str
    assertion_path: Path
    reviewed_by: str
    reviewed_at: str


@dataclass
class RejectResult:
    proposal_id: str
    reviewed_by: str
    reviewed_at: str
    rejection_reason: Optional[str]


def list_proposals(vault_root: Path, domain: str, status: Optional[str] = None) -> list[ProposalSummary]:
    storage._validate_domain(domain)

    summaries = []
    for proposal_id in storage.list_proposal_ids(vault_root, domain):
        try:
            frontmatter, _ = storage.read_proposal_file(vault_root, domain, proposal_id)
            storage._validate_frontmatter(frontmatter, storage.REQUIRED_PROPOSAL_FIELDS)
        except ValidationError:
            # A single malformed proposal file must not break the whole review queue.
            continue

        if frontmatter["domain"] != domain:
            continue
        if status is not None and frontmatter["proposal_status"] != status:
            continue

        summaries.append(ProposalSummary(
            id=frontmatter["id"],
            domain=frontmatter["domain"],
            proposal_status=frontmatter["proposal_status"],
            proposed_item_type=frontmatter["proposed_item_type"],
            epistemic_status=frontmatter["epistemic_status"],
            created_at=frontmatter["created_at"],
        ))

    return summaries


def get_proposal(vault_root: Path, domain: str, proposal_id: str) -> ProposalDetail:
    storage._validate_domain(domain)
    frontmatter, body = storage.read_proposal_file(vault_root, domain, proposal_id)
    storage._validate_frontmatter(frontmatter, storage.REQUIRED_PROPOSAL_FIELDS)

    if frontmatter["domain"] != domain:
        raise DomainMismatchError(
            f"Proposal '{proposal_id}' belongs to domain '{frontmatter['domain']}', not '{domain}'"
        )

    source_id = frontmatter["provenance"].get("source_id")
    if not source_id:
        raise ValidationError(f"Proposal '{proposal_id}' has no provenance.source_id")

    source_frontmatter, source_body = storage.read_source_file(vault_root, domain, source_id)

    return ProposalDetail(
        id=frontmatter["id"],
        domain=frontmatter["domain"],
        frontmatter=frontmatter,
        body=body,
        source_frontmatter=source_frontmatter,
        source_body=source_body,
    )


def _load_and_validate_for_review(
    vault_root: Path, domain: str, proposal_id: str, reviewer_id: str
) -> tuple[dict[str, Any], str]:
    storage._validate_domain(domain)
    frontmatter, body = storage.read_proposal_file(vault_root, domain, proposal_id)
    storage._validate_frontmatter(frontmatter, storage.REQUIRED_PROPOSAL_FIELDS)

    if frontmatter["domain"] != domain:
        raise DomainMismatchError(
            f"Proposal '{proposal_id}' belongs to domain '{frontmatter['domain']}', not '{domain}'"
        )
    if frontmatter["proposed_item_type"] != "assertion":
        raise UnsupportedProposalTypeError(
            f"Proposal '{proposal_id}' has proposed_item_type "
            f"'{frontmatter['proposed_item_type']}', only 'assertion' is supported"
        )
    if frontmatter["proposal_status"] != "PROPOSED":
        raise InvalidProposalStatusError(
            f"Proposal '{proposal_id}' has status '{frontmatter['proposal_status']}', "
            f"expected 'PROPOSED'"
        )
    if not reviewer_id:
        raise ValidationError("reviewer_id is required")

    return frontmatter, body


def accept_proposal(vault_root: Path, domain: str, proposal_id: str, reviewer_id: str) -> AcceptResult:
    frontmatter, body = _load_and_validate_for_review(vault_root, domain, proposal_id, reviewer_id)

    assertion_id = storage._generate_assertion_id()
    now = datetime.now().isoformat()

    assertion_frontmatter = {
        "id": assertion_id,
        "type": "assertion",
        "domain": domain,
        "epistemic_status": frontmatter["epistemic_status"],
        "lifecycle_status": "ACTIVE",
        "valid_from": frontmatter["valid_from"],
        "valid_until": frontmatter["valid_until"],
        "created_at": now,
        "provenance": {
            "source_id": frontmatter["provenance"]["source_id"],
            "extraction_provider": frontmatter["provenance"]["extraction_provider"],
            "proposal_id": proposal_id,
            "reviewed_by": reviewer_id,
            "reviewed_at": now,
        },
    }

    # Must fully succeed (atomic write) before the proposal is touched: a failed
    # assertion write must leave the proposal at PROPOSED, never partially accepted.
    written_path = storage.write_assertion_file(vault_root, domain, assertion_frontmatter, body)

    frontmatter["proposal_status"] = "ACCEPTED"
    frontmatter["reviewed_by"] = reviewer_id
    frontmatter["reviewed_at"] = now
    frontmatter["resulting_item_id"] = assertion_id
    frontmatter["rejection_reason"] = None
    storage.write_proposal_file_in_place(vault_root, domain, proposal_id, frontmatter, body)

    return AcceptResult(
        proposal_id=proposal_id,
        assertion_id=assertion_id,
        assertion_path=written_path,
        reviewed_by=reviewer_id,
        reviewed_at=now,
    )


def reject_proposal(
    vault_root: Path, domain: str, proposal_id: str, reviewer_id: str, reason: Optional[str] = None
) -> RejectResult:
    frontmatter, body = _load_and_validate_for_review(vault_root, domain, proposal_id, reviewer_id)

    now = datetime.now().isoformat()
    frontmatter["proposal_status"] = "REJECTED"
    frontmatter["reviewed_by"] = reviewer_id
    frontmatter["reviewed_at"] = now
    frontmatter["resulting_item_id"] = None
    frontmatter["rejection_reason"] = reason
    storage.write_proposal_file_in_place(vault_root, domain, proposal_id, frontmatter, body)

    return RejectResult(
        proposal_id=proposal_id,
        reviewed_by=reviewer_id,
        reviewed_at=now,
        rejection_reason=reason,
    )
