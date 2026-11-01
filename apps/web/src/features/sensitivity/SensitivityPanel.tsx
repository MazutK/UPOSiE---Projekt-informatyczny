import { useEffect, useState } from "react";
import { Card } from "@/components/Card";
import { api } from "@/api/client";
import type { OptimizeRequest, SensitivityRow } from "@/api/types";

import "./SensitivityPanel.css";

interface SensitivityPanelProps {
  settings: OptimizeRequest;
}

interface SensitivityState {
  settings: OptimizeRequest;
  parameter: "t_min" | "max_overshoot";
  rows: SensitivityRow[];
  error: string | null;
}

export function SensitivityPanel({ settings }: SensitivityPanelProps) {
  const [parameter, setParameter] = useState<"t_min" | "max_overshoot">("t_min");
  const [state, setState] = useState<SensitivityState | null>(null);

  useEffect(() => {
    let active = true;
    const values =
      parameter === "t_min" ? [20.0, 20.5, 21.0, 21.5, 22.0] : [0.0, 0.5, 1.0, 1.5, 2.0];

    api
      .sensitivity({
        ...settings,
        parameter,
        values,
      })
      .then((res) => {
        if (active) {
          setState({ settings, parameter, rows: res.rows, error: null });
        }
      })
      .catch((err) => {
        if (active) {
          setState((prev) => ({
            settings,
            parameter,
            rows: prev?.rows ?? [],
            error: err instanceof Error ? err.message : "Błąd analizy wrażliwości",
          }));
        }
      });

    return () => {
      active = false;
    };
  }, [settings, parameter]);

  const loading = state?.settings !== settings || state?.parameter !== parameter;
  const rows = state?.rows ?? [];
  const error = !loading ? (state?.error ?? null) : null;

  const handleExportCsv = () => {
    if (rows.length === 0) return;

    const headers = [
      `parametr_${parameter}`,
      "dp_koszt_pln",
      "termostat_koszt_pln",
      "oszczednosc_pln",
      "oszczednosc_proc",
      "dp_godziny_grzania",
      "termostat_godziny_grzania",
      "dp_ponizej_tmin",
      "termostat_ponizej_tmin",
      "dp_srednia_temp_c",
    ];

    const lines = [headers.join(",")];
    for (const r of rows) {
      lines.push(
        [
          r.value,
          r.dp_cost_pln.toFixed(4),
          r.thermostat_cost_pln.toFixed(4),
          r.saving_pln.toFixed(4),
          r.saving_pct.toFixed(2),
          r.dp_heating_hours,
          r.thermostat_heating_hours,
          r.dp_hours_below_t_min,
          r.thermostat_hours_below_t_min,
          r.dp_mean_temp_c.toFixed(2),
        ].join(",")
      );
    }

    const blob = new Blob([lines.join("\n")], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", `analiza_wrazliwosci_${parameter}_${settings.scenario}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const paramLabel =
    parameter === "t_min" ? "Dolna granica komfortu T_min (°C)" : "Dopuszczalne przegrzanie overshoot (°C)";

  return (
    <Card
      title="Analiza wrażliwości (Sensitivity Analysis)"
      hint="Wpływ zmiany parametrów komfortu na koszty i oszczędności"
    >
      <div className="sensitivity-section">
        <div className="sensitivity-controls">
          <label className="sensitivity-select-label">
            Badany parametr:
            <select
              className="sensitivity-select"
              value={parameter}
              onChange={(e) => setParameter(e.target.value as "t_min" | "max_overshoot")}
            >
              <option value="t_min">T_min (dolna granica komfortu)</option>
              <option value="max_overshoot">max_overshoot (dopuszczalne przegrzanie)</option>
            </select>
          </label>

          <button
            type="button"
            className="sensitivity-export-btn"
            disabled={rows.length === 0}
            onClick={handleExportCsv}
          >
            📊 Eksportuj tabelę do CSV
          </button>
        </div>

        {loading && <p className="banner banner--info">Przeliczam analizę wrażliwości…</p>}
        {error && <p className="banner banner--error">{error}</p>}

        <div className="sensitivity-table-wrapper">
          <table className="sensitivity-table">
            <thead>
              <tr>
                <th>{paramLabel}</th>
                <th>Koszt DP</th>
                <th>Koszt termostat</th>
                <th>Oszczędność (zł)</th>
                <th>Oszczędność (%)</th>
                <th>DP poniżej T_min</th>
                <th>Termostat poniżej T_min</th>
                <th>Śr. temp. DP</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => {
                const widthBar = Math.min(100, Math.max(5, r.saving_pct * 1.5));
                return (
                  <tr key={r.value}>
                    <td>
                      <strong>
                        {r.value.toFixed(1)} °C
                      </strong>
                    </td>
                    <td>{r.dp_cost_pln.toFixed(2)} zł</td>
                    <td>{r.thermostat_cost_pln.toFixed(2)} zł</td>
                    <td className="sensitivity-table__saving">
                      +{r.saving_pln.toFixed(2)} zł
                    </td>
                    <td>
                      <span className="sensitivity-bar" style={{ width: `${widthBar}px` }} />
                      <strong>{r.saving_pct.toFixed(1)}%</strong>
                    </td>
                    <td>
                      {r.dp_hours_below_t_min === 0 ? (
                        <span className="sensitivity-table__success">0 h</span>
                      ) : (
                        <span className="sensitivity-table__danger">{r.dp_hours_below_t_min} h</span>
                      )}
                    </td>
                    <td>{r.thermostat_hours_below_t_min} h</td>
                    <td>{r.dp_mean_temp_c.toFixed(1)} °C</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </Card>
  );
}
