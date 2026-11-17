import type { OptimizeResponse } from "@/api/types";
import "./ExportPlanButton.css";

interface ExportPlanButtonProps {
  result: OptimizeResponse | null;
}

function todayIso(): string {
  const now = new Date();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${now.getFullYear()}-${month}-${day}`;
}

/** Z-10: nazwa pliku niesie scenariusz, pasmo komfortu, temperaturę startową i datę eksportu. */
export function exportFileName(result: OptimizeResponse, exportedOn: string = todayIso()): string {
  const scenario = result.scenario.replace(/[^\w-]+/g, "_");
  return (
    `plan_grzania_${scenario}` +
    `_tmin${result.t_min.toFixed(1)}_tmax${result.t_max.toFixed(1)}_tstart${result.t_start.toFixed(1)}` +
    `_${exportedOn}.csv`
  );
}

export function ExportPlanButton({ result }: ExportPlanButtonProps) {
  const handleExport = () => {
    if (!result) return;

    const headers = [
      "hour",
      "price_pln_kwh",
      "outside_temp_c",
      "solar_radiation_wm2",
      "optimal_state",
      "optimal_temp_c",
      "optimal_cost_pln",
      "thermostat_state",
      "thermostat_temp_c",
      "thermostat_cost_pln",
    ];

    const lines = [headers.join(",")];
    for (const row of result.rows) {
      lines.push(
        [
          row.hour,
          row.price_pln_kwh.toFixed(4),
          row.outside_temp_c.toFixed(2),
          row.solar_radiation_wm2.toFixed(1),
          row.optimal_state,
          row.optimal_temp_c.toFixed(2),
          row.optimal_cost_pln.toFixed(4),
          row.thermostat_state,
          row.thermostat_temp_c.toFixed(2),
          row.thermostat_cost_pln.toFixed(4),
        ].join(",")
      );
    }

    const blob = new Blob([lines.join("\n")], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", exportFileName(result));
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="export-plan">
      <button
        type="button"
        className="export-plan__btn"
        disabled={!result}
        onClick={handleExport}
      >
        📥 Pobierz plan godzinowy (CSV)
      </button>
      <span className="export-plan__hint">
        Eksportuje 24-godzinny plan z temperaturami i decyzjami obu metod. Nazwa pliku zawiera
        scenariusz, T_min, T_max, T_start i datę eksportu.
      </span>
    </div>
  );
}
