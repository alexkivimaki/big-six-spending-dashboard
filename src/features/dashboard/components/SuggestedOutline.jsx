export function SuggestedOutline({ cards }) {
  return (
    <section className="panel outlinePanel">
      <div className="sectionHeading">
        <div>
          <span className="eyebrow">Suggested outline</span>
          <h2>Recommended structure for the full dashboard</h2>
        </div>
        <p>
          This is the implementation order I would use after the demo: keep the core compare view
          stable, then progressively unlock richer finance and efficiency modules as the missing
          layers arrive.
        </p>
      </div>

      <div className="outlineGrid">
        {cards.map((card) => {
          const Icon = card.icon;
          return (
            <article key={card.title} className="outlineCard">
              <div className="outlineIcon">
                <Icon size={18} />
              </div>
              <h3>{card.title}</h3>
              <p>{card.body}</p>
            </article>
          );
        })}
      </div>
    </section>
  );
}
