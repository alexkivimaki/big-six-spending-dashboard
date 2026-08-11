import { Link } from "react-router-dom";

import { ClubMarker } from "./ClubMarker";

export function ClubIdentity({ club, clickable = false, compact = false }) {
  const content = (
    <span className={`clubIdentity ${compact ? "isCompact" : ""}`}>
      <span
        className="clubAvatar"
        style={{
          background: club.visuals.identity.background,
          color: club.colors.ink,
          borderColor: club.visuals.identity.border,
        }}
      >
        <ClubMarker club={club} size={compact ? 18 : 24} />
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
