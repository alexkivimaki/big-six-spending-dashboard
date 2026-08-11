import { useMemo, useState } from "react";

import { CompareControls } from "../components/CompareControls";
import { ComparisonChart } from "../components/ComparisonChart";
import { ComparisonRanking } from "../components/ComparisonRanking";
import { SectionHeader } from "../components/SectionHeader";
import { SourceDrawer } from "../components/SourceDrawer";
import { clubConfigs } from "../config/clubConfig";
import { getMetric, getMetricFormulaText } from "../config/metricRegistry";
import { VALUE_BASIS } from "../config/valueBasis";
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
  const [selectedMetricId, setSelectedMetricId] = useState("netSquadInvestment");
  const [chartType, setChartType] = useState("line");
  const [valueBasis, setValueBasis] = useState(VALUE_BASIS.nominal);
  const [sourcePanel, setSourcePanel] = useState(null);

  const metricGroups = useMemo(() => getMetricOptionsForCompare(), []);
  const selectedMetric = getMetric(selectedMetricId);
  const selectedRows = useMemo(
    () => getRowsInRange(selectedClubIds, startSeason, endSeason),
    [selectedClubIds, startSeason, endSeason],
  );

  const metricCoverageById = useMemo(() => {
    const records = {};
    for (const group of metricGroups) {
      for (const metric of group.metrics) {
        records[metric.id] = {
          metric,
          coverage: getMetricCoverage(metric.id, selectedRows, { compareMode: true, valueBasis }),
        };
      }
    }
    return records;
  }, [metricGroups, selectedRows, valueBasis]);

  const chartData = useMemo(
    () => getComparisonChartData(selectedClubIds, startSeason, endSeason, selectedMetricId, { valueBasis }),
    [selectedClubIds, startSeason, endSeason, selectedMetricId, valueBasis],
  );

  const ranking = useMemo(
    () => getComparisonRanking(selectedClubIds, startSeason, endSeason, selectedMetricId, { valueBasis }),
    [selectedClubIds, startSeason, endSeason, selectedMetricId, valueBasis],
  );

  const selectionLabel = formatSeasonRange(startSeason, endSeason);
  const selectedCoverage = metricCoverageById[selectedMetricId]?.coverage ?? {
    status: "coming-soon",
    filled: 0,
    total: selectedRows.length,
  };

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

  function changeMetric(nextMetricId) {
    setSelectedMetricId(nextMetricId);
  }

  function openMetricSourcePanel() {
    setSourcePanel({
      title: selectedMetric.label,
      subtitle: `${selectionLabel} · ${selectedClubIds.length} selected clubs`,
      sections: getCompareSourceSections(selectedMetricId, selectedClubIds, startSeason, endSeason, valueBasis),
    });
  }

  return (
    <>
      <section className="pageHero panel">
        <div>
          <span className="eyebrow">Compare</span>
          <h1>Compare how the Big Six fund their squads</h1>
          <p>
            Focus on one metric at a time: transfer investment, player-sale offsets, and how those
            costs relate to revenue once the finance layers are ready.
          </p>
        </div>

        <div className="heroStats">
          <div className="heroStat">
            <span>Selected clubs</span>
            <strong>{selectedClubIds.length}</strong>
            <small>
              {selectedClubIds
                .map((clubId) => clubConfigs.find((club) => club.id === clubId)?.shortName)
                .join(", ")}
            </small>
          </div>
          <div className="heroStat">
            <span>Metric</span>
            <strong>{selectedMetric.label}</strong>
            <small>
              {selectedCoverage.filled}/{selectedCoverage.total} club-seasons available
            </small>
          </div>
        </div>
      </section>

      <section className="pageLayout">
        <CompareControls
          chartType={chartType}
          endSeason={endSeason}
          metricCoverageById={metricCoverageById}
          metricGroups={metricGroups}
          onChartTypeChange={setChartType}
          onEndSeasonChange={changeEndSeason}
          onMetricChange={changeMetric}
          onStartSeasonChange={changeStartSeason}
          onToggleClub={toggleClub}
          onValueBasisChange={setValueBasis}
          seasons={comparisonSeasons}
          selectedClubIds={selectedClubIds}
          selectedMetricId={selectedMetricId}
          startSeason={startSeason}
          valueBasis={valueBasis}
        />

        <section className="contentColumn">
          <section className="panel">
            <SectionHeader
              title={selectedMetric.label}
              description={`Historical comparison for ${selectionLabel}. Missing observations stay missing, and the chart never turns them into zero.`}
              coverage={selectedCoverage}
              sourceAction={openMetricSourcePanel}
              eyebrow="Historical chart"
            />

            <div className="metricMetaStrip">
              <div className="metricMetaItem">
                <span>Formula</span>
                <strong>{getMetricFormulaText(selectedMetricId, valueBasis)}</strong>
              </div>
              <div className="metricMetaItem">
                <span>Values</span>
                <strong>{valueBasis === VALUE_BASIS.nominal ? "Nominal" : "Inflation adjusted"}</strong>
              </div>
            </div>

            <ComparisonChart
              chartData={chartData}
              chartType={chartType}
              coverage={selectedCoverage}
              metric={selectedMetric}
              selectedClubIds={selectedClubIds}
              valueBasis={valueBasis}
            />
          </section>

          <section className="panel">
            <SectionHeader
              title="Period ranking"
              description={
                selectedMetric.aggregation.type === "ratio-of-sums"
                  ? "Selected-period percentages use summed squad investment divided by summed revenue."
                  : selectedMetric.aggregation.type === "latest"
                    ? "This ranking uses the latest comparable season in the selected range."
                    : "Period rankings use metric-specific aggregation rules instead of one generic total."
              }
              coverage={selectedCoverage}
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
