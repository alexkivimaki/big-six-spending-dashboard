import { clubConfigById } from "../config/clubConfig";

function CannonGlyph({ fill, stroke }) {
  return (
    <g>
      <circle cx="6.5" cy="17.5" r="2.7" fill={fill} stroke={stroke} strokeWidth="1.2" />
      <path
        d="M4.2 14.8h8.7c1.6 0 3.2-.8 4.1-2.1l2.8-4.1h-6.1l-1.8 2.8H4.2z"
        fill={fill}
        stroke={stroke}
        strokeWidth="1.2"
        strokeLinejoin="round"
      />
      <rect x="8.2" y="11.7" width="5.5" height="1.8" rx="0.9" fill={fill} />
      <path d="M18.2 7.2h3.4" stroke={stroke} strokeWidth="1.3" strokeLinecap="round" />
      <path d="M5 14.8v2.2" stroke={stroke} strokeWidth="1.2" strokeLinecap="round" />
    </g>
  );
}

function CircleGlyph({ fill, stroke }) {
  return <circle cx="12" cy="12" r="5.25" fill={fill} stroke={stroke} strokeWidth="2" />;
}

export function ClubMarkerSvg({ club, size = 18 }) {
  const marker = club.visuals.marker;
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden="true" focusable="false">
      {marker.kind === "cannon" ? (
        <CannonGlyph fill={marker.fill} stroke={marker.stroke} />
      ) : (
        <CircleGlyph fill={marker.fill} stroke={marker.stroke} />
      )}
    </svg>
  );
}

export function ClubMarker({ club, size = 18, className = "" }) {
  return (
    <span
      className={`clubMarker ${className}`.trim()}
      style={{ width: size, height: size }}
      aria-hidden="true"
    >
      <ClubMarkerSvg club={club} size={size} />
    </span>
  );
}

export function ClubMarkerById({ clubId, size = 18, className = "" }) {
  const club = clubConfigById[clubId];
  return club ? <ClubMarker club={club} size={size} className={className} /> : null;
}
