import { get, postForm, buildListUrl } from "./client.js";

export function listIngestions(domain, opts = {}) {
  return get(buildListUrl(`/domains/${domain}/ingestions`, opts));
}

export function listExtractions(domain, opts = {}) {
  return get(buildListUrl(`/domains/${domain}/extractions`, opts));
}

export function startIngestionUpload(domain, file) {
  const formData = new FormData();
  formData.append("file", file);
  return postForm(`/domains/${domain}/ingestions/upload`, formData);
}

export function getIngestion(domain, taskId) {
  return get(`/domains/${domain}/ingestions/${taskId}`);
}
