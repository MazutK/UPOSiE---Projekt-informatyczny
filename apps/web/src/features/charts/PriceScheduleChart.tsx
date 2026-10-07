import {
  Bar,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { Card } from "@/components/Card";
import type { OptimizeResponse } from "@/api/types";

import { axisStyle, tooltipStyle } from "./chartTheme";

export function PriceScheduleChart({ result }: { result: OptimizeResponse }) {
  return (
    <Card
      title="Cena energii i godziny grzania"
      hint="Słupki pokazują, w których godzinach każdy sposób sterowania włącza grzałkę."
    >
      <ResponsiveContainer width="100%" height={260}>
        <ComposedChart data={result.rows} margin={{ top: 8, right: 8, bottom: 0, left: -16 }}>
          <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" />
          <XAxis dataKey="hour" unit=" h" {...axisStyle} />
          <YAxis yAxisId="state" domain={[0, 1]} hide />
          <YAxis yAxisId="price" unit=" zł" {...axisStyle} />
          <Tooltip {...tooltipStyle} />
          <Legend />
          <Bar
            yAxisId="state"
            dataKey="optimal_state"
            name="Grzanie - optymalizator"
            fill="var(--optimal)"
            fillOpacity={0.55}
          />
          <Bar
            yAxisId="state"
            dataKey="thermostat_state"
            name="Grzanie - termostat"
            fill="var(--thermostat)"
            fillOpacity={0.45}
          />
          <Line
            yAxisId="price"
            type="stepAfter"
            dataKey="price_pln_kwh"
            name="Cena [zł/kWh]"
            stroke="var(--price)"
            strokeWidth={2}
            dot={false}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </Card>
  );
}
