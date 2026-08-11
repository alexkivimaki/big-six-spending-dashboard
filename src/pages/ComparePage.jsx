import { useMemo, useState } from "react";
import { Menu, X } from "lucide-react";

import { CompareControls } from "../components/CompareControls";
import { ComparisonChart } from "../components/ComparisonChart";
import { ComparisonRanking } from "../components/ComparisonRanking";
import { SectionHeader } from "../components/SectionHeader";
import { SourceDrawer } from "../components/SourceDrawer";
import { clubConfigs } from "../config/clubConfig";
import { DISPLAY_CURRENCY } from "../config/displayCurrency";
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
  const [displayCurrency, setDisplayCurrency] = useState(DISPLAY_CURRENCY.EUR);
  const [mobileControlsOpen, setMobileControlsOpen] = useState(false);
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

  function openMobileControls() {
    setMobileControlsOpen(true);
  }

  function closeMobileControls() {
    setMobileControlsOpen(false);
  }

  function openMetricSourcePanel() {
    setSourcePanel({
      title: selectedMetric.label,
      subtitle: `${selectionLabel} · ${selectedClubIds.length} selected clubs`,
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
          className="compareControlsDesktop"
          chartType={chartType}
          endSeason={endSeason}
          metricCoverageById={metricCoverageById}
          metricGroups={metricGroups}
          onChartTypeChange={setChartType}
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

        <section className="contentColumn">
          <section className="compareMobileBar panel">
            <button type="button" className="secondaryButton compareMobileMenuButton" onClick={openMobileControls}>
              <Menu size={18} />
              <span>Selections</span>
            </button>
            <div className="compareMobileSummary">
              <strong>{selectedMetric.label}</strong>
              <small>
                {selectionLabel} · {selectedClubIds.length} clubs · {displayCurrency}
              </small>
            </div>
          </section>

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
                <span>Currency</span>
                <strong>{displayCurrency}</strong>
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
              displayCurrency={displayCurrency}
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
            <ComparisonRanking displayCurrency={displayCurrency} metric={selectedMetric} ranking={ranking} />
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

      {mobileControlsOpen ? (
        <div className="mobileControlsOverlay" role="dialog" aria-modal="true" aria-label="Dashboard selections">
          <button
            type="button"
            className="mobileControlsBackdrop"
            aria-label="Close dashboard selections"
            onClick={closeMobileControls}
          />
          <div className="mobileControlsDrawer">
            <div className="mobileControlsHeader">
              <div>
                <span className="eyebrow">Selections</span>
                <h2>Compare setup</h2>
              </div>
              <button type="button" className="iconButton" aria-label="Close dashboard selections" onClick={closeMobileControls}>
                <X size={18} />
              </button>
            </div>

            <CompareControls
              className="compareControlsMobile"
              chartType={chartType}
              endSeason={endSeason}
              metricCoverageById={metricCoverageById}
              metricGroups={metricGroups}
              onChartTypeChange={setChartType}
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

            <div className="mobileControlsFooter">
              <button type="button" className="secondaryButton" onClick={closeMobileControls}>
                Close
              </button>
              <button type="button" className="secondaryButton drawerApplyButton isActive" onClick={closeMobileControls}>
                Apply
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </>
  );
}
