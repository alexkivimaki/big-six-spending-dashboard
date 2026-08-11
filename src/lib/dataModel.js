import clubSeasonData from "../data/clubSeasonData.json";
import clubSeasonMasterData from "../data/clubSeasonMasterData.json";
import clubRevenueData from "../data/clubRevenueData.json";
import clubTransferRowsData from "../data/clubTransferRowsData.json";
import { clubConfigById, clubConfigBySlug, clubConfigs } from "../config/clubConfig";
import { DISPLAY_CURRENCY, fxReference } from "../config/displayCurrency";
import { compareMetricGroups, getMetric, metricRegistry } from "../config/metricRegistry";
import { VALUE_BASIS, inflationConfig } from "../config/valueBasis";

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

function firstNumber(...values) {
  for (const value of values) {
    const numeric = toNumber(value);
    if (numeric !== null) return numeric;
  }
  return null;
}

function buildCurrencyValues({
  gbp = [],
  eur = [],
  usd = [],
  gbpReal = [],
  eurReal = [],
  usdReal = [],
} = {}) {
  return {
    nominal: {
      [DISPLAY_CURRENCY.GBP]: firstNumber(...gbp),
      [DISPLAY_CURRENCY.EUR]: firstNumber(...eur),
      [DISPLAY_CURRENCY.USD]: firstNumber(...usd),
    },
    real: {
      [DISPLAY_CURRENCY.GBP]: firstNumber(...gbpReal),
      [DISPLAY_CURRENCY.EUR]: firstNumber(...eurReal),
      [DISPLAY_CURRENCY.USD]: firstNumber(...usdReal),
    },
  };
}

