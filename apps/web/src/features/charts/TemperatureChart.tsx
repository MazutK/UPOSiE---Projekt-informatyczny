import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ReferenceArea,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { Card } from "@/components/Card";
import type { OptimizeResponse } from "@/api/types";

import { axisStyle, tooltipStyle } from "./chartTheme";

function insideTemperatures(result: OptimizeResponse): number[] {
  return result.rows.flatMap((row) => [row.optimal_temp_c, row.thermostat_temp_c]);
}

function insideMin(result: OptimizeResponse): number {
  return Math.min(result.t_min, ...insideTemperatures(result));
}

function insideMax(result: OptimizeResponse): number {
  return Math.max(result.t_max, ...insideTemperatures(result));
}

export function TemperatureChart({ result }: { result: OptimizeResponse }) {
  return (
    <Card
      title="Temperatura wewnętrzna"
      hint="Zacieniony obszar to pasmo komfortu zadane w panelu parametrów."
    >
      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={result.rows} margin={{ top: 8, right: 8, bottom: 0, left: -16 }}>
          <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" />
          <ReferenceArea
            yAxisId="inside"
            y1={result.t_min}
            y2={result.t_max}
            fill="var(--good)"
            fillOpacity={0.1}
          />
          <XAxis dataKey="hour" unit=" h" {...axisStyle} />
          <YAxis
            yAxisId="inside"
            domain={[insideMin(result) - 0.4, insideMax(result) + 0.4]}
            tickFormatter={(value: number) => value.toFixed(1)}
            unit=" °C"
            {...axisStyle}
          />
          <YAxis yAxisId="outside" orientation="right" unit=" °C" {...axisStyle} />
          <Tooltip {...tooltipStyle} />
          <Legend />
          <Line
            yAxisId="inside"
            type="monotone"
            dataKey="optimal_temp_c"
            name="Optymalizator"
            stroke="var(--optimal)"
            strokeWidth={2}
            dot={false}
          />
          <Line
            yAxisId="inside"
            type="monotone"
            dataKey="thermostat_temp_c"
            name="Termostat"
            stroke="var(--thermostat)"
            strokeWidth={2}
            strokeDasharray="4 3"
            dot={false}
          />
          <Line
            yAxisId="outside"
            type="monotone"
            dataKey="outside_temp_c"
            name="Na zewnątrz (oś prawa)"
            stroke="var(--outside)"
            strokeWidth={1}
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </Card>
  );
}
