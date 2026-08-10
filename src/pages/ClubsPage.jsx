import { ClubCard } from "../components/ClubCard";
import { getClubCardsData, getClubProfileCoverage } from "../lib/dataModel";
import { getMetric } from "../config/metricRegistry";

export function ClubsPage() {
  const cards = getClubCardsData().map((card) => ({
    ...card,
    coverage: getClubProfileCoverage(card.club.id).finance,
    metrics: [
      {
        label: "Revenue",
        value: card.revenue ? getMetric("revenue").formatValue(card.revenue.value) : "—",
        note: card.revenue ? `${card.revenue.season}` : "Coming soon",
      },
      {
        label: "Net transfer spend",
        value: card.netTransferSpend ? getMetric("netTransferSpend").formatValue(card.netTransferSpend.value) : "—",
        note: card.netTransferSpend ? `${card.netTransferSpend.season}` : "Coming soon",
      },
      {
        label: "Premier League position",
        value: card.leaguePosition ? getMetric("leaguePosition").formatValue(card.leaguePosition.value) : "—",
        note: card.leaguePosition ? `${card.leaguePosition.season}` : "Coming soon",
      },
    ],
  }));

  return (
    <>
      <section className="pageHero panel">
        <div>
          <span className="eyebrow">Clubs</span>
          <h1>Browse the Big Six club profiles</h1>
          <p>
            Each card uses the latest usable season for a few headline measures, then links into a
            deeper profile covering transfers, finance, performance, and season history.
          </p>
        </div>
      </section>

      <section className="clubsGrid">
        {cards.map((card) => (
          <ClubCard key={card.club.id} card={card} />
        ))}
      </section>
    </>
  );
}
