import { inflationConfig, VALUE_BASIS, valueBasisOptions } from "../config/valueBasis";
import { clubConfigs } from "../config/clubConfig";
import { displayCurrencyOptions, fxReference } from "../config/displayCurrency";
import { ClubMarker } from "./ClubMarker";
import { CoverageBadge } from "./CoverageBadge";

export function CompareControls({
  chartType,
  endSeason,
  metricCoverageById,
  metricGroups,
  onChartTypeChange,
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
  return (
    <aside className="controlsColumn panel">
      <div className="panelLead">
        <span className="eyebrow">Compare clubs</span>
        <h2>Choose clubs, seasons, and one metric</h2>
        <p>
          The compare beta stays focused on squad investment. Metrics remain visible even when
          their data layer is still partial or still being finalized.
        </p>
      </div>

      <section className="controlSection">
        <div className="controlHeader">
          <h3>Clubs</h3>
        </div>
        <div className="clubPicker">
          {clubConfigs.map((club) => {
            const selected = selectedClubIds.includes(club.id);
            return (
              <button
                key={club.id}
                type="button"
                className={`clubToggle ${selected ? "isSelected" : ""}`}
                onClick={() => onToggleClub(club.id)}
              >
                <ClubMarker club={club} size={18} />
                <span>{club.name}</span>
              </button>
            );
          })}
        </div>
      </section>

      <section className="controlSection splitInputs">
        <div>
          <div className="controlHeader">
            <h3>Start season</h3>
          </div>
          <select value={startSeason} onChange={(event) => onStartSeasonChange(event.target.value)}>
            {seasons.map((season) => (
              <option key={season} value={season}>
                {season}
              </option>
            ))}
          </select>
        </div>

        <div>
          <div className="controlHeader">
            <h3>End season</h3>
          </div>
          <select value={endSeason} onChange={(event) => onEndSeasonChange(event.target.value)}>
            {seasons.map((season) => (
              <option key={season} value={season}>
                {season}
              </option>
            ))}
          </select>
        </div>
      </section>

      <section className="controlSection">
        <div className="controlHeader">
          <h3>Metric</h3>
        </div>
        <div className="metricGroups">
          {metricGroups.map((group) => (
            <div key={group.id} className="metricGroup">
              <span className="metricGroupLabel">{group.label}</span>
              <div className="metricGrid">
                {group.metrics.map((metric) => {
                  const coverage = metricCoverageById[metric.id].coverage;
                  const disabled = coverage.status === "coming-soon";
                  return (
                    <button
                      key={metric.id}
                      type="button"
                      className={`metricButton ${selectedMetricId === metric.id ? "isActive" : ""}`}
                      disabled={disabled}
                      onClick={() => onMetricChange(metric.id)}
                    >
                      <span className="metricButtonTop">
                        <strong>{metric.label}</strong>
                        <CoverageBadge coverage={coverage} quiet />
                      </span>
                      <small>{metric.description}</small>
                    </button>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="controlSection">
        <div className="controlHeader">
          <h3>Currency</h3>
        </div>
        <div className="chartToggleRow">
          {displayCurrencyOptions.map((option) => (
            <button
              key={option.id}
              type="button"
              className={`secondaryButton ${displayCurrency === option.id ? "isActive" : ""}`}
              onClick={() => onDisplayCurrencyChange(option.id)}
            >
              {option.label}
            </button>
          ))}
        </div>
        <p className="controlNote">
          {fxReference.description}
        </p>
      </section>

      <section className="controlSection">
        <div className="controlHeader">
          <h3>Values</h3>
        </div>
        <div className="chartToggleRow">
          {valueBasisOptions.map((option) => (
            <button
              key={option.id}
              type="button"
              className={`secondaryButton ${valueBasis === option.id ? "isActive" : ""}`}
              onClick={() => onValueBasisChange(option.id)}
              disabled={option.disabled}
            >
              {option.label}
            </button>
          ))}
        </div>
        <p className="controlNote">
          {valueBasis === VALUE_BASIS.inflationAdjusted
            ? `Inflation adjusted to ${inflationConfig.baseSeason} prices.`
            : `Switch to inflation-adjusted values to restate money figures in ${inflationConfig.baseSeason} prices.`}
        </p>
      </section>

      <section className="controlSection">
        <div className="controlHeader">
          <h3>Chart</h3>
        </div>
        <div className="chartToggleRow">
          {["line", "bar"].map((option) => (
            <button
              key={option}
              type="button"
              className={`secondaryButton ${chartType === option ? "isActive" : ""}`}
              onClick={() => onChartTypeChange(option)}
            >
              {option === "line" ? "Line" : "Bar"}
            </button>
          ))}
        </div>
      </section>
    </aside>
  );
}
