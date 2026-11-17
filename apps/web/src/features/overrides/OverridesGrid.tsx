import { Card } from "@/components/Card";
import type { OptimizeRequest } from "@/api/types";

import "./OverridesGrid.css";

interface OverridesGridProps {
  settings: OptimizeRequest;
  disabled: boolean;
  onChange: (settings: OptimizeRequest) => void;
}

export function OverridesGrid({ settings, disabled, onChange }: OverridesGridProps) {
  const overrides = settings.overrides ?? {};

  const toggleHour = (hour: number) => {
    const current = overrides[hour];
    const nextOverrides = { ...overrides };

    if (current === undefined) {
      nextOverrides[hour] = 1; // Wymuś grzanie
    } else if (current === 1) {
      nextOverrides[hour] = 0; // Wymuś wyłączenie
    } else {
      delete nextOverrides[hour]; // Powrót do Auto
    }

    onChange({ ...settings, overrides: nextOverrides });
  };

  const clearAll = () => {
    onChange({ ...settings, overrides: {} });
  };

  const count = Object.keys(overrides).length;

  return (
    <Card
      title="Wymuszenia godzin (Overrides)"
      hint="Ręczne narzucenie decyzji: Auto → Wymuś ON (1) → Wymuś OFF (0)"
    >
      <div className="overrides-grid" aria-busy={disabled}>
        <p className="overrides-grid__description">
          Kliknij wybraną godzinę, aby wymusić grzanie (np. przed wyjściem do pracy) lub wyłączyć piec.
        </p>

        <div className="overrides-grid__matrix">
          {Array.from({ length: 24 }).map((_, hour) => {
            const state = overrides[hour];
            const stateClass =
              state === 1
                ? "overrides-cell--heat"
                : state === 0
                ? "overrides-cell--off"
                : "overrides-cell--auto";

            const label = state === 1 ? "ON" : state === 0 ? "OFF" : "Auto";

            return (
              <button
                key={hour}
                type="button"
                className={`overrides-cell ${stateClass}`}
                onClick={() => toggleHour(hour)}
                title={`Godzina ${hour}:00 - kliknij aby zmienić stan`}
              >
                <span className="overrides-cell__hour">{hour}:00</span>
                <span className="overrides-cell__badge">{label}</span>
              </button>
            );
          })}
        </div>

        <div className="overrides-grid__footer">
          <span className="overrides-grid__count">
            Aktywne wymuszenia: <strong>{count}</strong>
          </span>
          {count > 0 && (
            <button type="button" className="overrides-grid__reset" onClick={clearAll}>
              Wyczyść wymuszenia
            </button>
          )}
        </div>

        {count > 0 && (
          <p className="overrides-grid__notice" role="note">
            Wymuszenia dotyczą tylko planu optymalizatora. Termostat (baza porównania) ich nie
            uwzględnia, więc oszczędność jest liczona przy różnych warunkach dla obu planów.
          </p>
        )}
      </div>
    </Card>
  );
}
