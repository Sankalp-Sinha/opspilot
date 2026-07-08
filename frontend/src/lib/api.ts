import type {
  Incident,
  IncidentCreatePayload,
  Workspace,
  WorkspaceCreatePayload,
} from "@/types";


const API_URL =
  process.env.NEXT_PUBLIC_API_URL ??
  "http://127.0.0.1:8000";


async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const headers = new Headers(options.headers);

  if (options.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(
    `${API_URL}${path}`,
    {
      ...options,
      headers,
    }
  );

  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;

    try {
      const body = await response.json();

      if (body.detail) {
        message = body.detail;
      }
    } catch {
      // Response was not JSON.
    }

    throw new Error(message);
  }

  return response.json() as Promise<T>;
}


export function getWorkspaces(): Promise<Workspace[]> {
  return request<Workspace[]>(
    "/api/v1/workspaces"
  );
}


export function createWorkspace(
  payload: WorkspaceCreatePayload
): Promise<Workspace> {
  return request<Workspace>(
    "/api/v1/workspaces",
    {
      method: "POST",
      body: JSON.stringify(payload),
    }
  );
}


export function getIncidents(): Promise<Incident[]> {
  return request<Incident[]>(
    "/api/v1/incidents"
  );
}


export function createIncident(
  payload: IncidentCreatePayload
): Promise<Incident> {
  return request<Incident>(
    "/api/v1/incidents",
    {
      method: "POST",
      body: JSON.stringify(payload),
    }
  );
}