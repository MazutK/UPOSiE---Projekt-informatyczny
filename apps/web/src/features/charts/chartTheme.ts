export const axisStyle = {
  stroke: "var(--text-muted)",
  tick: { fill: "var(--text-muted)", fontSize: 12 },
} as const;

export const tooltipStyle = {
  contentStyle: {
    background: "var(--surface-raised)",
    border: "1px solid var(--border)",
    borderRadius: "8px",
    color: "var(--text)",
  },
  labelFormatter: (hour: number | string) => `Godzina ${hour}`,
} as const;
