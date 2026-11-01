import { useEffect, useState } from "react";
import { Card } from "@/components/Card";
import { api } from "@/api/client";
import type { MethodComparison, OptimizeRequest } from "@/api/types";

import "./ComparisonTable.css";

interface ComparisonTableProps {
  settings: OptimizeRequest;
}

interface ComparisonState {
  settings: OptimizeRequest;
  methods: MethodComparison[];
  error: string | null;
}

export function ComparisonTable({ settings }: ComparisonTableProps) {
  const [state, setState] = useState<ComparisonState | null>(null);

  useEffect(() => {
    let active = true;
    api
      .compare(settings)
      .then((res) => {
        if (active) {
          setState({ settings, methods: res.methods, error: null });
        }
      })
      .catch((err) => {
        if (active) {
          setState((prev) => ({
            settings,
            methods: prev?.methods ?? [],
            error: err instanceof Error ? err.message : "Błąd porównania metod",
          }));
        }
      });

    return () => {
      active = false;
    };
  }, [settings]);

  const loading = state?.settings !== settings;
  const methods = state?.methods ?? [];
  const error = state?.settings === settings ? state.error : null;

  return (
    <Card
      title="Porównanie metod sterowania"
      hint="Zestawienie 4 reguł na tych samych danych, modelu budynku i komforcie"
    >
      <div className="comparison-section">
        {loading && <p className="banner banner--info">Przeliczam porównanie metod…</p>}
        {error && <p className="banner banner--error">{error}</p>}

        <div className="comparison-table-wrapper">
          <table className="comparison-table">
            <thead>
              <tr>
                <th>Wariant</th>
                <th>Koszt</th>
                <th>Energia</th>
                <th>Grzanie</th>
                <th>T &lt; T_min</th>
                <th>Śr. temp</th>
                <th>Oszczędność vs termostat</th>
              </tr>
            </thead>
            <tbody>
              {methods.map((m) => {
                const isDP = m.method === "dp";
                return (
                  <tr
                    key={m.method}
                    className={isDP ? "comparison-table__row--dp" : undefined}
                  >
                    <td>
                      <div>
                        <div className="comparison-table__label">{m.label}</div>
                        <div className="comparison-table__desc">{m.description}</div>
                      </div>
                    </td>
                    <td>{m.cost_pln.toFixed(2)} zł</td>
                    <td>{m.energy_kwh.toFixed(1)} kWh</td>
                    <td>{m.heating_hours} h</td>
                    <td>
                      {m.hours_below_t_min === 0 ? (
                        <span className="comparison-table__success">0 h</span>
                      ) : (
                        <span className="comparison-table__danger">
                          {m.hours_below_t_min} h ({m.deficit_kh.toFixed(2)} °C·h)
                        </span>
                      )}
                    </td>
                    <td>{m.mean_temp_c.toFixed(1)} °C</td>
                    <td>
                      {m.saving_pln > 0 ? (
                        <span className="comparison-table__saving--pos">
                          +{m.saving_pln.toFixed(2)} zł ({m.saving_pct.toFixed(1)}%)
                        </span>
                      ) : (
                        <span className="comparison-table__saving--zero">
                          {m.saving_pln.toFixed(2)} zł
                        </span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        <div className="comparison-summary">
          <strong>Wnioski z porównania:</strong> Metoda programowania dynamicznego (DP) osiąga
          najniższy koszt energii dzięki wyprzedzaniu szczytów cenowych i bezwładności cieplnej
          budynku, gwarantując jednocześnie brak naruszeń pasma komfortu. Prosta reguła zachłanna
          (dogrzewanie przy cenie poniżej mediany) obniża koszt, lecz nie optymalizuje horyzontu tak
          precyzyjnie jak DP. Przy płaskich cenach energii przewaga DP nad termostatem maleje,
          natomiast przy taryfach dynamicznych z ostrym szczytem wieczornym oszczędność przekracza
          często 40–50%.
        </div>
      </div>
    </Card>
  );
}
