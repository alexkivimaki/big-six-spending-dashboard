import { CheckCircle2, Lock, TriangleAlert } from "lucide-react";

function StatusIcon({ status }) {
  if (status === "ready") return <CheckCircle2 size={16} />;
  if (status === "partial") return <TriangleAlert size={16} />;
  return <Lock size={16} />;
}

export function FeatureMatrix({ cards }) {
  return (
    <section className="featureSection panel">
      <div className="sectionHeading">
        <div>
          <span className="eyebrow">Build status</span>
          <h2>What this first demo can already show</h2>
        </div>
        <p>
          This is the dashboard backbone. We keep unfinished modules in view, but we only turn on
          the pieces backed by real coverage.
        </p>
      </div>

      <div className="featureGrid">
        {cards.map((card) => {
          const Icon = card.icon;
          return (
            <article key={card.key} className={`featureCard status-${card.status}`}>
              <div className="featureHeader">
                <div className="featureIcon">
                  <Icon size={18} />
                </div>
                <span className={`statusPill status-${card.status}`}>
                  <StatusIcon status={card.status} />
                  {card.status}
                </span>
              </div>
              <h3>{card.title}</h3>
              <p>{card.description}</p>
              <strong>{card.coverage}</strong>
            </article>
          );
        })}
      </div>
    </section>
  );
}
