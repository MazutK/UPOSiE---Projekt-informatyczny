import { useEffect, useState } from "react";

import { ApiError, api } from "@/api/client";
import type { OptimizeRequest, OptimizeResponse, Scenario } from "@/api/types";

export const DEFAULT_SETTINGS: OptimizeRequest = {
  scenario: "doba_zmienna_cena",
  t_min: 21.0,
  t_max: 22.5,
  t_start: 21.8,
};

function toMessage(error: unknown): string {
  if (error instanceof ApiError || error instanceof Error) return error.message;
  return "Nieznany błąd";
}

export function useScenarios() {
  const [state, setState] = useState<{ data: Scenario[]; error: string | null }>({
    data: [],
    error: null,
  });

  useEffect(() => {
    let active = true;
    api
      .scenarios()
      .then((data) => active && setState({ data, error: null }))
      .catch((e: unknown) => active && setState({ data: [], error: toMessage(e) }));
    return () => {
      active = false;
    };
  }, []);

  return state;
}

interface Loaded {
  settings: OptimizeRequest;
  result: OptimizeResponse | null;
  error: string | null;
}

export function useOptimization(settings: OptimizeRequest) {
  const [loaded, setLoaded] = useState<Loaded | null>(null);

  useEffect(() => {
    let active = true;
    api
      .optimize(settings)
      .then((result) => active && setLoaded({ settings, result, error: null }))
      .catch(
        (e: unknown) =>
          active &&
          setLoaded((previous) => ({
            settings,
            result: previous?.result ?? null,
            error: toMessage(e),
          })),
      );
    return () => {
      active = false;
    };
  }, [settings]);

  const current = loaded?.settings === settings;
  return {
    result: loaded?.result ?? null,
    error: current ? (loaded?.error ?? null) : null,
    loading: !current,
  };
}
