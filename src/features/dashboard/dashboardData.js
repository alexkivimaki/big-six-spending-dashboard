import clubSeasonRaw from "../../data/clubSeasonData.json?raw";
import masterRaw from "../../data/clubSeasonMasterData.json?raw";
import revenueRaw from "../../data/clubRevenueData.json?raw";
import {
  clubById,
  clubs,
  featureCards,
  metricDefinitions,
  projectScope,
} from "./dashboardConfig";

function parseLooseJson(raw) {
  return JSON.parse(raw.replace(/\bNaN\b/g, "null"));
}

function toNumber(value) {
  if (value === null || value === undefined || value === "") return null;
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
}

function toBoolean(value) {
  return value === true || value === "True";
}

function seasonStartYear(season) {
  return Number(String(season).slice(0, 4));
}

function keyFor(clubId, season) {
  return `${clubId}::${season}`;
}

const clubSeasonRows = parseLooseJson(clubSeasonRaw);
const masterRows = parseLooseJson(masterRaw);
const revenueRows = parseLooseJson(revenueRaw);

const scopeRows = clubSeasonRows
  .filter((row) => clubById[row.club_id] && seasonStartYear(row.season) >= 2008)
  .sort((left, right) => {
    const bySeason = seasonStartYear(left.season) - seasonStartYear(right.season);
    if (bySeason !== 0) return bySeason;
    return left.club_name.localeCompare(right.club_name);
  });

const masterByKey = new Map(masterRows.map((row) => [keyFor(row.club_id, row.season), row]));
const revenueByKey = new Map(revenueRows.map((row) => [keyFor(row.club_id, row.season), row]));

export const seasons = [...new Set(scopeRows.map((row) => row.season))];

export const mergedRows = scopeRows.map((row) => {
  const master = masterByKey.get(keyFor(row.club_id, row.season));
  const revenue = revenueByKey.get(keyFor(row.club_id, row.season));

  return {
    clubId: row.club_id,
    clubName: row.club_name,
    season: row.season,
    seasonStartYear: seasonStartYear(row.season),
    grossTransferSpendEur: toNumber(row.gross_transfer_spend_eur),
    transferIncomeEur: toNumber(row.transfer_income_eur),
    netTransferSpendEur: toNumber(row.net_transfer_spend_eur),
    incomingTransferCount: toNumber(row.incoming_transfer_count),
    outgoingTransferCount: toNumber(row.outgoing_transfer_count),
    points: toNumber(master?.points),
    leaguePosition: toNumber(master?.league_position),
    achievementCountTotal: toNumber(master?.achievement_count_total),
    majorTrophyCount: toNumber(master?.major_trophy_count),
    achievementsInSeason: master?.achievements_in_season ?? null,
    primaryManagerName: master?.primary_manager_name ?? null,
    managerNames: master?.manager_names ?? null,
    hasManagerData: Boolean(master?.primary_manager_name || toBoolean(master?.has_manager_data)),
    hasPerformanceData: toBoolean(master?.has_performance_data),
    hasAchievementData: toBoolean(master?.has_achievement_data),
    hasFinanceData: toBoolean(master?.has_finance_data),
    turnoverOriginal: toNumber(master?.total_revenue_original) ?? toNumber(revenue?.turnover_original),
    wageBillOriginal: toNumber(master?.official_staff_costs_original) ?? toNumber(revenue?.wage_bill_original),
    netDebtOriginal: toNumber(master?.net_debt_original) ?? toNumber(revenue?.net_debt_original),
    profitLossBeforeTaxOriginal:
      toNumber(master?.profit_loss_before_tax_original) ?? toNumber(revenue?.profit_loss_before_tax_original),
    estimatedPlayerWagesEur: toNumber(master?.estimated_player_wages_eur),
    revenueEur: toNumber(master?.revenue_eur),
    rawPlayerCostEur: toNumber(master?.raw_player_cost_eur),
    wageToRevenueRatio: toNumber(master?.wage_to_revenue_ratio),
    financeSourceDocument: master?.finance_source_document ?? revenue?.source_document ?? null,
    financeSourceUrl: master?.finance_source_url ?? revenue?.source_url ?? null,
    financeExtracted: Boolean(revenue || toBoolean(master?.has_finance_data)),
  };
});

function countWhere(predicate) {
  return mergedRows.reduce((count, row) => (predicate(row) ? count + 1 : count), 0);
}

function countFilled(key) {
  return countWhere((row) => row[key] !== null && row[key] !== undefined);
}

function metricCoverageNote(metric) {
  const count = countFilled(metric.key);
  return `${count}/${projectScope.expectedClubSeasons} club-seasons`;
}

export const metricOptions = metricDefinitions.map((metric) => ({
  ...metric,
  coverage: metricCoverageNote(metric),
}));

