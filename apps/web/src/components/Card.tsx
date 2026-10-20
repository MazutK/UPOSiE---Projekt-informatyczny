import type { ReactNode } from "react";

import "./Card.css";

interface CardProps {
  title: string;
  hint?: string;
  actions?: ReactNode;
  children: ReactNode;
}

export function Card({ title, hint, actions, children }: CardProps) {
  return (
    <section className="card">
      <header className="card__header">
        <div>
          <h2 className="card__title">{title}</h2>
          {hint && <p className="card__hint">{hint}</p>}
        </div>
        {actions}
      </header>
      <div className="card__body">{children}</div>
    </section>
  );
}
