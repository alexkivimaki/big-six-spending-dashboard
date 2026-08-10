import { getCoverageLabel } from "../shared/formatters";

export function CoverageBadge({ coverage, quiet = false }) {
  const label = getCoverageLabel(coverage.status, coverage.filled, coverage.total);
  return (
    <span className={`coverageBadge status-${coverage.status} ${quiet ? "isQuiet" : ""}`}>
      {label}
    </span>
  );
}
