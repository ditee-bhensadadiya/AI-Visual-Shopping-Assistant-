export interface HealthResponse {
  status: "ok";
  service: string;
  version: string;
}

export async function getHealth(signal?: AbortSignal): Promise<HealthResponse> {
  const response = await fetch("/api/health", {
    method: "GET",
    headers: { Accept: "application/json" },
    signal,
  });

  if (!response.ok) {
    throw new Error(`Backend request failed (${response.status})`);
  }

  return (await response.json()) as HealthResponse;
}

