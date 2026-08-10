import { X } from "lucide-react";

export function SourceDrawer({ open, onClose, title, subtitle, sections }) {
  if (!open) return null;

  return (
    <div className="sourceDrawerOverlay" role="presentation" onClick={onClose}>
      <aside className="sourceDrawer" role="dialog" aria-modal="true" onClick={(event) => event.stopPropagation()}>
        <header className="sourceDrawerHeader">
          <div>
            <span className="eyebrow">Source and data info</span>
            <h2>{title}</h2>
            {subtitle ? <p>{subtitle}</p> : null}
          </div>
          <button type="button" className="iconButton" onClick={onClose} aria-label="Close source panel">
            <X size={18} />
          </button>
        </header>

        <div className="sourceDrawerBody">
          {sections.map((section) => (
            <section key={section.title} className="sourceBlock">
              <h3>{section.title}</h3>
              <dl>
                {section.fields.map((field) => (
                  <div key={`${section.title}-${field.label}`} className="sourceField">
                    <dt>{field.label}</dt>
                    <dd>
                      {field.href ? (
                        <a href={field.href} target="_blank" rel="noreferrer">
                          {field.value}
                        </a>
                      ) : (
                        field.value
                      )}
                    </dd>
                  </div>
                ))}
              </dl>
            </section>
          ))}
        </div>
      </aside>
    </div>
  );
}
