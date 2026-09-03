const DAY_MS = 24 * 60 * 60 * 1000;

export const PERIOD_OPTIONS = [
  { value: "all", label: "Toute période" },
  { value: "today", label: "Aujourd'hui" },
  { value: "week", label: "Cette semaine" },
  { value: "month", label: "Ce mois" },
];

function periodCutoffMs(period) {
  if (period === "today") {
    const now = new Date();
    return new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
  }
  if (period === "week") return Date.now() - 7 * DAY_MS;
  if (period === "month") return Date.now() - 30 * DAY_MS;
  return null;
}

export function filterByPeriod(items, period, getTimestamp) {
  const cutoff = periodCutoffMs(period);
  if (cutoff === null) return items;
  return items.filter((item) => {
    const ts = new Date(getTimestamp(item)).getTime();
    return !Number.isNaN(ts) && ts >= cutoff;
  });
}
