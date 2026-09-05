import { get, post, buildListUrl } from "./client.js";

export function listProposals(domain, opts = {}) {
  return get(buildListUrl(`/domains/${domain}/proposals`, opts));
}

export function getProposal(domain, id) {
  return get(`/domains/${domain}/proposals/${id}`);
}

export function acceptProposal(domain, id, reviewerId) {
  return post(`/domains/${domain}/proposals/${id}/accept`, { reviewer_id: reviewerId });
}

export function rejectProposal(domain, id, reviewerId, reason) {
  return post(`/domains/${domain}/proposals/${id}/reject`, {
    reviewer_id: reviewerId,
    reason: reason || null,
  });
}

export function editProposal(domain, id, reviewerId, { body, fieldUpdates } = {}) {
  return post(`/domains/${domain}/proposals/${id}/edit`, {
    reviewer_id: reviewerId,
    body: body ?? null,
    field_updates: fieldUpdates ?? null,
  });
}

export function listOrganizationFolders(domain, itemType) {
  return get(`/domains/${domain}/organization-folders?item_type=${encodeURIComponent(itemType)}`);
}
