"""
Typed exceptions for the proposal review workflow.
"""


class ReviewError(Exception):
    """Base class for all review/ module errors."""


class ValidationError(ReviewError):
    """Raised when frontmatter is missing/invalid, on read or write."""


class ProposalNotFoundError(ReviewError):
    """Raised when proposal_id does not resolve to a file under <domain>/proposals/."""


class SourceNotFoundError(ReviewError):
    """Raised when provenance.source_id does not resolve to a file under <domain>/sources/."""


class DomainMismatchError(ReviewError):
    """Raised when the caller-supplied domain does not match the proposal's own domain field."""


class InvalidProposalStatusError(ReviewError):
    """Raised when accept/reject/edit is attempted on a proposal whose proposal_status is not
    one of the statuses that operation currently accepts ('PROPOSED' or 'EDITED', for all three)."""


class UnsupportedProposalTypeError(ReviewError):
    """Raised when proposed_item_type is not one of the recognized
    'assertion'/'entity'/'event'/'relationship' values."""


class UnresolvedRelationshipEndpointError(ReviewError):
    """Raised when accepting a relationship proposal whose endpoints include at least one
    identifier that matches another proposal in the same domain that is not yet ACCEPTED."""


class InvalidDomainError(ReviewError):
    """Raised when domain is not one of the allowed domains."""


class UneditableFieldError(ReviewError):
    """Raised when field_updates contains a key outside the allow-list for the proposal's proposed_item_type."""
