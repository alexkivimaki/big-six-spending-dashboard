import clubSeasonData from "../data/clubSeasonData.json";
import clubSeasonMasterData from "../data/clubSeasonMasterData.json";
import clubRevenueData from "../data/clubRevenueData.json";
import clubTransferRowsData from "../data/clubTransferRowsData.json";
import { clubConfigById, clubConfigBySlug, clubConfigs } from "../config/clubConfig";
import { compareMetricGroups, metricRegistry } from "../config/metricRegistry";

const START_YEAR = 2008;

function toNumber(value) {
  if (value === null || value === undefined || value === "") return null;
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric : null;
}

function toBoolean(value) {
  return value === true || value === "True";
}

function seasonToStartYear(season) {
  return Number(String(season).slice(0, 4));
}

function pairKey(clubId, season) {
  return `${clubId}::${season}`;
}

function intersect(listOfSets) {
  if (!listOfSets.length) return new Set();
  const [first, ...rest] = listOfSets;
  const result = new Set(first);
  for (const set of rest) {
    for (const value of [...result]) {
      if (!set.has(value)) result.delete(value);
    }
  }
  return result;
}

function sortSeasonsAscending(seasons) {
  return [...seasons].sort((left, right) => seasonToStartYear(left) - seasonToStartYear(right));
}

function createFinanceSources(masterRow, revenueRow) {
  return {
    sourceDocument: masterRow?.finance_source_document ?? revenueRow?.source_document ?? null,
    sourceUrl: masterRow?.finance_source_url ?? revenueRow?.source_url ?? null,
    confidence: masterRow?.finance_confidence_level ?? revenueRow?.confidence_level ?? null,
    notes: masterRow?.finance_notes ?? revenueRow?.notes ?? null,
    requiresManualReview:
      toBoolean(masterRow?.finance_requires_manual_review) || toBoolean(revenueRow?.requires_manual_review),
    reportingDate: masterRow?.financial_year_end ?? revenueRow?.financial_year_end ?? null,
  };
}

