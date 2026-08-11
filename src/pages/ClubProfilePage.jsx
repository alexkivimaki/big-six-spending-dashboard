import { useMemo, useState } from "react";
import { Bar, ComposedChart, Line, ResponsiveContainer, Tooltip, XAxis, YAxis, CartesianGrid } from "recharts";
import { useParams } from "react-router-dom";

import { ClubIdentity } from "../components/ClubIdentity";
import { CoverageBadge } from "../components/CoverageBadge";
import { SeasonHistoryTable } from "../components/SeasonHistoryTable";
import { SectionHeader } from "../components/SectionHeader";
import { SourceDrawer } from "../components/SourceDrawer";
import { DISPLAY_CURRENCY, displayCurrencyOptions } from "../config/displayCurrency";
import { getMetric, profileSnapshotMetricIds } from "../config/metricRegistry";
import { VALUE_BASIS, inflationConfig, valueBasisOptions } from "../config/valueBasis";
import {
  calculateMetricValue,
  getClubBySlug,
  getClubProfileCoverage,
  getClubRows,
  getClubTransferLeaders,
  getLatestMetricObservation,
  getProfileSectionSourceSections,
  getProfileSectionStatus,
} from "../lib/dataModel";
import {
  formatCount,
  formatCurrencyCompact,
  formatLeaguePosition,
  formatPercent,
} from "../shared/formatters";

function SimpleTooltip({ active, payload, label, formatters }) {
  if (!active || !payload?.length) return null;

  return (
    <div className="chartTooltip">
      <strong>{label}</strong>
      <div className="tooltipRows">
        {payload.map((entry) => (
          <div key={entry.dataKey} className="tooltipRow">
            <span>{entry.name}</span>
            <strong>{formatters[entry.dataKey](entry.value)}</strong>
          </div>
        ))}
      </div>
    </div>
  );
}