function getCurrencyValue(values, valueBasis, displayCurrency) {
  if (!values) return null;
  return valueBasis === VALUE_BASIS.inflationAdjusted
    ? values.real?.[displayCurrency] ?? null
    : values.nominal?.[displayCurrency] ?? null;
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
  const revenueOriginal = firstNumber(masterRow?.total_revenue_original, revenueRow?.turnover_original);
  const staffCostsOriginal = firstNumber(masterRow?.official_staff_costs_original, revenueRow?.wage_bill_original);
  const revenueEur = firstNumber(masterRow?.revenue_eur, revenueRow?.total_revenue_eur, baseRow.revenue_eur);
  const staffCostsEur = firstNumber(masterRow?.official_staff_costs_eur, baseRow.official_staff_costs_eur);
  const matchdayOriginal = firstNumber(
    masterRow?.matchday_revenue_original,
    revenueRow?.gate_and_matchday_income_original,
  );
  const broadcastOriginal = firstNumber(
    masterRow?.broadcast_revenue_original,
    revenueRow?.tv_and_broadcasting_original,
  );
  const commercialOriginal = firstNumber(
    masterRow?.commercial_revenue_original,
    revenueRow?.commercial_income_original,
  );
  const matchdayEur = firstNumber(masterRow?.matchday_revenue_eur, revenueRow?.matchday_revenue_eur);
  const broadcastEur = firstNumber(masterRow?.broadcast_revenue_eur, revenueRow?.broadcast_revenue_eur);
  const commercialEur = firstNumber(masterRow?.commercial_revenue_eur, revenueRow?.commercial_revenue_eur);
  const sportingRevenueEur =
    matchdayEur !== null && broadcastEur !== null ? matchdayEur + broadcastEur : null;
  const sportingRevenueOriginal =
    matchdayOriginal !== null && broadcastOriginal !== null ? matchdayOriginal + broadcastOriginal : null;
  const staffCostToRevenueRatio =
    revenueOriginal && staffCostsOriginal ? staffCostsOriginal / revenueOriginal : null;
  const estimatedPlayerWagesEur = firstNumber(masterRow?.estimated_player_wages_eur, baseRow.estimated_player_wages_eur);
  const economicFactorsComplete =
    toBoolean(masterRow?.economic_factors_complete) || toBoolean(revenueRow?.economic_factors_complete) || toBoolean(baseRow.economic_factors_complete);

  const grossSpend = buildCurrencyValues({
    gbp: [baseRow.gross_transfer_spend_gbp],
    eur: [baseRow.gross_transfer_spend_eur],
    usd: [baseRow.gross_transfer_spend_usd],
    gbpReal: [baseRow.gross_transfer_spend_gbp_real_2025_26],
    eurReal: [baseRow.gross_transfer_spend_eur_real_2025_26],
    usdReal: [baseRow.gross_transfer_spend_usd_real_2025_26],
  });
  const income = buildCurrencyValues({
    gbp: [baseRow.transfer_income_gbp],
    eur: [baseRow.transfer_income_eur],
    usd: [baseRow.transfer_income_usd],
    gbpReal: [baseRow.transfer_income_gbp_real_2025_26],
    eurReal: [baseRow.transfer_income_eur_real_2025_26],
    usdReal: [baseRow.transfer_income_usd_real_2025_26],
  });
  const netSpend = buildCurrencyValues({
    gbp: [baseRow.net_transfer_spend_gbp],
    eur: [baseRow.net_transfer_spend_eur],
    usd: [baseRow.net_transfer_spend_usd],
    gbpReal: [baseRow.net_transfer_spend_gbp_real_2025_26],
    eurReal: [baseRow.net_transfer_spend_eur_real_2025_26],
    usdReal: [baseRow.net_transfer_spend_usd_real_2025_26],
  });
  const financeRevenue = buildCurrencyValues({
    gbp: [masterRow?.total_revenue_gbp, revenueRow?.total_revenue_gbp, revenueRow?.turnover_gbp, revenueOriginal],
    eur: [masterRow?.revenue_eur, masterRow?.total_revenue_eur, revenueRow?.total_revenue_eur, revenueRow?.turnover_eur, revenueEur],
    usd: [masterRow?.total_revenue_usd, revenueRow?.total_revenue_usd, revenueRow?.turnover_usd],
    gbpReal: [masterRow?.total_revenue_gbp_real_2025_26, revenueRow?.total_revenue_gbp_real_2025_26, revenueRow?.turnover_gbp_real_2025_26],
    eurReal: [masterRow?.total_revenue_eur_real_2025_26, revenueRow?.total_revenue_eur_real_2025_26, revenueRow?.turnover_eur_real_2025_26],
    usdReal: [masterRow?.total_revenue_usd_real_2025_26, revenueRow?.total_revenue_usd_real_2025_26, revenueRow?.turnover_usd_real_2025_26],
  });
  const financeStaffCosts = buildCurrencyValues({
    gbp: [masterRow?.official_staff_costs_gbp, revenueRow?.wage_bill_gbp, staffCostsOriginal],
    eur: [masterRow?.official_staff_costs_eur, revenueRow?.wage_bill_eur, revenueRow?.staff_costs_eur, staffCostsEur],
    usd: [masterRow?.official_staff_costs_usd, revenueRow?.wage_bill_usd, revenueRow?.staff_costs_usd],
    gbpReal: [masterRow?.official_staff_costs_gbp_real_2025_26, revenueRow?.wage_bill_gbp_real_2025_26, revenueRow?.staff_costs_gbp_real_2025_26],
    eurReal: [masterRow?.official_staff_costs_eur_real_2025_26, revenueRow?.wage_bill_eur_real_2025_26, revenueRow?.staff_costs_eur_real_2025_26],
    usdReal: [masterRow?.official_staff_costs_usd_real_2025_26, revenueRow?.wage_bill_usd_real_2025_26, revenueRow?.staff_costs_usd_real_2025_26],
  });
  const financeSportingRevenue = buildCurrencyValues({
    gbp: [masterRow?.sporting_revenue_gbp, revenueRow?.sporting_revenue_gbp, sportingRevenueOriginal],
    eur: [masterRow?.sporting_revenue_eur, revenueRow?.sporting_revenue_eur, sportingRevenueEur],
    usd: [masterRow?.sporting_revenue_usd, revenueRow?.sporting_revenue_usd],
    gbpReal: [masterRow?.sporting_revenue_gbp_real_2025_26, revenueRow?.sporting_revenue_gbp_real_2025_26],
    eurReal: [masterRow?.sporting_revenue_eur_real_2025_26, revenueRow?.sporting_revenue_eur_real_2025_26],
    usdReal: [masterRow?.sporting_revenue_usd_real_2025_26, revenueRow?.sporting_revenue_usd_real_2025_26],
  });

  return {
    clubId: club.id,
    clubSlug: club.slug,
    clubName: club.name,
    season: baseRow.season,
    seasonStartYear: seasonToStartYear(baseRow.season),
    economics: {
      gbpToEurRate: firstNumber(baseRow.gbp_to_eur_rate, masterRow?.gbp_to_eur_rate, revenueRow?.gbp_to_eur_rate),
      eurToUsdRate: firstNumber(baseRow.eur_to_usd_rate, masterRow?.eur_to_usd_rate, revenueRow?.eur_to_usd_rate),
      gbpToUsdRate: firstNumber(baseRow.gbp_to_usd_rate, masterRow?.gbp_to_usd_rate, revenueRow?.gbp_to_usd_rate),
      inflationAdjustmentToBase: firstNumber(
        baseRow.inflation_adjustment_to_2025_26,
        masterRow?.inflation_adjustment_to_2025_26,
        revenueRow?.inflation_adjustment_to_2025_26,
      ),
      realPriceBasisLabel:
        baseRow.real_price_basis_label ??
        masterRow?.real_price_basis_label ??
        revenueRow?.real_price_basis_label ??
        `${inflationConfig.baseSeason} prices`,
      fxSource: baseRow.fx_source ?? masterRow?.fx_source ?? revenueRow?.fx_source ?? null,
      inflationSource:
        baseRow.inflation_source ?? masterRow?.inflation_source ?? revenueRow?.inflation_source ?? null,
      notes:
        baseRow.economic_factor_notes ??
        masterRow?.finance_economic_factor_notes ??
        revenueRow?.economic_factor_notes ??
        null,
      complete: economicFactorsComplete,
    },
    transfers: {
      grossSpend,
      grossSpendEur: toNumber(baseRow.gross_transfer_spend_eur),
      income,
      incomeEur: toNumber(baseRow.transfer_income_eur),
      netSpend,
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
      currency: masterRow?.currency_original ?? baseRow.currency_original ?? "GBP",
      revenue: financeRevenue,
      revenueOriginal,
      revenueEur,
      staffCosts: financeStaffCosts,
      staffCostsOriginal,
      staffCostsEur,
      staffCostToRevenueRatio,
      profitBeforeTaxOriginal:
        toNumber(masterRow?.profit_loss_before_tax_original) ??
        toNumber(revenueRow?.profit_loss_before_tax_original),
      profitBeforeTaxEur: toNumber(masterRow?.profit_loss_before_tax_eur),
      netDebtOriginal:
        toNumber(masterRow?.net_debt_original) ?? toNumber(revenueRow?.net_debt_original),
      netDebtEur: toNumber(masterRow?.net_debt_eur),
      matchdayOriginal,
      matchdayEur,
      broadcastOriginal,
      broadcastEur,
      commercialOriginal,
      commercialEur,
      sportingRevenue: financeSportingRevenue,
      sportingRevenueOriginal,
      sportingRevenueEur,
      playerAmortisationOriginal: toNumber(masterRow?.player_amortisation_original),
      profitOnPlayerSalesOriginal: toNumber(masterRow?.profit_on_player_sales_original),
      hasData:
        revenueOriginal !== null ||
        staffCostsOriginal !== null ||
        revenueEur !== null ||
        sportingRevenueEur !== null ||
        financeRevenue.nominal[DISPLAY_CURRENCY.EUR] !== null,
      ...createFinanceSources(masterRow, revenueRow),
    },
    performance: {
      points: toNumber(masterRow?.points) ?? toNumber(baseRow.points),
      leaguePosition: toNumber(masterRow?.league_position) ?? toNumber(baseRow.league_position),
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
    wages: {
      estimatedPlayerWagesEur,
      estimatedPlayerWagesOriginal: toNumber(baseRow.estimated_player_wages_original),
      estimatedPlayerWagesOriginalCurrency:
        baseRow.estimated_player_wages_original_currency ?? null,
      weeklyWagesOriginal: toNumber(baseRow.weekly_wages_original),
      sourceName: baseRow.source_name_wages ?? null,
      sourceUrl: baseRow.source_url ?? null,
      confidence: baseRow.confidence_level_wages ?? null,
      notes: baseRow.notes_wages ?? null,
      requiresManualReview: toBoolean(baseRow.requires_manual_review),
      hasData: estimatedPlayerWagesEur !== null,
    },
    efficiency: {
      rawPlayerCostEur: toNumber(masterRow?.raw_player_cost_eur) ?? toNumber(baseRow.raw_player_cost_eur),
      costPerPoint: toNumber(masterRow?.cost_per_point) ?? toNumber(baseRow.cost_per_point),
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
  normalizeClubSeason(
    row,
    masterByKey.get(pairKey(row.club_id, row.season)),
    revenueByKey.get(pairKey(row.club_id, row.season)),
  ),
);

export const clubSeasonRecordsByClub = Object.fromEntries(
  clubConfigs.map((club) => [club.id, clubSeasonRecords.filter((row) => row.clubId === club.id)]),
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

function inflationUnavailableForMetric(metric, valueBasis) {
  return (
    valueBasis === VALUE_BASIS.inflationAdjusted &&
    metric.isMonetary &&
    metric.supportsInflationAdjustment !== false &&
    !inflationConfig.available
  );
}

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

export function calculateMetricValue(
  row,
  metricId,
  valueBasis = VALUE_BASIS.nominal,
  displayCurrency = DISPLAY_CURRENCY.EUR,
) {
  const metric = getMetric(metricId);
  if (!metric) return null;

  if (inflationUnavailableForMetric(metric, valueBasis)) {
    return metric.format === "percentage"
      ? calculateMetricValue(row, metricId, VALUE_BASIS.nominal, displayCurrency)
      : null;
  }

  switch (metricId) {
    case "transferSpend":
    case "grossTransferSpend":
      return getCurrencyValue(row.transfers.grossSpend, valueBasis, displayCurrency);
    case "playerWages":
      return getCurrencyValue(row.finance.staffCosts, valueBasis, displayCurrency);
    case "grossSquadInvestment": {
      const transferSpend = calculateMetricValue(row, "transferSpend", valueBasis, displayCurrency);
      const playerWages = calculateMetricValue(row, "playerWages", valueBasis, displayCurrency);
      return transferSpend !== null && playerWages !== null ? transferSpend + playerWages : null;
    }
    case "playerSales":
    case "transferIncome":
      return getCurrencyValue(row.transfers.income, valueBasis, displayCurrency);
    case "netTransferSpend": {
      const exportedValue = getCurrencyValue(row.transfers.netSpend, valueBasis, displayCurrency);
      if (exportedValue !== null) {
        return exportedValue;
      }
      const transferSpend = calculateMetricValue(row, "transferSpend", valueBasis, displayCurrency);
      const playerSales = calculateMetricValue(row, "playerSales", valueBasis, displayCurrency);
      return transferSpend !== null && playerSales !== null ? transferSpend - playerSales : null;
    }
    case "netSquadInvestment": {
      const transferSpend = calculateMetricValue(row, "transferSpend", valueBasis, displayCurrency);
      const playerWages = calculateMetricValue(row, "playerWages", valueBasis, displayCurrency);
      const playerSales = calculateMetricValue(row, "playerSales", valueBasis, displayCurrency);
      return transferSpend !== null && playerWages !== null && playerSales !== null
        ? transferSpend + playerWages - playerSales
        : null;
    }
    case "squadCostAfterSportingRevenue": {
      const netSquadInvestment = calculateMetricValue(row, "netSquadInvestment", valueBasis, displayCurrency);
      const sportingRevenue = calculateMetricValue(row, "sportingRevenue", valueBasis, displayCurrency);
      return netSquadInvestment !== null && sportingRevenue !== null
        ? netSquadInvestment - sportingRevenue
        : null;
    }
    case "sportingRevenue":
      return getCurrencyValue(row.finance.sportingRevenue, valueBasis, displayCurrency);
    case "totalRevenue":
      return getCurrencyValue(row.finance.revenue, valueBasis, displayCurrency);
    case "squadInvestmentRevenueRatio": {
      const netSquadInvestment = calculateMetricValue(row, "netSquadInvestment", valueBasis, displayCurrency);
      const totalRevenue = calculateMetricValue(row, "totalRevenue", valueBasis, displayCurrency);
      return netSquadInvestment !== null && totalRevenue ? netSquadInvestment / totalRevenue : null;
    }
    case "revenue":
      return row.finance.revenueOriginal;
    case "staffCosts":
      return row.finance.staffCostsOriginal;
    case "staffCostToRevenueRatio":
      return row.finance.staffCostToRevenueRatio;
    case "profitBeforeTax":
      return row.finance.profitBeforeTaxOriginal;
    case "netDebt":
      return row.finance.netDebtOriginal;
    case "points":
      return row.performance.points;
    case "leaguePosition":
      return row.performance.leaguePosition;
    case "trophies":
      return row.achievements.majorTrophyCount;
    case "rawPlayerCost":
      return row.efficiency.rawPlayerCostEur;
    case "costPerPoint":
      return row.efficiency.costPerPoint;
    default:
      return null;
  }
}

export function getMetricCoverage(
  metricId,
  rows,
  {
    compareMode = false,
    valueBasis = VALUE_BASIS.nominal,
    displayCurrency = DISPLAY_CURRENCY.EUR,
  } = {},
) {
  const metric = getMetric(metricId);
  const total = rows.length;

  if (!metric) {
    return { status: "coming-soon", filled: 0, total };
  }

  if ((compareMode && !metric.compareEnabled) || (!compareMode && !metric.profileEnabled)) {
    return { status: "coming-soon", filled: 0, total };
  }

  if (inflationUnavailableForMetric(metric, valueBasis) && metric.format !== "percentage") {
    return { status: "coming-soon", filled: 0, total };
  }

  const filled = rows.filter((row) => calculateMetricValue(row, metricId, valueBasis, displayCurrency) !== null).length;

  if (!filled) {
    return { status: "coming-soon", filled, total };
  }

  if (filled === total) {
    return { status: "complete", filled, total };
  }

  return { status: "partial", filled, total };
}

function aggregateMetricRows(
  metricId,
  rows,
  { valueBasis = VALUE_BASIS.nominal, displayCurrency = DISPLAY_CURRENCY.EUR } = {},
) {
  const metric = getMetric(metricId);
  if (!metric || !rows.length) return null;

  if (metric.aggregation.type === "sum") {
    return rows.reduce((sum, row) => sum + calculateMetricValue(row, metricId, valueBasis, displayCurrency), 0);
  }

  if (metric.aggregation.type === "average") {
    return rows.reduce((sum, row) => sum + calculateMetricValue(row, metricId, valueBasis, displayCurrency), 0) / rows.length;
  }

  if (metric.aggregation.type === "latest") {
    const latestRow = rows[rows.length - 1];
    return latestRow ? calculateMetricValue(latestRow, metricId, valueBasis, displayCurrency) : null;
  }

  if (metric.aggregation.type === "weighted-ratio") {
    const numerator = rows.reduce((sum, row) => sum + (metric.aggregation.numeratorAccessor(row) ?? 0), 0);
    const denominator = rows.reduce((sum, row) => sum + (metric.aggregation.denominatorAccessor(row) ?? 0), 0);
    if (!denominator) return null;
    return numerator / denominator;
  }

  if (metric.aggregation.type === "ratio-of-sums") {
    const numerator = aggregateMetricRows(metric.aggregation.numeratorMetricId, rows, { valueBasis, displayCurrency });
    const denominator = aggregateMetricRows(metric.aggregation.denominatorMetricId, rows, { valueBasis, displayCurrency });
    if (numerator === null || denominator === null || denominator === 0) return null;
    return numerator / denominator;
  }

  return null;
}

export function getComparisonChartData(
  clubIds,
  startSeason,
  endSeason,
  metricId,
  { valueBasis = VALUE_BASIS.nominal, displayCurrency = DISPLAY_CURRENCY.EUR } = {},
) {
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
        row[clubId] = found ? calculateMetricValue(found, metricId, valueBasis, displayCurrency) : null;
      }
      return row;
    });
}

export function getComparisonRanking(
  clubIds,
  startSeason,
  endSeason,
  metricId,
  { valueBasis = VALUE_BASIS.nominal, displayCurrency = DISPLAY_CURRENCY.EUR } = {},
) {
  const metric = getMetric(metricId);
  if (!metric?.compareEnabled) {
    return { status: "coming-soon", rows: [], note: "This metric is not configured for cross-club comparison yet." };
  }

  const selectedRows = getRowsInRange(clubIds, startSeason, endSeason);
  const coverage = getMetricCoverage(metricId, selectedRows, { compareMode: true, valueBasis, displayCurrency });
  if (coverage.status === "coming-soon") {
    return {
      status: "coming-soon",
      rows: [],
      note:
        valueBasis === VALUE_BASIS.inflationAdjusted && metric.isMonetary && !inflationConfig.available
          ? inflationConfig.description
          : "This metric does not yet have enough comparable data for a ranking.",
    };
  }

  const seasonsInRange = comparisonSeasons.filter((season) => {
    const year = seasonToStartYear(season);
    return year >= seasonToStartYear(startSeason) && year <= seasonToStartYear(endSeason);
  });

  const seasonsByClub = clubIds.map((clubId) => {
    const set = new Set(
      selectedRows
        .filter((row) => row.clubId === clubId && calculateMetricValue(row, metricId, valueBasis, displayCurrency) !== null)
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
        .filter((row) => calculateMetricValue(row, metricId, valueBasis, displayCurrency) !== null)
        .sort((left, right) => left.seasonStartYear - right.seasonStartYear);

      if (!clubRows.length) return null;

      return {
        clubId,
        value: aggregateMetricRows(metricId, clubRows, { valueBasis, displayCurrency }),
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
    if (metric.higherIsBetter === false) return left.value - right.value;
    return right.value - left.value;
  });

  const note = useCommonPeriod
    ? `Ranking uses ${commonSeasons[0]}-${commonSeasons[commonSeasons.length - 1]}, the common period with available data.`
    : metric.aggregation.type === "latest"
      ? `Ranking uses the latest comparable season in range: ${seasonsToUse[seasonsToUse.length - 1]}.`
      : metric.aggregation.type === "ratio-of-sums"
        ? "The selected-period ratio uses summed squad investment divided by summed revenue."
        : null;

  return { status: "ready", rows: rankingRows, note };
}

export function getLatestMetricObservation(
  clubId,
  metricId,
  { valueBasis = VALUE_BASIS.nominal, displayCurrency = DISPLAY_CURRENCY.EUR } = {},
) {
  const rows = [...getClubRows(clubId)].sort((left, right) => right.seasonStartYear - left.seasonStartYear);
  for (const row of rows) {
    const value = calculateMetricValue(row, metricId, valueBasis, displayCurrency);
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

function getMetricMethodologySection(
  metricId,
  valueBasis = VALUE_BASIS.nominal,
  displayCurrency = DISPLAY_CURRENCY.EUR,
) {
  const metric = getMetric(metricId);
  if (!metric) return null;

  const priceBasis =
    metric.format === "percentage"
      ? metric.inflationBehavior ?? "Same-period ratios are unchanged by inflation adjustment."
      : valueBasis === VALUE_BASIS.inflationAdjusted
        ? inflationConfig.available
          ? `Inflation adjusted to ${inflationConfig.baseSeason} prices`
          : inflationConfig.description
        : "Nominal values";

  return {
    title: `${metric.label} methodology`,
    fields: [
      { label: "Metric", value: metric.label },
      { label: "Formula", value: metric.formulaLabel || "—" },
      { label: "Price basis", value: priceBasis },
      ...(metric.isMonetary
        ? [
            { label: "Display currency", value: displayCurrency },
            {
              label: "FX source",
              value: fxReference.description,
              href: fxReference.sourceUrl,
            },
            ...(valueBasis === VALUE_BASIS.inflationAdjusted
              ? [
                  {
                    label: "Inflation source",
                    value: inflationConfig.description,
                    href: inflationConfig.sourceUrl,
                  },
                ]
              : []),
          ]
        : []),
      { label: "Method", value: metric.methodologyNote || metric.description || "—" },
      { label: "Source layer", value: metric.sourceType || "—" },
    ],
  };
}

function getSourceSectionsForMetric(
  metricId,
  row,
  valueBasis = VALUE_BASIS.nominal,
  displayCurrency = DISPLAY_CURRENCY.EUR,
) {
  const metric = getMetric(metricId);
  if (!metric || !row) return [];
  const value = metric.formatValue(calculateMetricValue(row, metricId, valueBasis, displayCurrency), {
    displayCurrency,
  });
  const sections = [];

  if (metric.sourceGroups?.includes("transfers")) {
    sections.push({
      title: `${row.clubName} · ${row.season} transfer layer`,
      fields: [
        { label: "Metric", value: metric.label },
        { label: "Reported value", value },
        { label: "Source", value: row.transfers.sourceName || "—" },
        { label: "Source URL", value: row.transfers.sourceUrl || "—", href: row.transfers.sourceUrl || null },
        { label: "Collected", value: row.transfers.collectedAt || "—" },
        { label: "Confidence", value: row.transfers.confidence || "—" },
        { label: "Notes", value: row.transfers.notes || "—" },
      ],
    });
  }

  if (metric.sourceGroups?.includes("finances")) {
    sections.push({
      title: `${row.clubName} · ${row.season} finance layer`,
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
    });
  }

  if (metric.sourceGroups?.includes("performance")) {
    sections.push({
      title: `${row.clubName} · ${row.season} performance layer`,
      fields: [
        { label: "Metric", value: metric.label },
        { label: "Reported value", value },
        { label: "Source", value: row.performance.sourceName || "—" },
        { label: "Source URL", value: row.performance.sourceUrl || "—", href: row.performance.sourceUrl || null },
        { label: "Evidence", value: row.performance.evidence || "—" },
        { label: "Confidence", value: row.performance.confidence || "—" },
        { label: "Notes", value: row.performance.notes || "—" },
      ],
    });
  }

  if (metric.sourceGroups?.includes("achievements")) {
    sections.push({
      title: `${row.clubName} · ${row.season} achievements layer`,
      fields: [
        { label: "Metric", value: metric.label },
        { label: "Reported value", value },
        { label: "Source", value: row.achievements.sourceName || "—" },
        { label: "Source URL", value: row.achievements.sourceUrl || "—", href: row.achievements.sourceUrl || null },
        { label: "Confidence", value: row.achievements.confidence || "—" },
        { label: "Notes", value: row.achievements.notes || "—" },
      ],
    });
  }

  return sections;
}

export function getCompareSourceSections(
  metricId,
  clubIds,
  startSeason,
  endSeason,
  valueBasis = VALUE_BASIS.nominal,
  displayCurrency = DISPLAY_CURRENCY.EUR,
) {
  const rows = getRowsInRange(clubIds, startSeason, endSeason);
  const sections = [];
  const methodologySection = getMetricMethodologySection(metricId, valueBasis, displayCurrency);
  if (methodologySection) sections.push(methodologySection);

  for (const clubId of clubIds) {
    const latestRow = [...rows]
      .filter((row) => row.clubId === clubId && calculateMetricValue(row, metricId, valueBasis, displayCurrency) !== null)
      .sort((left, right) => right.seasonStartYear - left.seasonStartYear)[0];

    if (!latestRow) continue;
    sections.push(...getSourceSectionsForMetric(metricId, latestRow, valueBasis, displayCurrency));
  }

  return sections;
}

export function getProfileSectionSourceSections(clubId, metricIds) {
  return metricIds
    .flatMap((metricId) => {
      const latest = getLatestMetricObservation(clubId, metricId);
      if (!latest) return [];
      return getSourceSectionsForMetric(metricId, latest.row);
    });
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
