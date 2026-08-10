import { useMemo, useState } from "react";

import { CompareControls } from "../components/CompareControls";
import { ComparisonChart } from "../components/ComparisonChart";
import { ComparisonRanking } from "../components/ComparisonRanking";
import { SectionHeader } from "../components/SectionHeader";
import { SourceDrawer } from "../components/SourceDrawer";
import { clubConfigs } from "../config/clubConfig";
import { getMetric } from "../config/metricRegistry";
import {
  comparisonSeasons,
  getCompareSourceSections,
  getComparisonChartData,
  getComparisonRanking,
  getMetricCoverage,
  getMetricOptionsForCompare,
  getRowsInRange,
} from "../lib/dataModel";
import { formatSeasonRange } from "../shared/formatters";

export function ComparePage() {
  const [selectedClubIds, setSelectedClubIds] = useState(["arsenal", "chelsea", "liverpool"]);
  const [startSeason, setStartSeason] = useState("2011/12");
  const [endSeason, setEndSeason] = useState("2024/25");
  const [selectedMetricId, setSelectedMetricId] = useState("netTransferSpend");
  const [chartType, setChartType] = useState("line");
  const [sourcePanel, setSourcePanel] = useState(null);

  const selectedMetric = getMetric(selectedMetricId);
  const selectedRows = useMemo(
    () => getRowsInRange(selectedClubIds, startSeason, endSeason),
    [selectedClubIds, startSeason, endSeason],
  );

  const metricCoverageById = useMemo(() => {
    const records = {};
    for (const group of getMetricOptionsForCompare()) {
      for (const metric of group.metrics) {
        records[metric.id] = {
          metric,
          coverage: getMetricCoverage(metric.id, selectedRows, { compareMode: true }),
        };
      }
    }
    return records;
  }, [selectedRows]);

  const chartData = useMemo(
    () => getComparisonChartData(selectedClubIds, startSeason, endSeason, selectedMetricId),
    [selectedClubIds, startSeason, endSeason, selectedMetricId],
  );

  const ranking = useMemo(
    () => getComparisonRanking(selectedClubIds, startSeason, endSeason, selectedMetricId),
    [selectedClubIds, startSeason, endSeason, selectedMetricId],
  );

  const selectionLabel = formatSeasonRange(startSeason, endSeason);

  function toggleClub(clubId) {
    setSelectedClubIds((current) => {
      if (current.includes(clubId)) {
        return current.length === 1 ? current : current.filter((value) => value !== clubId);
      }
      return [...current, clubId];
    });
  }

  function changeStartSeason(nextSeason) {
    if (comparisonSeasons.indexOf(nextSeason) > comparisonSeasons.indexOf(endSeason)) {
      setEndSeason(nextSeason);
    }
    setStartSeason(nextSeason);
  }

  function changeEndSeason(nextSeason) {
    if (comparisonSeasons.indexOf(nextSeason) < comparisonSeasons.indexOf(startSeason)) {
      setStartSeason(nextSeason);
    }
    setEndSeason(nextSeason);
  }

  function openMetricSourcePanel() {
    setSourcePanel({
      title: selectedMetric.label,
      subtitle: `${selectionLabel} · ${selectedClubIds.length} selected clubs`,
      sections: getCompareSourceSections(selectedMetricId, selectedClubIds, startSeason, endSeason),
    });
  }

  return (
    <>
      <section className="pageHero panel">
        <div>
          <span className="eyebrow">Compare</span>
          <h1>Compare clubs across spend, finance, and performance</h1>
          <p>
            The beta focuses on one job: compare how the Big Six spend, earn, and convert those
            resources into results, while staying honest about incomplete data.
          </p>
        </div>

        <div className="heroStats">
          <div className="heroStat">
            <span>Selected clubs</span>
            <strong>{selectedClubIds.length}</strong>
            <small>{selectedClubIds.map((clubId) => clubConfigs.find((club) => club.id === clubId)?.shortName).join(", ")}</small>
          </div>
          <div className="heroStat">
            <span>Metric</span>
            <strong>{selectedMetric.label}</strong>
            <small>{metricCoverageById[selectedMetricId].coverage.filled}/{metricCoverageById[selectedMetricId].coverage.total} rows available</small>
          </div>
        </div>
      </section>

      <section className="pageLayout">
        <CompareControls
          chartType={chartType}
          endSeason={endSeason}
          metricCoverageById={metricCoverageById}
          onChartTypeChange={setChartType}
          onEndSeasonChange={changeEndSeason}
          onMetricChange={setSelectedMetricId}
          onStartSeasonChange={changeStartSeason}
          onToggleClub={toggleClub}
          seasons={comparisonSeasons}
          selectedClubIds={selectedClubIds}
          selectedMetricId={selectedMetricId}
          startSeason={startSeason}
        />

        <section className="contentColumn">
          <section className="panel">
            <SectionHeader
              title={selectedMetric.label}
              description={`Historical comparison for ${selectionLabel}. Missing observations are left as gaps, never converted to zero.`}
              coverage={metricCoverageById[selectedMetricId].coverage}
              sourceAction={openMetricSourcePanel}
              eyebrow="Historical chart"
            />
            <ComparisonChart
              chartData={chartData}
              chartType={chartType}
              metric={selectedMetric}
              selectedClubIds={selectedClubIds}
            />
          </section>

          <section className="panel">
            <SectionHeader
              title="Period ranking"
              description={
                selectedMetric.aggregation.type === "latest"
                  ? "This ranking uses the latest comparable season in the selected range."
                  : "Aggregation logic is metric-specific, so totals, averages, and latest-value metrics are handled differently."
              }
              coverage={metricCoverageById[selectedMetricId].coverage}
              sourceAction={openMetricSourcePanel}
              eyebrow="Ranking"
            />
            <ComparisonRanking metric={selectedMetric} ranking={ranking} />
          </section>
        </section>
      </section>

      <SourceDrawer
        open={Boolean(sourcePanel)}
        onClose={() => setSourcePanel(null)}
        title={sourcePanel?.title ?? ""}
        subtitle={sourcePanel?.subtitle ?? ""}
        sections={sourcePanel?.sections ?? []}
      />
    </>
  );
}
