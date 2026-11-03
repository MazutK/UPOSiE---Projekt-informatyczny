import { useState } from "react";
import { Card } from "@/components/Card";
import { api } from "@/api/client";
import type { OptimizeRequest } from "@/api/types";

import "./LiveDateSelector.css";

interface LiveDateSelectorProps {
  settings: OptimizeRequest;
  onScenarioChange: (scenario: string) => void;
}

function todayLocal(): string {
  const now = new Date();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${now.getFullYear()}-${month}-${day}`;
}

export function LiveDateSelector({ settings, onScenarioChange }: LiveDateSelectorProps) {
  const [date, setDate] = useState(todayLocal);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [isError, setIsError] = useState(false);

  const handleFetch = async () => {
    setLoading(true);
    setMessage(null);
    setIsError(false);
    try {
      const resp = await api.live(date);
      setMessage(resp.message);
      setIsError(false);
      onScenarioChange(resp.scenario_name);
    } catch (err) {
      setIsError(true);
      setMessage(err instanceof Error ? err.message : "Błąd pobierania danych live");
    } finally {
      setLoading(false);
    }
  };

  const isDobaLive = settings.scenario === "doba_live";

  return (
    <Card
      title="Dane publiczne (PSE + Open-Meteo)"
      hint="Pobiera rzeczywiste ceny RCE z PSE oraz pogodę z Open-Meteo"
    >
      <div className="live-data">
        <div className="live-data__row">
          <input
            type="date"
            className="live-data__input"
            value={date}
            onChange={(e) => setDate(e.target.value)}
          />
          <button
            type="button"
            className="live-data__btn"
            disabled={loading}
            onClick={handleFetch}
          >
            {loading ? "Pobieram…" : "Pobierz dobę"}
          </button>
        </div>

        {message && (
          <p
            className={`live-data__status ${
              isError ? "live-data__status--error" : "live-data__status--info"
            }`}
          >
            {message}
          </p>
        )}

        {isDobaLive && !message && (
          <p className="live-data__status live-data__status--info">
            Aktywny scenariusz: <strong>doba_live</strong> (doba rzeczywista).
          </p>
        )}
      </div>
    </Card>
  );
}
