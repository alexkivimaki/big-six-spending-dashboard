export function formatMoneyMillions(value, currencySymbol = "EUR") {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "Data pending";
  }

  const amount = Number(value);
  const sign = amount < 0 ? "-" : "";
  const abs = Math.abs(amount);
  const inMillions = abs / 1_000_000;
  const symbol = currencySymbol === "GBP" ? "PS" : "EUR";

  if (inMillions >= 1000) {
    return `${sign}${symbol} ${(inMillions / 1000).toFixed(2)}bn`;
  }

  return `${sign}${symbol} ${inMillions.toFixed(1)}m`;
}

export function formatInteger(value) {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "Data pending";
  }

  return Number(value).toFixed(0);
}

export function formatDecimal(value, digits = 1) {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "Data pending";
  }

  return Number(value).toFixed(digits);
}

export function formatPercent(value) {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "Data pending";
  }

  return `${(Number(value) * 100).toFixed(1)}%`;
}

export function formatSeasonRange(startSeason, endSeason) {
  return `${startSeason} to ${endSeason}`;
}

export function statusLabel(status) {
  if (status === "ready") return "Ready";
  if (status === "partial") return "Partial";
  return "Blocked";
}
