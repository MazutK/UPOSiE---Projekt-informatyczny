import { Card } from "@/components/Card";
import type { OptimizeResponse } from "@/api/types";

import "./HourlyTable.css";

const HEADERS = ["godz.", "cena", "T_zew", "opt.", "T_wew opt.", "term.", "T_wew term."];

export function HourlyTable({ result }: { result: OptimizeResponse }) {
  return (
    <Card title="Plan godzina po godzinie" hint="1 oznacza włączoną grzałkę w danej godzinie.">
      <div className="hourly">
        <table className="hourly__table">
          <thead>
            <tr>
              {HEADERS.map((header) => (
                <th key={header}>{header}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {result.rows.map((row) => (
              <tr key={row.hour} className={row.optimal_temp_c < result.t_min ? "is-cold" : ""}>
                <td>{row.hour}</td>
                <td>{row.price_pln_kwh.toFixed(2)}</td>
                <td>{row.outside_temp_c.toFixed(1)}</td>
                <td className={row.optimal_state ? "is-on-optimal" : ""}>{row.optimal_state}</td>
                <td>{row.optimal_temp_c.toFixed(2)}</td>
                <td className={row.thermostat_state ? "is-on-thermostat" : ""}>
                  {row.thermostat_state}
                </td>
                <td>{row.thermostat_temp_c.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}