function normalizeClubSeason(baseRow, masterRow, revenueRow) {
  const club = clubConfigById[baseRow.club_id];
  const revenueOriginal = toNumber(masterRow?.total_revenue_original) ?? toNumber(revenueRow?.turnover_original);
  const staffCostsOriginal =
    toNumber(masterRow?.official_staff_costs_original) ?? toNumber(revenueRow?.wage_bill_original);
  const staffCostToRevenueRatio =
    revenueOriginal && staffCostsOriginal ? staffCostsOriginal / revenueOriginal : null;

  return {
    clubId: club.id,
    clubSlug: club.slug,
    clubName: club.name,
    season: baseRow.season,
    seasonStartYear: seasonToStartYear(baseRow.season),
    transfers: {
      grossSpendEur: toNumber(baseRow.gross_transfer_spend_eur),
      incomeEur: toNumber(baseRow.transfer_income_eur),
      netSpendEur: toNumber(baseRow.net_transfer_spend_eur),
      incomingCount: toNumber(baseRow.incoming_transfer_count),
      outgoingCount: toNumber(baseRow.outgoing_transfer_count),
      sourceName: baseRow.source_name,
      sourceUrl: baseRow.source_endpoint,
      confidence: baseRow.confidence_level,
      notes: baseRow.notes || null,
      collectedAt: baseRow.collected_at_utc || null,
    },
    finance: {
      currency: masterRow?.currency_original ?? "GBP",
      revenueOriginal,
      staffCostsOriginal,
      staffCostToRevenueRatio,
      profitBeforeTaxOriginal:
        toNumber(masterRow?.profit_loss_before_tax_original) ?? toNumber(revenueRow?.profit_loss_before_tax_original),
      netDebtOriginal: toNumber(masterRow?.net_debt_original) ?? toNumber(revenueRow?.net_debt_original),
      matchdayOriginal:
        toNumber(masterRow?.matchday_revenue_original) ?? toNumber(revenueRow?.gate_and_matchday_income_original),
      broadcastOriginal:
        toNumber(masterRow?.broadcast_revenue_original) ?? toNumber(revenueRow?.tv_and_broadcasting_original),
      commercialOriginal:
        toNumber(masterRow?.commercial_revenue_original) ?? toNumber(revenueRow?.commercial_income_original),
      playerAmortisationOriginal: toNumber(masterRow?.player_amortisation_original),
      profitOnPlayerSalesOriginal: toNumber(masterRow?.profit_on_player_sales_original),
      hasData: revenueOriginal !== null || staffCostsOriginal !== null,
      ...createFinanceSources(masterRow, revenueRow),
    },
    performance: {
      points: toNumber(masterRow?.points),
      leaguePosition: toNumber(masterRow?.league_position),
      wins: toNumber(masterRow?.wins),
      draws: toNumber(masterRow?.draws),
      losses: toNumber(masterRow?.losses),
      sourceName: masterRow?.performance_source_name ?? null,
      sourceUrl: masterRow?.performance_source_url ?? null,
      confidence: masterRow?.performance_confidence_level ?? null,
      notes: masterRow?.performance_notes ?? null,
      evidence: masterRow?.performance_evidence ?? null,
      hasData: toBoolean(masterRow?.has_performance_data),
    },
    achievements: {
      majorTrophyCount: toNumber(masterRow?.major_trophy_count),
      achievementCountTotal: toNumber(masterRow?.achievement_count_total),
      achievementNames: masterRow?.achievement_names ?? null,
      achievementsInSeason: masterRow?.achievements_in_season ?? null,
      sourceName: masterRow?.achievement_source_name ?? null,
      sourceUrl: masterRow?.achievement_source_endpoint ?? null,
      confidence: masterRow?.achievement_confidence_level ?? null,
      notes: masterRow?.achievement_notes ?? null,
      hasData: toBoolean(masterRow?.has_achievement_data),
    },
    manager: {
      primaryManagerName: masterRow?.primary_manager_name ?? null,
      managerNames: masterRow?.manager_names ?? null,
      sourceName: masterRow?.manager_source_name ?? null,
      sourceUrl: masterRow?.manager_source_endpoint ?? null,
      confidence: masterRow?.manager_confidence_level ?? null,
      notes: masterRow?.manager_notes ?? null,
      hasData: toBoolean(masterRow?.has_manager_data) || Boolean(masterRow?.primary_manager_name),
    },
    efficiency: {
      rawPlayerCostEur: toNumber(masterRow?.raw_player_cost_eur),
      costPerPoint: toNumber(masterRow?.cost_per_point),
      estimatedPlayerWagesEur: toNumber(masterRow?.estimated_player_wages_eur),
    },
  };
}

const baseRows = clubSeasonData
  .filter((row) => clubConfigById[row.club_id] && seasonToStartYear(row.season) >= START_YEAR)
  .sort((left, right) => seasonToStartYear(left.season) - seasonToStartYear(right.season));

const masterByKey = new Map(clubSeasonMasterData.map((row) => [pairKey(row.club_id, row.season), row]));
const revenueByKey = new Map(clubRevenueData.map((row) => [pairKey(row.club_id, row.season), row]));

export const comparisonSeasons = sortSeasonsAscending([...new Set(baseRows.map((row) => row.season))]);

export const clubSeasonRecords = baseRows.map((row) =>
  normalizeClubSeason(row, masterByKey.get(pairKey(row.club_id, row.season)), revenueByKey.get(pairKey(row.club_id, row.season))),
);

export const clubSeasonRecordsByClub = Object.fromEntries(
  clubConfigs.map((club) => [
    club.id,
    clubSeasonRecords.filter((row) => row.clubId === club.id),
  ]),
);

