import { Database, Link as LinkIcon, Sparkles } from "lucide-react";

import { clubById } from "../dashboardConfig";
import {
  formatInteger,
  formatMoneyMillions,
  formatPercent,
} from "../../../shared/formatters";

function AvailabilityPill({ active, label }) {
  return <span className={`availabilityPill ${active ? "isOn" : "isOff"}`}>{label}</span>;
}

export function SeasonSpotlight({ row }) {
  if (!row) {
    return null;
  }

  const club = clubById[row.clubId];

  return (
    <section className="panel spotlightPanel">
      <div className="sectionHeading">
        <div>
          <span className="eyebrow">
            <Sparkles size={14} />
            Season spotlight
          </span>
          <h2>
            {club.name} in {row.season}
          </h2>
        </div>
        <p>
          The spotlight shows how the final club-season detail area can work once every dataset is
          fully joined.
        </p>
      </div>

      <div className="spotlightBanner" style={{ borderColor: club.color }}>
        <div className="spotlightClub">
          <span className="clubSwatch large" style={{ background: club.color }} />
          <div>
            <strong>{club.name}</strong>
            <small>{row.season}</small>
          </div>
        </div>

        <div className="availabilityRow">
          <AvailabilityPill active label="Transfers" />
          <AvailabilityPill active={row.hasManagerData} label="Managers" />
          <AvailabilityPill active={row.hasPerformanceData} label="Results" />
          <AvailabilityPill active={row.hasAchievementData} label="Achievements" />
          <AvailabilityPill active={row.financeExtracted} label="Finance extract" />
        </div>
      </div>

      <div className="spotlightGrid">
        <article className="miniCard">
          <span>Gross spend</span>
          <strong>{formatMoneyMillions(row.grossTransferSpendEur, "EUR")}</strong>
          <small>Income: {formatMoneyMillions(row.transferIncomeEur, "EUR")}</small>
        </article>

        <article className="miniCard">
          <span>Manager</span>
          <strong>{row.primaryManagerName ?? "Data pending"}</strong>
          <small>Manager layer is already wired into the master dataset.</small>
        </article>

        <article className="miniCard">
          <span>League points</span>
          <strong>{formatInteger(row.points)}</strong>
          <small>Finish: {formatInteger(row.leaguePosition)}</small>
        </article>

        <article className="miniCard">
          <span>Achievements</span>
          <strong>{formatInteger(row.achievementCountTotal)}</strong>
          <small>{row.achievementsInSeason ?? "No seasonal achievement string yet."}</small>
        </article>

        <article className="miniCard">
          <span>Reported turnover</span>
          <strong>{formatMoneyMillions(row.turnoverOriginal, "GBP")}</strong>
          <small>Shown here as source context, not yet as a shared compare metric.</small>
        </article>

        <article className="miniCard">
          <span>Wage-to-revenue ratio</span>
          <strong>{formatPercent(row.wageToRevenueRatio)}</strong>
          <small>Blocked until wage and EUR-normalized revenue layers are complete.</small>
        </article>
      </div>

      {row.financeSourceUrl ? (
        <a className="sourceLink" href={row.financeSourceUrl} target="_blank" rel="noreferrer">
          <Database size={14} />
          <span>{row.financeSourceDocument ?? "Finance source"}</span>
          <LinkIcon size={14} />
        </a>
      ) : null}
    </section>
  );
}
