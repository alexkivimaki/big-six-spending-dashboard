export function isMissing(value) {
  return value === null || value === undefined || Number.isNaN(value);
}

export function formatCurrencyCompact(value, currency = "EUR", fallback = "—") {
  if (isMissing(value)) return fallback;

  const numeric = Number(value);
  const sign = numeric < 0 ? "-" : "";
  const absolute = Math.abs(numeric);
  const symbol = currency === "GBP" ? "£" : currency === "USD" ? "$" : "€";

  if (absolute >= 1_000_000_000) {
    return `${sign}${symbol}${(absolute / 1_000_000_000).toFixed(2)}bn`;
  }

  if (absolute >= 1_000_000) {
    return `${sign}${symbol}${(absolute / 1_000_000).toFixed(0)}m`;
  }

  if (absolute >= 1_000) {
    return `${sign}${symbol}${(absolute / 1_000).toFixed(0)}k`;
  }

  return `${sign}${symbol}${absolute.toFixed(0)}`;
}

export function formatCount(value, fallback = "—") {
  if (isMissing(value)) return fallback;
  return Number(value).toFixed(0);
}

export function formatPercent(value, fallback = "—") {
  if (isMissing(value)) return fallback;
  return `${(Number(value) * 100).toFixed(1)}%`;
}

export function formatLeaguePosition(value, fallback = "—") {
  if (isMissing(value)) return fallback;
  return `${Number(value).toFixed(0)}`;
}

export function formatSeasonRange(startSeason, endSeason) {
  return `${startSeason} to ${endSeason}`;
}

export function formatCoverageText(filled, total) {
  if (!total) return "0% coverage";
  return `${Math.round((filled / total) * 100)}% coverage`;
}

export function formatCoverageFraction(filled, total) {
  return `${filled}/${total}`;
}

export function getCoverageLabel(status, filled, total) {
  if (status === "complete") return "Complete";
  if (status === "coming-soon") return "Coming soon";
  return `Partial data · ${formatCoverageText(filled, total)}`;
}

export function formatSourceDate(value, fallback = "—") {
  if (!value) return fallback;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return date.toISOString().slice(0, 10);
}