export const clubTransferRows = clubTransferRowsData
  .filter((row) => clubConfigById[row.club_id] && toNumber(row.season_start_year) >= START_YEAR)
  .map((row) => ({
    clubId: row.club_id,
    season: row.season,
    seasonStartYear: toNumber(row.season_start_year),
    direction: row.direction,
    playerName: row.player_name,
    age: toNumber(row.age),
    position: row.position || null,
    otherClubName: row.other_club_name || null,
    feeText: row.fee_text || null,
    feeEur: toNumber(row.fee_eur),
    moveType: row.move_type || null,
    sourceName: row.source_name || null,
    sourceUrl: row.source_endpoint || null,
    confidence: row.confidence_level || null,
    notes: row.notes || null,
  }));

export function getClubBySlug(slug) {
  return clubConfigBySlug[slug] ?? null;
}

export function getClubRows(clubId) {
  return clubSeasonRecordsByClub[clubId] ?? [];
}

export function getRowsInRange(clubIds, startSeason, endSeason) {
  const startYear = seasonToStartYear(startSeason);
  const endYear = seasonToStartYear(endSeason);
  return clubSeasonRecords.filter(
    (row) =>
      clubIds.includes(row.clubId) &&
      row.seasonStartYear >= startYear &&
      row.seasonStartYear <= endYear,
  );
}

export function getMetric(metricId) {
  return metricRegistry[metricId];
}

export function getMetricValue(metricId, row) {
  return metricRegistry[metricId].getValue(row);
}

export function getMetricCoverage(metricId, rows, { compareMode = false } = {}) {
  const metric = getMetric(metricId);
  const total = rows.length;
  const filled = rows.filter((row) => getMetricValue(metricId, row) !== null).length;

  if ((compareMode && !metric.compareEnabled) || (!compareMode && !metric.profileEnabled)) {
    return { status: "coming-soon", filled, total };
  }

  if (!filled) {
    return { status: "coming-soon", filled, total };
  }

  if (filled === total) {
    return { status: "complete", filled, total };
  }

  return { status: "partial", filled, total };
}

function aggregateMetric(metric, rows) {
  if (!rows.length) return null;

  if (metric.aggregation.type === "sum") {
    return rows.reduce((sum, row) => sum + metric.getValue(row), 0);
  }

  if (metric.aggregation.type === "average") {
    return rows.reduce((sum, row) => sum + metric.getValue(row), 0) / rows.length;
  }

  if (metric.aggregation.type === "latest") {
    return rows[rows.length - 1] ? metric.getValue(rows[rows.length - 1]) : null;
  }

  if (metric.aggregation.type === "weighted-ratio") {
    const numerator = rows.reduce((sum, row) => sum + (metric.aggregation.numeratorAccessor(row) ?? 0), 0);
    const denominator = rows.reduce((sum, row) => sum + (metric.aggregation.denominatorAccessor(row) ?? 0), 0);
    if (!denominator) return null;
    return numerator / denominator;
  }

  return null;
}

export function getComparisonChartData(clubIds, startSeason, endSeason, metricId) {
  const startYear = seasonToStartYear(startSeason);
  const endYear = seasonToStartYear(endSeason);
  return comparisonSeasons
    .filter((season) => {
      const year = seasonToStartYear(season);
      return year >= startYear && year <= endYear;
    })
    .map((season) => {
      const row = { season };
      for (const clubId of clubIds) {
        const found = clubSeasonRecords.find((record) => record.clubId === clubId && record.season === season);
        row[clubId] = found ? getMetricValue(metricId, found) : null;
      }
      return row;
    });
}

