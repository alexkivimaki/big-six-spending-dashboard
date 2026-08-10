import { Filter, Lock } from "lucide-react";

import { chartTypes, clubById } from "../dashboardConfig";
import { statusLabel } from "../../../shared/formatters";

function groupByDomain(metrics) {
  return metrics.reduce((groups, metric) => {
    if (!groups[metric.domain]) groups[metric.domain] = [];
    groups[metric.domain].push(metric);
    return groups;
  }, {});
}

export function CompareControls({
  chartType,
  endSeason,
  metricOptions,
  selectedClubIds,
  selectedMetric,
  seasons,
  setChartType,
  setEndSeason,
  setSelectedMetricKey,
  setStartSeason,
  startSeason,
  toggleClub,
}) {
  const metricsByDomain = groupByDomain(metricOptions);

  return (
    <aside className="panel controlsPanel">
      <div className="panelHeader">
        <span className="eyebrow">
          <Filter size={14} />
          Demo controls
        </span>
        <h2>Compare the layers we already trust</h2>
        <p>
          The controls expose the final app shape now. Features with incomplete data stay visible,
          but disabled, so the UI does not pretend the dataset is more complete than it is.
        </p>
      </div>

      <section className="controlBlock">
        <div className="blockHeader">
          <h3>Clubs</h3>
          <small>Pick at least one</small>
        </div>
        <div className="clubGrid">
          {Object.values(clubById).map((club) => {
            const selected = selectedClubIds.includes(club.id);
            return (
              <button
                key={club.id}
                type="button"
                className={`clubChip ${selected ? "isSelected" : ""}`}
                onClick={() => toggleClub(club.id)}
              >
                <span className="clubSwatch" style={{ background: club.color }} />
                <span>{club.name}</span>
              </button>
            );
          })}
        </div>
      </section>

      <section className="controlBlock">
        <div className="blockHeader">
          <h3>Metrics</h3>
          <small>Ready, partial, and blocked are all shown</small>
        </div>

        {Object.entries(metricsByDomain).map(([domain, metrics]) => (
          <div key={domain} className="metricGroup">
            <div className="metricGroupLabel">{domain}</div>
            <div className="metricGrid">
              {metrics.map((metric) => {
                const active = selectedMetric.key === metric.key;
                const blocked = metric.status === "blocked";

                return (
                  <button
                    key={metric.key}
                    type="button"
                    className={`metricCard ${active ? "isActive" : ""} ${blocked ? "isBlocked" : ""}`}
                    disabled={blocked}
                    onClick={() => setSelectedMetricKey(metric.key)}
                  >
                    <div className="metricTopline">
                      <strong>{metric.shortLabel}</strong>
                      <span className={`statusPill status-${metric.status}`}>{statusLabel(metric.status)}</span>
                    </div>
                    <span className="metricCoverage">{metric.coverage}</span>
                    <small>{metric.description}</small>
                    {blocked ? (
                      <span className="metricLock">
                        <Lock size={12} />
                        Waiting on missing data
                      </span>
                    ) : null}
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </section>

      <section className="controlBlock splitBlock">
        <div>
          <div className="blockHeader">
            <h3>From</h3>
          </div>
          <select value={startSeason} onChange={(event) => setStartSeason(event.target.value)}>
            {seasons.map((season) => (
              <option key={season} value={season}>
                {season}
              </option>
            ))}
          </select>
        </div>

        <div>
          <div className="blockHeader">
            <h3>To</h3>
          </div>
          <select value={endSeason} onChange={(event) => setEndSeason(event.target.value)}>
            {seasons.map((season) => (
              <option key={season} value={season}>
                {season}
              </option>
            ))}
          </select>
        </div>
      </section>

      <section className="controlBlock">
        <div className="blockHeader">
          <h3>Chart type</h3>
        </div>
        <div className="toggleRow">
          {chartTypes.map((option) => {
            const Icon = option.icon;
            return (
              <button
                key={option.key}
                type="button"
                className={`toggleButton ${chartType === option.key ? "isActive" : ""}`}
                onClick={() => setChartType(option.key)}
              >
                <Icon size={15} />
                {option.label}
              </button>
            );
          })}
        </div>
      </section>
    </aside>
  );
}
