import { ChevronDown } from "lucide-react";

import { valueBasisOptions } from "../config/valueBasis";
import { clubConfigs } from "../config/clubConfig";
import { displayCurrencyOptions } from "../config/displayCurrency";
import { ClubMarker } from "./ClubMarker";

export function CompareControls({
  className = "",
  endSeason,
  metricCoverageById,
  metricGroups,
  onEndSeasonChange,
  onMetricChange,
  onStartSeasonChange,
  onToggleClub,
  onDisplayCurrencyChange,
  onValueBasisChange,
  displayCurrency,
  seasons,
  selectedClubIds,
  selectedMetricId,
  startSeason,
  valueBasis,
}) {
  const classes = ["compareControlsCompact", className].filter(Boolean).join(" ");
  const currencySymbols = {
    EUR: "€",
    GBP: "£",
    USD: "$",
  };

  return (
    <div className={classes}>
      <div className="compactField compactFieldClubs">
        <span>Clubs to compare</span>
        <div className="clubBadgeSelector" aria-label="Clubs to compare">
          {clubConfigs.map((club) => {
            const selected = selectedClubIds.includes(club.id);
            const disabled = selected && selectedClubIds.length === 1;
            return (
              <button
                key={club.id}
                type="button"
                className={`clubBadgeButton ${selected ? "isSelected" : ""}`}
                onClick={() => onToggleClub(club.id)}
                disabled={disabled}
                aria-label={club.name}
                title={club.name}
              >
                <ClubMarker club={club} size={18} />
              </button>
            );
          })}
        </div>
      </div>

      <label className="compactField">
        <span>Start</span>
        <div className="compactSelectShell">
          <select value={startSeason} onChange={(event) => onStartSeasonChange(event.target.value)}>
            {seasons.map((season) => (
              <option key={season} value={season}>
                {season}
              </option>
            ))}
          </select>
          <ChevronDown size={16} className="compactSelectChevron" />
        </div>
      </label>

      <label className="compactField">
        <span>End</span>
        <div className="compactSelectShell">
          <select value={endSeason} onChange={(event) => onEndSeasonChange(event.target.value)}>
            {seasons.map((season) => (
              <option key={season} value={season}>
                {season}
              </option>
            ))}
          </select>
          <ChevronDown size={16} className="compactSelectChevron" />
        </div>
      </label>

      <label className="compactField compactFieldMetric">
        <span>Metric</span>
        <div className="compactSelectShell">
          <select value={selectedMetricId} onChange={(event) => onMetricChange(event.target.value)}>
            {metricGroups.map((group) => (
              <optgroup key={group.id} label={group.label}>
                {group.metrics.map((metric) => {
                  const coverage = metricCoverageById[metric.id].coverage;
                  const suffix =
                    coverage.status === "coming-soon"
                      ? " · Coming soon"
                      : coverage.status === "partial"
                        ? " · Partial"
                        : "";
                  return (
                    <option key={metric.id} value={metric.id} disabled={coverage.status === "coming-soon"}>
                      {metric.label}
                      {suffix}
                    </option>
                  );
                })}
              </optgroup>
            ))}
          </select>
          <ChevronDown size={16} className="compactSelectChevron" />
        </div>
      </label>

      <div className="compactToggleField">
        <span>Currency</span>
        <div className="compactToggleGroup" aria-label="Display currency">
          {displayCurrencyOptions.map((option) => (
            <button
              key={option.id}
              type="button"
              className={`compactToggleButton ${displayCurrency === option.id ? "isActive" : ""}`}
              onClick={() => onDisplayCurrencyChange(option.id)}
              aria-label={option.label}
              title={option.label}
            >
              <span aria-hidden="true">{currencySymbols[option.id] ?? option.label}</span>
            </button>
          ))}
        </div>
      </div>

      <div className="compactToggleField compactToggleFieldWide">
        <span>Values</span>
        <div className="compactToggleGroup compactToggleGroupWide" aria-label="Value basis">
          {valueBasisOptions.map((option) => (
            <button
              key={option.id}
              type="button"
              className={`compactToggleButton ${valueBasis === option.id ? "isActive" : ""}`}
              onClick={() => onValueBasisChange(option.id)}
              disabled={option.disabled}
              aria-label={option.label}
              title={option.label}
            >
              <span>{option.label}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