const transfersReady = countFilled("grossTransferSpendEur");
const managersReady = countWhere((row) => row.hasManagerData);
const performanceReady = countWhere((row) => row.hasPerformanceData);
const achievementsReady = countWhere((row) => row.hasAchievementData);
const financeReady = countWhere((row) => row.hasFinanceData);
const financeExtracted = countWhere((row) => row.financeExtracted);
const wagesReady = countFilled("estimatedPlayerWagesEur");

export const readinessCards = featureCards.map((card) => {
  if (card.key === "transfers") {
    return { ...card, coverage: `${transfersReady}/${projectScope.expectedClubSeasons} app-ready` };
  }

  if (card.key === "managers") {
    return { ...card, coverage: `${managersReady}/${projectScope.expectedClubSeasons} app-ready` };
  }

  if (card.key === "performance") {
    return { ...card, coverage: `${performanceReady}/${projectScope.expectedClubSeasons} app-ready` };
  }

  if (card.key === "achievements") {
    return { ...card, coverage: `${achievementsReady}/${projectScope.expectedClubSeasons} app-ready` };
  }

  if (card.key === "finance") {
    return {
      ...card,
      coverage: `${financeReady}/${projectScope.expectedClubSeasons} joined, ${financeExtracted}/${projectScope.expectedClubSeasons} extracted`,
    };
  }

  return { ...card, coverage: `${wagesReady}/${projectScope.expectedClubSeasons} usable` };
});

export const overviewStats = [
  {
    label: "Clubs in scope",
    value: `${clubs.length}`,
    note: "Arsenal, Chelsea, Liverpool, Manchester City, Manchester United, Tottenham Hotspur",
  },
  {
    label: "Seasons in demo",
    value: `${seasons.length}`,
    note: `${projectScope.seasonFrom} to ${projectScope.seasonTo}`,
  },
  {
    label: "Ready modules",
    value: `${readinessCards.filter((item) => item.status === "ready").length}`,
    note: "Transfers and managers are ready to visualize now",
  },
  {
    label: "Blocked modules",
    value: `${readinessCards.filter((item) => item.status === "blocked").length}`,
    note: "Finance normalization and wages still need data work",
  },
];

export function getRowsForSelection(selectedClubIds, startSeason, endSeason) {
  const startYear = seasonStartYear(startSeason);
  const endYear = seasonStartYear(endSeason);

  return mergedRows.filter(
    (row) =>
      selectedClubIds.includes(row.clubId) &&
      row.seasonStartYear >= startYear &&
      row.seasonStartYear <= endYear,
  );
}

export function aggregateClubMetric(rows, clubId, metric) {
  const clubRows = rows.filter((row) => row.clubId === clubId);
  const values = clubRows.map((row) => row[metric.key]).filter((value) => value !== null && value !== undefined);

  if (values.length === 0) {
    return null;
  }

  if (metric.aggregate === "average") {
    return values.reduce((sum, value) => sum + value, 0) / values.length;
  }

  return values.reduce((sum, value) => sum + value, 0);
}

export function getSelectionSummary(selectedClubIds, startSeason, endSeason, metric) {
  const selectionRows = getRowsForSelection(selectedClubIds, startSeason, endSeason);

  return clubs
    .filter((club) => selectedClubIds.includes(club.id))
    .map((club) => {
      const clubRows = selectionRows.filter((row) => row.clubId === club.id);
      return {
        ...club,
        selectedValue: aggregateClubMetric(selectionRows, club.id, metric),
        dataPoints: clubRows.filter((row) => row[metric.key] !== null && row[metric.key] !== undefined).length,
        managersCovered: clubRows.filter((row) => row.hasManagerData).length,
        achievementsCovered: clubRows.filter((row) => row.hasAchievementData).length,
      };
    })
    .sort((left, right) => {
      const leftValue = left.selectedValue;
      const rightValue = right.selectedValue;

      if (leftValue === null && rightValue === null) return left.name.localeCompare(right.name);
      if (leftValue === null) return 1;
      if (rightValue === null) return -1;

      if (metric.sortDirection === "asc") return leftValue - rightValue;
      return rightValue - leftValue;
    });
}

export function buildChartRows(selectedClubIds, startSeason, endSeason, metricKey) {
  const startYear = seasonStartYear(startSeason);
  const endYear = seasonStartYear(endSeason);

  return seasons
    .filter((season) => {
      const year = seasonStartYear(season);
      return year >= startYear && year <= endYear;
    })
    .map((season) => {
      const seasonRow = { season };

      selectedClubIds.forEach((clubId) => {
        const found = mergedRows.find((row) => row.clubId === clubId && row.season === season);
        seasonRow[clubId] = found ? found[metricKey] : null;
      });

      return seasonRow;
    });
}

export function getSpotlightRow(clubId, season) {
  return mergedRows.find((row) => row.clubId === clubId && row.season === season) ?? null;
}