export function getComparisonRanking(clubIds, startSeason, endSeason, metricId) {
  const metric = getMetric(metricId);
  if (!metric.compareEnabled) {
    return { status: "coming-soon", rows: [], note: "This metric is not ready for cross-club comparison yet." };
  }

  const selectedRows = getRowsInRange(clubIds, startSeason, endSeason);
  const seasonsInRange = comparisonSeasons.filter((season) => {
    const year = seasonToStartYear(season);
    return year >= seasonToStartYear(startSeason) && year <= seasonToStartYear(endSeason);
  });

  const seasonsByClub = clubIds.map((clubId) => {
    const set = new Set(
      selectedRows
        .filter((row) => row.clubId === clubId && getMetricValue(metricId, row) !== null)
        .map((row) => row.season),
    );
    return set;
  });

  const commonSeasons = sortSeasonsAscending([...intersect(seasonsByClub)]);
  if (!commonSeasons.length) {
    return {
      status: "insufficient",
      rows: [],
      note: "Insufficient comparable coverage across the selected clubs and period.",
    };
  }

  const useCommonPeriod = commonSeasons.length !== seasonsInRange.length;
  const seasonsToUse = useCommonPeriod ? commonSeasons : seasonsInRange;

  const rankingRows = clubIds
    .map((clubId) => {
      const clubRows = selectedRows
        .filter((row) => row.clubId === clubId && seasonsToUse.includes(row.season))
        .filter((row) => getMetricValue(metricId, row) !== null)
        .sort((left, right) => left.seasonStartYear - right.seasonStartYear);

      if (!clubRows.length) return null;

      return {
        clubId,
        value: aggregateMetric(metric, clubRows),
        seasonsUsed: clubRows.map((row) => row.season),
      };
    })
    .filter(Boolean);

  if (rankingRows.length !== clubIds.length || rankingRows.some((row) => row.value === null)) {
    return {
      status: "insufficient",
      rows: [],
      note: "Insufficient comparable coverage across the selected clubs and period.",
    };
  }

  rankingRows.sort((left, right) => {
    if (metric.higherIsBetter) return right.value - left.value;
    return left.value - right.value;
  });

  const note = useCommonPeriod
    ? `Ranking uses ${commonSeasons[0]} to ${commonSeasons[commonSeasons.length - 1]}, the common period with available data.`
    : metric.aggregation.type === "latest"
      ? `Ranking uses the latest comparable season in range: ${seasonsToUse[seasonsToUse.length - 1]}.`
      : null;

  return { status: "ready", rows: rankingRows, note };
}

export function getLatestMetricObservation(clubId, metricId) {
  const rows = [...getClubRows(clubId)].sort((left, right) => right.seasonStartYear - left.seasonStartYear);
  for (const row of rows) {
    const value = getMetricValue(metricId, row);
    if (value !== null) {
      return { season: row.season, value, row };
    }
  }
  return null;
}

export function getClubCardsData() {
  return clubConfigs.map((club) => ({
    club,
    revenue: getLatestMetricObservation(club.id, "revenue"),
    netTransferSpend: getLatestMetricObservation(club.id, "netTransferSpend"),
    leaguePosition: getLatestMetricObservation(club.id, "leaguePosition"),
  }));
}

export function getClubTransferLeaders(clubId, season, direction) {
  return clubTransferRows
    .filter((row) => row.clubId === clubId && row.season === season && row.direction === direction)
    .filter((row) => row.feeEur !== null)
    .sort((left, right) => right.feeEur - left.feeEur)
    .slice(0, 5);
}

export function getClubProfileCoverage(clubId) {
  const rows = getClubRows(clubId);
  return {
    transfers: getMetricCoverage("netTransferSpend", rows),
    finance: getMetricCoverage("revenue", rows),
    performance: getMetricCoverage("points", rows),
    trophies: getMetricCoverage("trophies", rows),
  };
}

