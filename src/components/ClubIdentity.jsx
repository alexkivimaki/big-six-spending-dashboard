import { Link } from "react-router-dom";

export function ClubIdentity({ club, clickable = false, compact = false }) {
  const content = (
    <span className={`clubIdentity ${compact ? "isCompact" : ""}`}>
      <span
        className="clubAvatar"
        style={{ background: club.colors.secondary, color: club.colors.ink, borderColor: club.colors.primary }}
      >
        {club.initials}
      </span>
      <span className="clubIdentityText">
        <strong>{club.name}</strong>
        {compact ? null : <small>{club.shortName}</small>}
      </span>
    </span>
  );

  if (!clickable) return content;

  return (
    <Link className="clubIdentityLink" to={`/clubs/${club.slug}`}>
      {content}
    </Link>
  );
}
