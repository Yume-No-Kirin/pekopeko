import { get, buildListUrl } from "./client.js";

export function listIngestions(domain, opts = {}) {
  return get(buildListUrl(`/domains/${domain}/ingestions`, opts));
}

export function listExtractions(domain, opts = {}) {
  return get(buildListUrl(`/domains/${domain}/extractions`, opts));
}