export function getSourceSectionsForMetric(metricId, row) {
  const metric = getMetric(metricId);
  const value = metric.formatValue(getMetricValue(metricId, row));

  if (metric.category === "transfers") {
    return [
      {
        title: `${row.clubName} · ${row.season}`,
        fields: [
          { label: "Metric", value: metric.label },
          { label: "Reported value", value },
          { label: "Source", value: row.transfers.sourceName || "—" },
          { label: "Source URL", value: row.transfers.sourceUrl || "—", href: row.transfers.sourceUrl || null },
          { label: "Collected", value: row.transfers.collectedAt || "—" },
          { label: "Confidence", value: row.transfers.confidence || "—" },
          { label: "Notes", value: row.transfers.notes || "—" },
        ],
      },
    ];
  }

  if (metric.category === "finances") {
    return [
      {
        title: `${row.clubName} · ${row.season}`,
        fields: [
          { label: "Metric", value: metric.label },
          { label: "Reported value", value },
          { label: "Reported currency", value: row.finance.currency || "—" },
          { label: "Source document", value: row.finance.sourceDocument || "—" },
          { label: "Source URL", value: row.finance.sourceUrl || "—", href: row.finance.sourceUrl || null },
          { label: "Financial year end", value: row.finance.reportingDate || "—" },
          { label: "Confidence", value: row.finance.confidence || "—" },
          { label: "Manual review", value: row.finance.requiresManualReview ? "Yes" : "No" },
          { label: "Notes", value: row.finance.notes || "—" },
        ],
      },
    ];
  }

  if (metric.category === "performance") {
    return [
      {
        title: `${row.clubName} · ${row.season}`,
        fields: [
          { label: "Metric", value: metric.label },
          { label: "Reported value", value },
          { label: "Source", value: row.performance.sourceName || "—" },
          { label: "Source URL", value: row.performance.sourceUrl || "—", href: row.performance.sourceUrl || null },
          { label: "Evidence", value: row.performance.evidence || "—" },
          { label: "Confidence", value: row.performance.confidence || "—" },
          { label: "Notes", value: row.performance.notes || "—" },
        ],
      },
    ];
  }

  return [
    {
      title: `${row.clubName} · ${row.season}`,
      fields: [
        { label: "Metric", value: metric.label },
        { label: "Reported value", value },
        { label: "Source", value: row.achievements.sourceName || "—" },
        { label: "Source URL", value: row.achievements.sourceUrl || "—", href: row.achievements.sourceUrl || null },
        { label: "Confidence", value: row.achievements.confidence || "—" },
        { label: "Notes", value: row.achievements.notes || "—" },
      ],
    },
  ];
}

export function getCompareSourceSections(metricId, clubIds, startSeason, endSeason) {
  const rows = getRowsInRange(clubIds, startSeason, endSeason);
  return clubIds
    .map((clubId) => {
      const latestRow = [...rows]
        .filter((row) => row.clubId === clubId && getMetricValue(metricId, row) !== null)
        .sort((left, right) => right.seasonStartYear - left.seasonStartYear)[0];

      if (!latestRow) return null;
      return getSourceSectionsForMetric(metricId, latestRow)[0];
    })
    .filter(Boolean);
}

export function getProfileSectionSourceSections(clubId, metricIds) {
  return metricIds
    .map((metricId) => {
      const latest = getLatestMetricObservation(clubId, metricId);
      if (!latest) return null;
      return getSourceSectionsForMetric(metricId, latest.row)[0];
    })
    .filter(Boolean);
}

export function getProfileSectionStatus(clubId, metricIds) {
  const rows = getClubRows(clubId);
  const totals = metricIds.map((metricId) => getMetricCoverage(metricId, rows));
  if (!totals.some((item) => item.filled > 0)) {
    return { status: "coming-soon", filled: 0, total: rows.length };
  }
  if (totals.every((item) => item.status === "complete")) {
    return { status: "complete", filled: rows.length, total: rows.length };
  }
  const filled = Math.max(...totals.map((item) => item.filled));
  return { status: "partial", filled, total: rows.length };
}

export function getMetricOptionsForCompare() {
  return compareMetricGroups.map((group) => ({
    ...group,
    metrics: group.metricIds.map((metricId) => metricRegistry[metricId]),
  }));
}
