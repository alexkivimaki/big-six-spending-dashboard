import { Link } from "react-router-dom";

import { ClubIdentity } from "./ClubIdentity";
import { CoverageBadge } from "./CoverageBadge";

export function ClubCard({ card }) {
  return (
    <article className="clubCard panel">
      <div className="clubCardTop">
        <ClubIdentity club={card.club} />
        <CoverageBadge coverage={card.coverage} quiet />
      </div>

      <div className="clubCardMetrics">
        {card.metrics.map((metric) => (
          <div key={metric.label} className="clubCardMetric">
            <span>{metric.label}</span>
            <strong>{metric.value}</strong>
            <small>{metric.note}</small>
          </div>
        ))}
      </div>

      <Link className="primaryLink" to={`/clubs/${card.club.slug}`}>
        View profile →
      </Link>
    </article>
  );
}
