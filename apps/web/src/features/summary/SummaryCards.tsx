import type { OptimizeResponse } from "@/api/types";

import "./SummaryCards.css";

interface Metric {
  label: string;
  optimal: string;
  thermostat: string;
}

function metrics(result: OptimizeResponse): Metric[] {
  const { optimal, thermostat } = result;
  return [
    {
      label: "Koszt energii",
      optimal: `${optimal.cost_pln.toFixed(2)} zł`,
      thermostat: `${thermostat.cost_pln.toFixed(2)} zł`,
    },
    {
      label: "Zużyta energia",
      optimal: `${optimal.energy_kwh.toFixed(1)} kWh`,
      thermostat: `${thermostat.energy_kwh.toFixed(1)} kWh`,
    },
    {
      label: "Godziny grzania",
      optimal: `${optimal.heating_hours}`,
      thermostat: `${thermostat.heating_hours}`,
    },
    {
      label: "Godziny poniżej T_min",
      optimal: `${optimal.hours_below_t_min}`,
      thermostat: `${thermostat.hours_below_t_min}`,
    },
  ];
}

export function SummaryCards({ result }: { result: OptimizeResponse }) {
  const saved = result.saving_pln > 0;

  return (
    <div className="summary">
      <div className={`summary__headline ${saved ? "is-good" : "is-bad"}`}>
        <span className="summary__headline-label">Oszczędność wobec termostatu</span>
        <strong className="summary__headline-value">
          {result.saving_pln.toFixed(2)} zł
          <span className="summary__headline-pct"> ({result.saving_pct.toFixed(1)}%)</span>
        </strong>
        <span className="summary__headline-note">
          {result.scenario} · horyzont {result.hours} h
        </span>
      </div>

      <div className="summary__grid">
        {metrics(result).map((metric) => (
          <div key={metric.label} className="summary__metric">
            <span className="summary__metric-label">{metric.label}</span>
            <span className="summary__metric-optimal">{metric.optimal}</span>
            <span className="summary__metric-thermostat">termostat: {metric.thermostat}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
