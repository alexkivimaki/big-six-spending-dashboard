import { useMemo, useState } from "react";
import { ChevronDown, ChevronUp, Info } from "lucide-react";

import { CompareControls } from "../components/CompareControls";
import { ComparisonChart } from "../components/ComparisonChart";
import { ComparisonRanking } from "../components/ComparisonRanking";
import { CoverageBadge } from "../components/CoverageBadge";
import { SourceDrawer } from "../components/SourceDrawer";
import { DISPLAY_CURRENCY } from "../config/displayCurrency";
import { getMetric } from "../config/metricRegistry";
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

export function ComparePage() {
  const [selectedClubIds, setSelectedClubIds] = useState(["arsenal", "chelsea", "liverpool"]);
  const [startSeason, setStartSeason] = useState("2011/12");
  const [endSeason, setEndSeason] = useState("2024/25");
  const [selectedMetricId, setSelectedMetricId] = useState("netSquadInvestment");
  const [chartType, setChartType] = useState("line");
  const [valueBasis, setValueBasis] = useState(VALUE_BASIS.nominal);
  const [displayCurrency, setDisplayCurrency] = useState(DISPLAY_CURRENCY.EUR);
  const [showControls, setShowControls] = useState(false);
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
          coverage: getMetricCoverage(metric.id, selectedRows, {
            compareMode: true,
            valueBasis,
            displayCurrency,
          }),
        };
      }
    }
    return records;
  }, [metricGroups, selectedRows, valueBasis, displayCurrency]);

  const chartData = useMemo(
    () =>
      getComparisonChartData(selectedClubIds, startSeason, endSeason, selectedMetricId, {
        valueBasis,
        displayCurrency,
      }),
    [selectedClubIds, startSeason, endSeason, selectedMetricId, valueBasis, displayCurrency],
  );

  const ranking = useMemo(
    () =>
      getComparisonRanking(selectedClubIds, startSeason, endSeason, selectedMetricId, {
        valueBasis,
        displayCurrency,
      }),
    [selectedClubIds, startSeason, endSeason, selectedMetricId, valueBasis, displayCurrency],
  );

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
      subtitle: `${startSeason}–${endSeason} · ${selectedClubIds.length} selected clubs`,
      sections: getCompareSourceSections(
        selectedMetricId,
        selectedClubIds,
        startSeason,
        endSeason,
        valueBasis,
        displayCurrency,
      ),
    });
  }

  return (
    <>
      <section className="panel compareDashboardPanel">
        <div className="compareDashboardHeader">
          <h1>Compare how the Big Six fund their squads</h1>
        </div>

        <div className="compareControlsDisclosure">
          <button
            type="button"
            className="compareControlsTrigger"
            aria-expanded={showControls}
            aria-controls="compare-controls-panel"
            onClick={() => setShowControls((open) => !open)}
          >
            <span>Select options</span>
            {showControls ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </button>

          {showControls ? (
            <div id="compare-controls-panel">
              <CompareControls
                endSeason={endSeason}
                metricCoverageById={metricCoverageById}
                metricGroups={metricGroups}
                onEndSeasonChange={changeEndSeason}
                onMetricChange={changeMetric}
                onStartSeasonChange={changeStartSeason}
                onToggleClub={toggleClub}
                onDisplayCurrencyChange={setDisplayCurrency}
                onValueBasisChange={setValueBasis}
                displayCurrency={displayCurrency}
                seasons={comparisonSeasons}
                selectedClubIds={selectedClubIds}
                selectedMetricId={selectedMetricId}
                startSeason={startSeason}
                valueBasis={valueBasis}
              />
            </div>
          ) : null}
        </div>

        <ComparisonChart
          chartData={chartData}
          chartType={chartType}
          coverage={selectedCoverage}
          metric={selectedMetric}
          selectedClubIds={selectedClubIds}
          displayCurrency={displayCurrency}
          showLegend={false}
          valueBasis={valueBasis}
        />

        <div className="compareMetricInfo">
          <div className="compareMetricInfoText">
            <strong>{selectedMetric.label}</strong>
            <p>{selectedMetric.description}</p>
            <p className="compareMetricFormula">
              <span>Formula:</span> {selectedMetric.formulaLabel}
            </p>
          </div>
          <div className="compareMetricInfoMeta">
            <CoverageBadge coverage={selectedCoverage} />
            <button type="button" className="iconButton" onClick={openMetricSourcePanel} aria-label="Open source information">
              <Info size={16} />
            </button>
          </div>
        </div>

        <section className="compareRankingSection">
          <div className="compareSubsectionHeader">
            <h2>Period ranking</h2>
            <p>
              {selectedMetric.aggregation.type === "ratio-of-sums"
                ? "Selected-period percentages use summed squad investment divided by summed revenue."
                : selectedMetric.aggregation.type === "latest"
                  ? "This ranking uses the latest comparable season in the selected range."
                  : "Period rankings use metric-specific aggregation rules."}
            </p>
          </div>
          <ComparisonRanking displayCurrency={displayCurrency} metric={selectedMetric} ranking={ranking} />
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