export function ClubProfilePage() {
  const { clubSlug } = useParams();
  const club = getClubBySlug(clubSlug);
  const [displayCurrency, setDisplayCurrency] = useState(DISPLAY_CURRENCY.EUR);
  const [valueBasis, setValueBasis] = useState(VALUE_BASIS.nominal);
  const [sourcePanel, setSourcePanel] = useState(null);

  const rows = useMemo(() => (club ? getClubRows(club.id) : []), [club]);

  if (!club) {
    return (
      <section className="panel emptyState">
        <h1>Club not found</h1>
        <p>The requested profile does not exist in the current beta dataset.</p>
      </section>
    );
  }

  const descendingRows = [...rows].sort((left, right) => right.seasonStartYear - left.seasonStartYear);
  const latestSeasonRepresented = descendingRows[0]?.season ?? "—";
  const profileCoverage = getClubProfileCoverage(club.id, { valueBasis, displayCurrency });

  const snapshotCards = profileSnapshotMetricIds.map((metricId) => {
    const metric = getMetric(metricId);
    const observation = getLatestMetricObservation(club.id, metricId, { valueBasis, displayCurrency });
    return {
      metricId,
      label: metric.label,
      value: observation ? metric.formatValue(observation.value, { displayCurrency }) : "Coming soon",
      note: observation ? observation.season : "No usable observation yet",
    };
  });

  const transferStatus = getProfileSectionStatus(
    club.id,
    ["grossTransferSpend", "transferIncome", "netTransferSpend"],
    { valueBasis, displayCurrency },
  );
  const financeStatus = getProfileSectionStatus(
    club.id,
    ["revenue", "staffCosts", "staffCostToRevenueRatio"],
    { valueBasis, displayCurrency },
  );
  const performanceStatus = getProfileSectionStatus(club.id, ["points", "leaguePosition", "trophies"]);
  const seasonTableStatus = getProfileSectionStatus(
    club.id,
    ["netTransferSpend", "revenue", "points"],
    { valueBasis, displayCurrency },
  );

  const latestTransferRow =
    getLatestMetricObservation(club.id, "netTransferSpend", { valueBasis, displayCurrency })?.row ?? null;
  const latestFinanceRow =
    getLatestMetricObservation(club.id, "revenue", { valueBasis, displayCurrency })?.row ?? null;
  const latestPerformanceRow = getLatestMetricObservation(club.id, "points")?.row ?? null;

  const grossTransferMetric = getMetric("grossTransferSpend");
  const transferIncomeMetric = getMetric("transferIncome");
  const netTransferMetric = getMetric("netTransferSpend");
  const revenueMetric = getMetric("revenue");
  const staffCostsMetric = getMetric("staffCosts");
  const profitBeforeTaxMetric = getMetric("profitBeforeTax");
  const netDebtMetric = getMetric("netDebt");

  const transferChartData = rows.map((row) => ({
    season: row.season,
    grossSpend: calculateMetricValue(row, "grossTransferSpend", valueBasis, displayCurrency),
    income: calculateMetricValue(row, "transferIncome", valueBasis, displayCurrency),
    netSpend: calculateMetricValue(row, "netTransferSpend", valueBasis, displayCurrency),
  }));

  const financeChartData = rows.map((row) => ({
    season: row.season,
    revenue: calculateMetricValue(row, "revenue", valueBasis, displayCurrency),
    staffCosts: calculateMetricValue(row, "staffCosts", valueBasis, displayCurrency),
  }));

  const performanceChartData = rows.map((row) => ({
    season: row.season,
    points: row.performance.points,
    leaguePosition: row.performance.leaguePosition,
  }));

  const arrivals = latestTransferRow ? getClubTransferLeaders(club.id, latestTransferRow.season, "arrival") : [];
  const departures = latestTransferRow ? getClubTransferLeaders(club.id, latestTransferRow.season, "departure") : [];

  const seasonHistoryRows = descendingRows.map((row) => ({
    season: row.season,
    grossSpend: grossTransferMetric.formatValue(
      calculateMetricValue(row, "grossTransferSpend", valueBasis, displayCurrency),
      { displayCurrency },
    ),
    income: transferIncomeMetric.formatValue(
      calculateMetricValue(row, "transferIncome", valueBasis, displayCurrency),
      { displayCurrency },
    ),
    netSpend: netTransferMetric.formatValue(
      calculateMetricValue(row, "netTransferSpend", valueBasis, displayCurrency),
      { displayCurrency },
    ),
    revenue: revenueMetric.formatValue(calculateMetricValue(row, "revenue", valueBasis, displayCurrency), {
      displayCurrency,
    }),
    staffCosts: staffCostsMetric.formatValue(
      calculateMetricValue(row, "staffCosts", valueBasis, displayCurrency),
      { displayCurrency },
    ),
    staffRatio: formatPercent(row.finance.staffCostToRevenueRatio),
    profitBeforeTax: profitBeforeTaxMetric.formatValue(
      calculateMetricValue(row, "profitBeforeTax", valueBasis, displayCurrency),
      { displayCurrency },
    ),
    points: formatCount(row.performance.points),
    leaguePosition: formatLeaguePosition(row.performance.leaguePosition),
    trophies: formatCount(row.achievements.majorTrophyCount),
    manager: row.manager.primaryManagerName ?? "—",
  }));

  function openSectionSources(title, subtitle, metricIds) {
    setSourcePanel({
      title,
      subtitle,
      sections: getProfileSectionSourceSections(club.id, metricIds, valueBasis, displayCurrency),
    });
  }

  return (
    <>
      <section className="profileHero panel">
        <div className="profileHeroTop">
          <ClubIdentity club={club} />
          <div className="profileHeroMeta">
            <CoverageBadge coverage={profileCoverage.transfers} quiet />
            <CoverageBadge coverage={profileCoverage.finance} quiet />
            <CoverageBadge coverage={profileCoverage.performance} quiet />
          </div>
        </div>

        <div className="profileHeroText">
          <h1>{club.name}</h1>
          <p>
            Latest season represented: <strong>{latestSeasonRepresented}</strong>. The beta profile
            keeps transfers, finance, and sporting context together so the numbers stay useful.
          </p>
        </div>

        <div className="profileToolbar">
          <div className="profileToolbarGroup">
            <span>Currency</span>
            <div className="chartToggleRow">
              {displayCurrencyOptions.map((option) => (
                <button
                  key={option.id}
                  type="button"
                  className={`secondaryButton ${displayCurrency === option.id ? "isActive" : ""}`}
                  onClick={() => setDisplayCurrency(option.id)}
                >
                  {option.label}
                </button>
              ))}
            </div>
          </div>
          <div className="profileToolbarGroup">
            <span>Values</span>
            <div className="chartToggleRow">
              {valueBasisOptions.map((option) => (
                <button
                  key={option.id}
                  type="button"
                  className={`secondaryButton ${valueBasis === option.id ? "isActive" : ""}`}
                  onClick={() => setValueBasis(option.id)}
                  disabled={option.disabled}
                >
                  {option.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        <p className="controlNote profileToolbarNote">
          {valueBasis === VALUE_BASIS.inflationAdjusted
            ? `Money values are restated to ${inflationConfig.baseSeason} prices.`
            : "Money values are shown in nominal season terms."}
        </p>

        <div className="snapshotGrid">
          {snapshotCards.map((card) => (
            <article key={card.metricId} className="snapshotCard">
              <span>{card.label}</span>
              <strong>{card.value}</strong>
              <small>{card.note}</small>
            </article>
          ))}
        </div>
      </section>

      <section className="panel profileSection">
        <SectionHeader
          title="Transfers"
          description="Gross spend, income, and net spend over time, plus a quick latest-season transfer summary."
          coverage={transferStatus}
          sourceAction={() =>
            openSectionSources("Transfer data", `${club.name} transfer dataset`, [
              "grossTransferSpend",
              "transferIncome",
              "netTransferSpend",
            ])
          }
          eyebrow="Section 1"
        />

        <div className="chartCanvas compact">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={transferChartData} margin={{ top: 10, right: 8, left: 0, bottom: 24 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(19, 34, 28, 0.12)" />
              <XAxis dataKey="season" angle={-35} textAnchor="end" height={70} tick={{ fontSize: 12 }} />
              <YAxis
                tickFormatter={(value) => grossTransferMetric.axisTick(value, { displayCurrency })}
                tick={{ fontSize: 12 }}
              />
              <Tooltip
                content={
                  <SimpleTooltip
                    formatters={{
                      grossSpend: (value) => grossTransferMetric.formatValue(value, { displayCurrency }),
                      income: (value) => transferIncomeMetric.formatValue(value, { displayCurrency }),
                      netSpend: (value) => netTransferMetric.formatValue(value, { displayCurrency }),
                    }}
                  />
                }
              />
              <Bar dataKey="grossSpend" name="Gross spend" fill={club.colors.primary} radius={[8, 8, 0, 0]} />
              <Bar dataKey="income" name="Income" fill={club.colors.secondary} radius={[8, 8, 0, 0]} />
              <Line dataKey="netSpend" name="Net spend" stroke={club.colors.ink} strokeWidth={3} dot={{ r: 2 }} />
            </ComposedChart>
          </ResponsiveContainer>
        </div>

        <div className="summaryGrid">
          <article className="summaryCard">
            <span>Gross spend</span>
            <strong>
              {grossTransferMetric.formatValue(
                latestTransferRow
                  ? calculateMetricValue(latestTransferRow, "grossTransferSpend", valueBasis, displayCurrency)
                  : null,
                { displayCurrency },
              )}
            </strong>
            <small>{latestTransferRow?.season ?? "Coming soon"}</small>
          </article>
          <article className="summaryCard">
            <span>Transfer income</span>
            <strong>
              {transferIncomeMetric.formatValue(
                latestTransferRow
                  ? calculateMetricValue(latestTransferRow, "transferIncome", valueBasis, displayCurrency)
                  : null,
                { displayCurrency },
              )}
            </strong>
            <small>{latestTransferRow?.season ?? "Coming soon"}</small>
          </article>
          <article className="summaryCard">
            <span>Net spend</span>
            <strong>
              {netTransferMetric.formatValue(
                latestTransferRow
                  ? calculateMetricValue(latestTransferRow, "netTransferSpend", valueBasis, displayCurrency)
                  : null,
                { displayCurrency },
              )}
            </strong>
            <small>{latestTransferRow?.season ?? "Coming soon"}</small>
          </article>
          <article className="summaryCard">
            <span>Incoming / outgoing</span>
            <strong>
              {formatCount(latestTransferRow?.transfers.incomingCount)} / {formatCount(latestTransferRow?.transfers.outgoingCount)}
            </strong>
            <small>{latestTransferRow?.season ?? "Coming soon"}</small>
          </article>
        </div>

        <div className="detailGrid">
          <article className="detailCard">
            <h3>Largest arrivals</h3>
            {arrivals.length ? (
              <ul className="transferList">
                {arrivals.map((transfer) => (
                  <li key={`${transfer.season}-${transfer.playerName}-${transfer.direction}`}>
                    <span>
                      <strong>{transfer.playerName}</strong>
                      <small>{transfer.otherClubName ?? "Unknown club"}</small>
                    </span>
                    <strong>{formatCurrencyCompact(transfer.feeEur, "EUR", transfer.feeText ?? "—")}</strong>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="placeholderText">Detailed transfer records coming soon.</p>
            )}
          </article>

          <article className="detailCard">
            <h3>Largest departures</h3>
            {departures.length ? (
              <ul className="transferList">
                {departures.map((transfer) => (
                  <li key={`${transfer.season}-${transfer.playerName}-${transfer.direction}`}>
                    <span>
                      <strong>{transfer.playerName}</strong>
                      <small>{transfer.otherClubName ?? "Unknown club"}</small>
                    </span>
                    <strong>{formatCurrencyCompact(transfer.feeEur, "EUR", transfer.feeText ?? "—")}</strong>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="placeholderText">Detailed transfer records coming soon.</p>
            )}
          </article>
        </div>
      </section>

      <section className="panel profileSection">
        <SectionHeader
          title="Finances"
          description="Revenue and reported staff costs stay central. Wage-bill comparisons use the current club-accounts proxy rather than a pure player-payroll series."
          coverage={financeStatus}
          sourceAction={() =>
            openSectionSources("Finance data", `${club.name} annual reports`, [
              "revenue",
              "staffCosts",
              "staffCostToRevenueRatio",
              "profitBeforeTax",
              "netDebt",
            ])
          }
          eyebrow="Section 2"
        />

        <div className="chartCanvas compact">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={financeChartData} margin={{ top: 10, right: 8, left: 0, bottom: 24 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(19, 34, 28, 0.12)" />
              <XAxis dataKey="season" angle={-35} textAnchor="end" height={70} tick={{ fontSize: 12 }} />
              <YAxis
                tickFormatter={(value) => revenueMetric.axisTick(value, { displayCurrency })}
                tick={{ fontSize: 12 }}
              />
              <Tooltip
                content={
                  <SimpleTooltip
                    formatters={{
                      revenue: (value) => revenueMetric.formatValue(value, { displayCurrency }),
                      staffCosts: (value) => staffCostsMetric.formatValue(value, { displayCurrency }),
                    }}
                  />
                }
              />
              <Bar dataKey="revenue" name="Revenue" fill={club.colors.primary} radius={[8, 8, 0, 0]} />
              <Line dataKey="staffCosts" name="Staff costs" stroke={club.colors.ink} strokeWidth={3} dot={{ r: 2 }} />
            </ComposedChart>
          </ResponsiveContainer>
        </div>

        <div className="summaryGrid">
          <article className="summaryCard">
            <span>Revenue</span>
            <strong>
              {revenueMetric.formatValue(
                latestFinanceRow
                  ? calculateMetricValue(latestFinanceRow, "revenue", valueBasis, displayCurrency)
                  : null,
                { displayCurrency },
              )}
            </strong>
            <small>{latestFinanceRow?.season ?? "Coming soon"}</small>
          </article>
          <article className="summaryCard">
            <span>Staff costs</span>
            <strong>
              {staffCostsMetric.formatValue(
                latestFinanceRow
                  ? calculateMetricValue(latestFinanceRow, "staffCosts", valueBasis, displayCurrency)
                  : null,
                { displayCurrency },
              )}
            </strong>
            <small>{latestFinanceRow?.season ?? "Coming soon"}</small>
          </article>
          <article className="summaryCard">
            <span>Staff costs / revenue</span>
            <strong>{formatPercent(latestFinanceRow?.finance.staffCostToRevenueRatio)}</strong>
            <small>{latestFinanceRow?.season ?? "Coming soon"}</small>
          </article>
          <article className="summaryCard">
            <span>Profit before tax</span>
            <strong>
              {profitBeforeTaxMetric.formatValue(
                latestFinanceRow
                  ? calculateMetricValue(latestFinanceRow, "profitBeforeTax", valueBasis, displayCurrency)
                  : null,
                { displayCurrency },
              )}
            </strong>
            <small>{latestFinanceRow?.season ?? "Coming soon"}</small>
          </article>
          <article className="summaryCard">
            <span>Net debt</span>
            <strong>
              {netDebtMetric.formatValue(
                latestFinanceRow
                  ? calculateMetricValue(latestFinanceRow, "netDebt", valueBasis, displayCurrency)
                  : null,
                { displayCurrency },
              )}
            </strong>
            <small>{latestFinanceRow?.season ?? "Coming soon"}</small>
          </article>
          <article className="summaryCard">
            <span>Player wages estimate</span>
            <strong>Coming soon</strong>
            <small>Data collection in progress</small>
          </article>
        </div>

        <div className="detailGrid financeGrid">
          <article className="detailCard">
            <h3>Revenue composition</h3>
            {latestFinanceRow?.finance.revenueOriginal ? (
              <>
                <div className="compositionBar">
                  <span
                    className="compositionSegment commercial"
                    style={{
                      width: `${((latestFinanceRow.finance.commercialOriginal ?? 0) / latestFinanceRow.finance.revenueOriginal) * 100}%`,
                    }}
                  />
                  <span
                    className="compositionSegment broadcast"
                    style={{
                      width: `${((latestFinanceRow.finance.broadcastOriginal ?? 0) / latestFinanceRow.finance.revenueOriginal) * 100}%`,
                    }}
                  />
                  <span
                    className="compositionSegment matchday"
                    style={{
                      width: `${((latestFinanceRow.finance.matchdayOriginal ?? 0) / latestFinanceRow.finance.revenueOriginal) * 100}%`,
                    }}
                  />
                </div>
                <ul className="miniList">
                  <li>
                    Commercial:{" "}
                    {formatCurrencyCompact(
                      valueBasis === VALUE_BASIS.inflationAdjusted
                        ? latestFinanceRow.finance.commercial.real?.[displayCurrency]
                        : latestFinanceRow.finance.commercial.nominal?.[displayCurrency],
                      displayCurrency,
                    )}
                  </li>
                  <li>
                    Broadcasting:{" "}
                    {formatCurrencyCompact(
                      valueBasis === VALUE_BASIS.inflationAdjusted
                        ? latestFinanceRow.finance.broadcast.real?.[displayCurrency]
                        : latestFinanceRow.finance.broadcast.nominal?.[displayCurrency],
                      displayCurrency,
                    )}
                  </li>
                  <li>
                    Matchday:{" "}
                    {formatCurrencyCompact(
                      valueBasis === VALUE_BASIS.inflationAdjusted
                        ? latestFinanceRow.finance.matchday.real?.[displayCurrency]
                        : latestFinanceRow.finance.matchday.nominal?.[displayCurrency],
                      displayCurrency,
                    )}
                  </li>
                </ul>
              </>
            ) : (
              <p className="placeholderText">Coming soon.</p>
            )}
          </article>

          <article className="detailCard">
            <h3>Secondary finance metrics</h3>
            <ul className="miniList">
              <li>
                Player amortisation:{" "}
                {formatCurrencyCompact(
                  valueBasis === VALUE_BASIS.inflationAdjusted
                    ? latestFinanceRow?.finance.playerAmortisation.real?.[displayCurrency]
                    : latestFinanceRow?.finance.playerAmortisation.nominal?.[displayCurrency],
                  displayCurrency,
                )}
              </li>
              <li>
                Profit on player sales:{" "}
                {formatCurrencyCompact(
                  valueBasis === VALUE_BASIS.inflationAdjusted
                    ? latestFinanceRow?.finance.profitOnPlayerSales.real?.[displayCurrency]
                    : latestFinanceRow?.finance.profitOnPlayerSales.nominal?.[displayCurrency],
                  displayCurrency,
                )}
              </li>
            </ul>
          </article>
        </div>
      </section>

      <section className="panel profileSection">
        <SectionHeader
          title="Sporting performance"
          description="Results stay in service of the finance story rather than becoming a separate football stats product."
          coverage={performanceStatus}
          sourceAction={() =>
            openSectionSources("Sporting performance data", `${club.name} season table context`, [
              "points",
              "leaguePosition",
              "trophies",
            ])
          }
          eyebrow="Section 3"
        />

        <div className="chartCanvas compact">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={performanceChartData} margin={{ top: 10, right: 8, left: 0, bottom: 24 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(19, 34, 28, 0.12)" />
              <XAxis dataKey="season" angle={-35} textAnchor="end" height={70} tick={{ fontSize: 12 }} />
              <YAxis yAxisId="points" tick={{ fontSize: 12 }} />
              <YAxis yAxisId="position" orientation="right" reversed tick={{ fontSize: 12 }} />
              <Tooltip
                content={
                  <SimpleTooltip
                    formatters={{
                      points: (value) => formatCount(value),
                      leaguePosition: (value) => formatLeaguePosition(value),
                    }}
                  />
                }
              />
              <Bar yAxisId="points" dataKey="points" name="Points" fill={club.colors.primary} radius={[8, 8, 0, 0]} />
              <Line yAxisId="position" dataKey="leaguePosition" name="League position" stroke={club.colors.ink} strokeWidth={3} dot={{ r: 2 }} />
            </ComposedChart>
          </ResponsiveContainer>
        </div>

        <div className="summaryGrid">
          <article className="summaryCard">
            <span>Points</span>
            <strong>{formatCount(latestPerformanceRow?.performance.points)}</strong>
            <small>{latestPerformanceRow?.season ?? "Coming soon"}</small>
          </article>
          <article className="summaryCard">
            <span>Premier League position</span>
            <strong>{formatLeaguePosition(latestPerformanceRow?.performance.leaguePosition)}</strong>
            <small>{latestPerformanceRow?.season ?? "Coming soon"}</small>
          </article>
          <article className="summaryCard">
            <span>Trophies</span>
            <strong>{formatCount(latestPerformanceRow?.achievements.majorTrophyCount)}</strong>
            <small>{latestPerformanceRow?.season ?? "Coming soon"}</small>
          </article>
          <article className="summaryCard">
            <span>Primary manager</span>
            <strong>{latestPerformanceRow?.manager.primaryManagerName ?? "Coming soon"}</strong>
            <small>{latestPerformanceRow?.season ?? "No current row"}</small>
          </article>
        </div>
      </section>

      <section className="panel profileSection">
        <SectionHeader
          title="Season history"
          description="One detailed season-by-season view of the club, newest season first."
          coverage={seasonTableStatus}
          sourceAction={() =>
            openSectionSources("Season history", `${club.name} combined club-season view`, [
              "netTransferSpend",
              "revenue",
              "points",
            ])
          }
          eyebrow="Section 4"
        />
        <SeasonHistoryTable rows={seasonHistoryRows} />
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
