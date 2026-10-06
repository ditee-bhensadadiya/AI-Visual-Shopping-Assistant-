import { useEffect, useState } from "react";
import { getHealth, type HealthResponse } from "../services/api";

type HealthState =
  | { state: "loading" }
  | { state: "connected"; health: HealthResponse }
  | { state: "disconnected"; message: string };

export function useHealth(): HealthState {
  const [health, setHealth] = useState<HealthState>({ state: "loading" });

  useEffect(() => {
    const controller = new AbortController();
    getHealth(controller.signal).then(
      (result) => setHealth({ state: "connected", health: result }),
      (error: unknown) => {
        if (!controller.signal.aborted) {
          setHealth({
            state: "disconnected",
            message: error instanceof Error ? error.message : "Could not reach the API",
          });
        }
      },
    );
    return () => controller.abort();
  }, []);

  return health;
}

