import { compareMetricGroups } from "../config/metricRegistry";
import { clubConfigs } from "../config/clubConfig";
import { CoverageBadge } from "./CoverageBadge";

export function CompareControls({
  chartType,
  endSeason,
  onChartTypeChange,
  onEndSeasonChange,
  onMetricChange,
  onStartSeasonChange,
  onToggleClub,
  seasons,
  selectedClubIds,
  selectedMetricId,
  startSeason,
  metricCoverageById,
}) {
  return (
    <aside className="controlsColumn panel">
      <div className="panelLead">
        <span className="eyebrow">Compare clubs</span>
        <h2>Choose clubs, seasons, and a metric</h2>
        <p>
          Incomplete metrics stay visible. If a metric is only partly ready, the compare view makes
          that explicit instead of filling the gaps with fake values.
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
                <span className="clubToggleSwatch" style={{ background: club.colors.primary }} />
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
          {compareMetricGroups.map((group) => (
            <div key={group.id} className="metricGroup">
              <span className="metricGroupLabel">{group.label}</span>
              <div className="metricGrid">
                {group.metricIds.map((metricId) => {
                  const metric = metricCoverageById[metricId].metric;
                  const coverage = metricCoverageById[metricId].coverage;
                  const disabled = coverage.status === "coming-soon" && !metric.compareEnabled;
                  return (
                    <button
                      key={metricId}
                      type="button"
                      className={`metricButton ${selectedMetricId === metricId ? "isActive" : ""}`}
                      disabled={disabled}
                      onClick={() => onMetricChange(metricId)}
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
