import { useMemo, useState } from "react";
import { Bar, ComposedChart, Line, ResponsiveContainer, Tooltip, XAxis, YAxis, CartesianGrid } from "recharts";
import { useParams } from "react-router-dom";

import { ClubIdentity } from "../components/ClubIdentity";
import { CoverageBadge } from "../components/CoverageBadge";
import { SeasonHistoryTable } from "../components/SeasonHistoryTable";
import { SectionHeader } from "../components/SectionHeader";
import { SourceDrawer } from "../components/SourceDrawer";
import { getMetric, profileSnapshotMetricIds } from "../config/metricRegistry";
import {
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
  const profileCoverage = getClubProfileCoverage(club.id);

  const snapshotCards = profileSnapshotMetricIds.map((metricId) => {
    const metric = getMetric(metricId);
    const observation = getLatestMetricObservation(club.id, metricId);
    return {
      metricId,
      label: metric.label,
      value: observation ? metric.formatValue(observation.value) : "Coming soon",
      note: observation ? observation.season : "No usable observation yet",
    };
  });

  const transferStatus = getProfileSectionStatus(club.id, ["grossTransferSpend", "transferIncome", "netTransferSpend"]);
  const financeStatus = getProfileSectionStatus(club.id, ["revenue", "staffCosts", "staffCostToRevenueRatio"]);
  const performanceStatus = getProfileSectionStatus(club.id, ["points", "leaguePosition", "trophies"]);
  const seasonTableStatus = getProfileSectionStatus(club.id, ["netTransferSpend", "revenue", "points"]);

  const latestTransferRow = getLatestMetricObservation(club.id, "netTransferSpend")?.row ?? null;
  const latestFinanceRow = getLatestMetricObservation(club.id, "revenue")?.row ?? null;
  const latestPerformanceRow = getLatestMetricObservation(club.id, "points")?.row ?? null;

  const transferChartData = rows.map((row) => ({
    season: row.season,
    grossSpend: row.transfers.grossSpendEur,
    income: row.transfers.incomeEur,
    netSpend: row.transfers.netSpendEur,
  }));

  const financeChartData = rows.map((row) => ({
    season: row.season,
    revenue: row.finance.revenueOriginal,
    staffCosts: row.finance.staffCostsOriginal,
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
    grossSpend: formatCurrencyCompact(row.transfers.grossSpendEur, "EUR"),
    income: formatCurrencyCompact(row.transfers.incomeEur, "EUR"),
    netSpend: formatCurrencyCompact(row.transfers.netSpendEur, "EUR"),
    revenue: formatCurrencyCompact(row.finance.revenueOriginal, "GBP"),
    staffCosts: formatCurrencyCompact(row.finance.staffCostsOriginal, "GBP"),
    staffRatio: formatPercent(row.finance.staffCostToRevenueRatio),
    profitBeforeTax: formatCurrencyCompact(row.finance.profitBeforeTaxOriginal, "GBP"),
    points: formatCount(row.performance.points),
    leaguePosition: formatLeaguePosition(row.performance.leaguePosition),
    trophies: formatCount(row.achievements.majorTrophyCount),
    manager: row.manager.primaryManagerName ?? "—",
  }));

  function openSectionSources(title, subtitle, metricIds) {
    setSourcePanel({
      title,
      subtitle,
      sections: getProfileSectionSourceSections(club.id, metricIds),
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

      <section className="panel">
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
              <YAxis tickFormatter={(value) => `€${Math.round(value / 1_000_000)}m`} tick={{ fontSize: 12 }} />
              <Tooltip
                content={
                  <SimpleTooltip
                    formatters={{
                      grossSpend: (value) => formatCurrencyCompact(value, "EUR"),
                      income: (value) => formatCurrencyCompact(value, "EUR"),
                      netSpend: (value) => formatCurrencyCompact(value, "EUR"),
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
            <strong>{formatCurrencyCompact(latestTransferRow?.transfers.grossSpendEur, "EUR")}</strong>
            <small>{latestTransferRow?.season ?? "Coming soon"}</small>
          </article>
          <article className="summaryCard">
            <span>Transfer income</span>
            <strong>{formatCurrencyCompact(latestTransferRow?.transfers.incomeEur, "EUR")}</strong>
            <small>{latestTransferRow?.season ?? "Coming soon"}</small>
          </article>
          <article className="summaryCard">
            <span>Net spend</span>
            <strong>{formatCurrencyCompact(latestTransferRow?.transfers.netSpendEur, "EUR")}</strong>
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

      <section className="panel">
        <SectionHeader
          title="Finances"
          description="Revenue and staff costs stay central. Secondary finance fields are available, but kept less prominent."
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
              <YAxis tickFormatter={(value) => `£${Math.round(value / 1_000_000)}m`} tick={{ fontSize: 12 }} />
              <Tooltip
                content={
                  <SimpleTooltip
                    formatters={{
                      revenue: (value) => formatCurrencyCompact(value, "GBP"),
                      staffCosts: (value) => formatCurrencyCompact(value, "GBP"),
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
            <strong>{formatCurrencyCompact(latestFinanceRow?.finance.revenueOriginal, "GBP")}</strong>
            <small>{latestFinanceRow?.season ?? "Coming soon"}</small>
          </article>
          <article className="summaryCard">
            <span>Staff costs</span>
            <strong>{formatCurrencyCompact(latestFinanceRow?.finance.staffCostsOriginal, "GBP")}</strong>
            <small>{latestFinanceRow?.season ?? "Coming soon"}</small>
          </article>
          <article className="summaryCard">
            <span>Staff costs / revenue</span>
            <strong>{formatPercent(latestFinanceRow?.finance.staffCostToRevenueRatio)}</strong>
            <small>{latestFinanceRow?.season ?? "Coming soon"}</small>
          </article>
          <article className="summaryCard">
            <span>Profit before tax</span>
            <strong>{formatCurrencyCompact(latestFinanceRow?.finance.profitBeforeTaxOriginal, "GBP")}</strong>
            <small>{latestFinanceRow?.season ?? "Coming soon"}</small>
          </article>
          <article className="summaryCard">
            <span>Net debt</span>
            <strong>{formatCurrencyCompact(latestFinanceRow?.finance.netDebtOriginal, "GBP")}</strong>
            <small>{latestFinanceRow?.season ?? "Coming soon"}</small>
          </article>
          <article className="summaryCard">
            <span>Estimated player wages</span>
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
                  <li>Commercial: {formatCurrencyCompact(latestFinanceRow.finance.commercialOriginal, "GBP")}</li>
                  <li>Broadcasting: {formatCurrencyCompact(latestFinanceRow.finance.broadcastOriginal, "GBP")}</li>
                  <li>Matchday: {formatCurrencyCompact(latestFinanceRow.finance.matchdayOriginal, "GBP")}</li>
                </ul>
              </>
            ) : (
              <p className="placeholderText">Coming soon.</p>
            )}
          </article>

          <article className="detailCard">
            <h3>Secondary finance metrics</h3>
            <ul className="miniList">
              <li>Player amortisation: {formatCurrencyCompact(latestFinanceRow?.finance.playerAmortisationOriginal, "GBP")}</li>
              <li>Profit on player sales: {formatCurrencyCompact(latestFinanceRow?.finance.profitOnPlayerSalesOriginal, "GBP")}</li>
            </ul>
          </article>
        </div>
      </section>

      <section className="panel">
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

      <section className="panel">
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
