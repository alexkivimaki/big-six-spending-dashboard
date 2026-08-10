import { Info } from "lucide-react";

import { CoverageBadge } from "./CoverageBadge";

export function SectionHeader({
  title,
  description,
  coverage,
  sourceAction,
  eyebrow = null,
}) {
  return (
    <div className="sectionHeader">
      <div>
        {eyebrow ? <span className="eyebrow">{eyebrow}</span> : null}
        <h2>{title}</h2>
        {description ? <p>{description}</p> : null}
      </div>

      <div className="sectionHeaderMeta">
        {coverage ? <CoverageBadge coverage={coverage} /> : null}
        {sourceAction ? (
          <button type="button" className="secondaryButton" onClick={sourceAction}>
            <Info size={15} />
            Source
          </button>
        ) : null}
      </div>
    </div>
  );
}
