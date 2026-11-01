import { useState } from "react";

import type { OptimizeRequest } from "@/api/types";
import { ControlsPanel } from "@/features/controls/ControlsPanel";
import { PriceScheduleChart } from "@/features/charts/PriceScheduleChart";
import { TemperatureChart } from "@/features/charts/TemperatureChart";
import { HourlyTable } from "@/features/summary/HourlyTable";
import { SummaryCards } from "@/features/summary/SummaryCards";
import { LiveDateSelector } from "@/features/live-data/LiveDateSelector";
import { OverridesGrid } from "@/features/overrides/OverridesGrid";
import { ExportPlanButton } from "@/features/export/ExportPlanButton";
import { ComparisonTable } from "@/features/comparison/ComparisonTable";
import { SensitivityPanel } from "@/features/sensitivity/SensitivityPanel";
import { DEFAULT_SETTINGS, useOptimization, useScenarios } from "@/hooks/useOptimization";

export default function App() {
  const [settings, setSettings] = useState<OptimizeRequest>(DEFAULT_SETTINGS);
  const scenarios = useScenarios();
  const { result, error, loading } = useOptimization(settings);

  return (
    <div className="app">
      <header className="app__header">
        <h1>Optymalizator ogrzewania</h1>
        <p>
          Najtańszy plan grzania przy zmiennych cenach energii, porównany z klasycznym
          termostatem oraz heurystykami.
        </p>
      </header>

      {(error ?? scenarios.error) && <p className="banner">{error ?? scenarios.error}</p>}

      <div className="app__layout">
        <aside style={{ display: "flex", flexDirection: "column", gap: "var(--space-6)" }}>
          <ControlsPanel
            settings={settings}
            scenarios={scenarios.data}
            disabled={loading}
            onChange={setSettings}
          />

          <LiveDateSelector
            settings={settings}
            onScenarioChange={(scenario) => setSettings((prev) => ({ ...prev, scenario }))}
          />

          <OverridesGrid
            settings={settings}
            disabled={loading}
            onChange={setSettings}
          />
        </aside>

        <main className="app__main">
          {result ? (
            <>
              <SummaryCards result={result} />
              <TemperatureChart result={result} />
              <PriceScheduleChart result={result} />
              <HourlyTable result={result} />
              <ExportPlanButton result={result} />
              <ComparisonTable settings={settings} />
              <SensitivityPanel settings={settings} />
            </>
          ) : (
            !error && <p className="banner banner--info">Liczę plan…</p>
          )}
        </main>
      </div>
    </div>
  );
}
