import { Card } from "@/components/Card";
import { NumberField, SelectField } from "@/components/Field";
import type { OptimizeRequest, Scenario } from "@/api/types";

import "./ControlsPanel.css";

interface ControlsPanelProps {
  settings: OptimizeRequest;
  scenarios: Scenario[];
  disabled: boolean;
  onChange: (settings: OptimizeRequest) => void;
}

export function ControlsPanel({ settings, scenarios, disabled, onChange }: ControlsPanelProps) {
  const patch = (changes: Partial<OptimizeRequest>) => onChange({ ...settings, ...changes });

  return (
    <Card title="Parametry" hint="Zmiana dowolnego pola przelicza plan od nowa.">
      <div className="controls" aria-busy={disabled}>
        <SelectField
          label="Scenariusz doby"
          value={settings.scenario}
          options={scenarios.map((scenario) => ({
            value: scenario.name,
            label: `${scenario.name} - ${scenario.description}`,
          }))}
          onChange={(scenario) => patch({ scenario })}
        />
        <NumberField
          label="Dolna granica komfortu"
          unit="°C"
          min={16}
          max={24}
          step={0.5}
          value={settings.t_min}
          onChange={(t_min) => patch({ t_min, t_max: Math.max(t_min, settings.t_max) })}
        />
        <NumberField
          label="Górna granica komfortu"
          unit="°C"
          min={16}
          max={26}
          step={0.5}
          value={settings.t_max}
          onChange={(t_max) => patch({ t_max, t_min: Math.min(t_max, settings.t_min) })}
        />
        <NumberField
          label="Temperatura początkowa"
          unit="°C"
          min={15}
          max={26}
          step={0.1}
          value={settings.t_start}
          onChange={(t_start) => patch({ t_start })}
        />
      </div>
    </Card>
  );
}
