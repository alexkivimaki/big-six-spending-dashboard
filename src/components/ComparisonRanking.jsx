import { Link } from "react-router-dom";

import { clubConfigById } from "../config/clubConfig";
import { formatCount } from "../shared/formatters";

export function ComparisonRanking({ metric, ranking }) {
  if (ranking.status === "coming-soon") {
    return (
      <div className="emptyState compact">
        <h3>Coming soon</h3>
        <p>{ranking.note}</p>
      </div>
    );
  }

  if (ranking.status === "insufficient") {
    return (
      <div className="emptyState compact">
        <h3>No defensible ranking yet</h3>
        <p>{ranking.note}</p>
      </div>
    );
  }

  return (
    <div className="rankingBlock">
      {ranking.note ? <p className="rankingNote">{ranking.note}</p> : null}
      <div className="tableWrap">
        <table>
          <thead>
            <tr>
              <th>Club</th>
              <th>{metric.shortLabel}</th>
              <th>Seasons used</th>
            </tr>
          </thead>
          <tbody>
            {ranking.rows.map((row) => {
              const club = clubConfigById[row.clubId];
              return (
                <tr key={row.clubId}>
                  <td>
                    <Link className="tableClubLink" to={`/clubs/${club.slug}`}>
                      <span className="clubToggleSwatch" style={{ background: club.colors.primary }} />
                      <strong>{club.name}</strong>
                    </Link>
                  </td>
                  <td>{metric.formatValue(row.value)}</td>
                  <td>{formatCount(row.seasonsUsed.length)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
