import { useMemo, useState } from "react";
import { ArrowRight, Database, TrendingUp } from "lucide-react";

import { CompareControls } from "./components/CompareControls";
import { FeatureMatrix } from "./components/FeatureMatrix";
import { MetricChart } from "./components/MetricChart";
import { SeasonSpotlight } from "./components/SeasonSpotlight";
import { SuggestedOutline } from "./components/SuggestedOutline";
import { clubs, metricDefinitions, outlineCards, projectScope } from "./dashboardConfig";
import {
  buildChartRows,
  getRowsForSelection,
  getSelectionSummary,
  getSpotlightRow,
  metricOptions,
  overviewStats,
  readinessCards,
  seasons,
} from "./dashboardData";
import {
  formatInteger,
  formatMoneyMillions,
  formatSeasonRange,
} from "../../shared/formatters";

export function DashboardPage() {
  const [selectedClubIds, setSelectedClubIds] = useState(["arsenal", "manchester_city", "liverpool"]);
  const [selectedMetricKey, setSelectedMetricKey] = useState("grossTransferSpendEur");
  const [startSeason, setStartSeason] = useState("2011/12");
  const [endSeason, setEndSeason] = useState("2024/25");
  const [chartType, setChartType] = useState("line");

  const selectedMetric =
    metricOptions.find((metric) => metric.key === selectedMetricKey) ?? metricDefinitions[0];

  function toggleClub(clubId) {
    setSelectedClubIds((current) => {
      if (current.includes(clubId)) {
        return current.length === 1 ? current : current.filter((value) => value !== clubId);
      }

      return [...current, clubId];
    });
  }

  function updateStartSeason(nextSeason) {
    if (seasons.indexOf(nextSeason) > seasons.indexOf(endSeason)) {
      setEndSeason(nextSeason);
    }
    setStartSeason(nextSeason);
  }

  function updateEndSeason(nextSeason) {
    if (seasons.indexOf(nextSeason) < seasons.indexOf(startSeason)) {
      setStartSeason(nextSeason);
    }
    setEndSeason(nextSeason);
  }

  const selectionRows = useMemo(
    () => getRowsForSelection(selectedClubIds, startSeason, endSeason),
    [selectedClubIds, startSeason, endSeason],
  );

  const summaryRows = useMemo(
    () => getSelectionSummary(selectedClubIds, startSeason, endSeason, selectedMetric),
    [selectedClubIds, startSeason, endSeason, selectedMetric],
  );

  const chartData = useMemo(
    () => buildChartRows(selectedClubIds, startSeason, endSeason, selectedMetric.key),
    [selectedClubIds, startSeason, endSeason, selectedMetric.key],
  );

  const topClub = summaryRows.find((row) => row.selectedValue !== null) ?? summaryRows[0];
  const spotlightClubId = selectedClubIds[0];
  const spotlightSeason = endSeason;
  const spotlightRow = getSpotlightRow(spotlightClubId, spotlightSeason);
  const selectedPeriodLabel = formatSeasonRange(startSeason, endSeason);

  const filledDataPoints = selectionRows.filter(
    (row) => row[selectedMetric.key] !== null && row[selectedMetric.key] !== undefined,
  ).length;

  return (
    <div className="pageFrame">
      <main className="pageShell">
        <header className="heroPanel panel">
          <div className="heroCopy">
            <span className="eyebrow">
              <Database size={14} />
              Demo backbone for the final product
            </span>
            <h1>Big Six spending dashboard</h1>
            <p>
              This first demo uses the repo&apos;s real exports, not placeholder tables. Transfer and
              manager views are already usable, performance and achievements are partially live, and
              finance or wage-dependent features stay transparently gated until the data catches up.
            </p>
          </div>

          <div className="heroAside">
            <div className="heroBadge">
              <span>{projectScope.league}</span>
              <strong>
                {projectScope.seasonFrom} to {projectScope.seasonTo}
              </strong>
            </div>
            <div className="heroCallout">
              <TrendingUp size={18} />
              <div>
                <strong>Current view</strong>
                <span>{selectedMetric.label}</span>
              </div>
              <ArrowRight size={18} />
            </div>
          </div>
        </header>

        <section className="statsGrid">
          {overviewStats.map((stat) => (
            <article key={stat.label} className="panel statCard">
              <span>{stat.label}</span>
              <strong>{stat.value}</strong>
              <small>{stat.note}</small>
            </article>
          ))}
        </section>

        <FeatureMatrix cards={readinessCards} />

        <section className="layoutGrid">
          <CompareControls
            chartType={chartType}
            endSeason={endSeason}
            metricOptions={metricOptions}
            selectedClubIds={selectedClubIds}
            selectedMetric={selectedMetric}
            seasons={seasons}
            setChartType={setChartType}
            setEndSeason={updateEndSeason}
            setSelectedMetricKey={setSelectedMetricKey}
            setStartSeason={updateStartSeason}
            startSeason={startSeason}
            toggleClub={toggleClub}
          />

          <section className="contentColumn">
            <section className="panel summaryPanel">
              <div className="sectionHeading">
                <div>
                  <span className="eyebrow">Active compare view</span>
                  <h2>
                    {selectedMetric.label} across {selectedPeriodLabel}
                  </h2>
                </div>
                <p>
                  {filledDataPoints}/{selectionRows.length} selected club-season rows currently have
                  usable values for this metric.
                </p>
              </div>

              <div className="summaryTiles">
                <article className="miniCard">
                  <span>Selected clubs</span>
                  <strong>{selectedClubIds.length}</strong>
                  <small>{selectedClubIds.map((clubId) => clubs.find((club) => club.id === clubId)?.name).join(", ")}</small>
                </article>

                <article className="miniCard">
                  <span>Period</span>
                  <strong>{selectedPeriodLabel}</strong>
                  <small>{selectionRows.length} club-season rows in the current selection</small>
                </article>

                <article className="miniCard">
                  <span>Highest aggregate</span>
                  <strong>{topClub?.name ?? "Data pending"}</strong>
                  <small>
                    {topClub?.selectedValue === null
                      ? "No usable values yet"
                      : selectedMetric.formatter(topClub.selectedValue)}
                  </small>
                </article>

                <article className="miniCard">
                  <span>Metric coverage</span>
                  <strong>{selectedMetric.coverage}</strong>
                  <small>{selectedMetric.description}</small>
                </article>
              </div>
            </section>

            <section className="panel">
              <div className="sectionHeading">
                <div>
                  <span className="eyebrow">Trend chart</span>
                  <h2>{selectedMetric.label}</h2>
                </div>
                <p>
                  Ready metrics are fully usable now. Partial ones expose real gaps rather than
                  smoothing over them.
                </p>
              </div>

              <MetricChart
                chartData={chartData}
                chartType={chartType}
                metric={selectedMetric}
                selectedClubIds={selectedClubIds}
              />
            </section>

            <section className="panel tablePanel">
              <div className="sectionHeading">
                <div>
                  <span className="eyebrow">Selection summary</span>
                  <h2>Club ranking for this view</h2>
                </div>
                <p>
                  The table uses the selected metric for ranking, while still keeping supporting
                  counts visible.
                </p>
              </div>

              <div className="tableWrap">
                <table>
                  <thead>
                    <tr>
                      <th>Club</th>
                      <th>{selectedMetric.shortLabel}</th>
                      <th>Metric rows</th>
                      <th>Managers covered</th>
                      <th>Achievement rows</th>
                    </tr>
                  </thead>
                  <tbody>
                    {summaryRows.map((row) => (
                      <tr key={row.id ?? row.name}>
                        <td>
                          <span className="clubCell">
                            <span className="clubSwatch" style={{ background: row.color }} />
                            <strong>{row.name}</strong>
                          </span>
                        </td>
                        <td>
                          {row.selectedValue === null
                            ? "Data pending"
                            : selectedMetric.formatter(row.selectedValue)}
                        </td>
                        <td>{formatInteger(row.dataPoints)}</td>
                        <td>{formatInteger(row.managersCovered)}</td>
                        <td>{formatInteger(row.achievementsCovered)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>

            <SeasonSpotlight row={spotlightRow} />

            <section className="panel calloutPanel">
              <div>
                <span className="eyebrow">What happens next</span>
                <h2>The next dataset wins are clear</h2>
              </div>

              <div className="calloutGrid">
                <article className="miniCard">
                  <span>1. Revenue normalization</span>
                  <strong>Unlock finance charts</strong>
                  <small>
                    We already have extracted accounts data. The missing step is a consistent EUR
                    comparison layer and cleaner master joins.
                  </small>
                </article>

                <article className="miniCard">
                  <span>2. Wage pipeline</span>
                  <strong>Unlock efficiency metrics</strong>
                  <small>
                    Once wages are populated, raw player cost, wage-to-revenue ratio, and
                    spend-efficiency sections become real.
                  </small>
                </article>

                <article className="miniCard">
                  <span>3. Achievement cleanup</span>
                  <strong>Complete context views</strong>
                  <small>
                    Filling the remaining achievement gaps will make trophy and qualification
                    context consistent across the full window.
                  </small>
                </article>
              </div>
            </section>
          </section>
        </section>

        <SuggestedOutline cards={outlineCards} />
      </main>
    </div>
  );
}
