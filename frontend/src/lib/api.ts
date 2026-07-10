import type {
  AgentInvestigation,
  AgentInvestigationRequest,
  AgentRunStats,
  Incident,
  IncidentAnalysis,
  IncidentCreatePayload,
  ToolInvestigation,
  ToolInvestigationRequest,
  Workspace,
  WorkspaceCreatePayload,
  LangChainAgentInvestigation,
  LangGraphAgentInvestigation,
} from "@/types";


const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ??
  "http://127.0.0.1:8000";


async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const headers = new Headers(options.headers);

  if (
    options.body &&
    !headers.has("Content-Type")
  ) {
    headers.set(
      "Content-Type",
      "application/json"
    );
  }

  const response = await fetch(
    `${API_BASE_URL}${path}`,
    {
      ...options,
      headers,
    }
  );

  if (!response.ok) {
    let message =
      `Request failed with status ${response.status}`;

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


export function analyzeIncident(
  incidentId: string
): Promise<IncidentAnalysis> {
  return request<IncidentAnalysis>(
    `/api/v1/incidents/${incidentId}/analyze`,
    {
      method: "POST",
    }
  );
}


export function getIncidentAnalyses(
  incidentId: string
): Promise<IncidentAnalysis[]> {
  return request<IncidentAnalysis[]>(
    `/api/v1/incidents/${incidentId}/analyses`
  );
}

export function investigateIncidentWithTool(
  incidentId: string,
  payload: ToolInvestigationRequest
): Promise<ToolInvestigation> {
  return request<ToolInvestigation>(
    `/api/v1/incidents/${incidentId}/tool-investigate`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    }
  );
}


export function investigateIncidentWithAgent(
  incidentId: string,
  payload: AgentInvestigationRequest
): Promise<AgentInvestigation> {
  return request<AgentInvestigation>(
    `/api/v1/incidents/${incidentId}/agent-investigate`,
    {
      method: "POST",

      body: JSON.stringify(
        payload
      ),
    }
  );
}


export function getAgentRunStats():
  Promise<AgentRunStats> {
  return request<AgentRunStats>(
    "/api/v1/agent-runs/stats"
  );
}

export async function investigateIncidentWithLangChainAgent(
  incidentId: string,
  payload: AgentInvestigationRequest,
): Promise<LangChainAgentInvestigation> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/incidents/${incidentId}/langchain-agent-investigate`,
    {
      method: "POST",

      headers: {
        "Content-Type": "application/json",
      },

      body: JSON.stringify(payload),
    },
  );


  if (!response.ok) {
    const errorBody = await response
      .json()
      .catch(() => null);

    throw new Error(
      errorBody?.detail ??
        "LangChain agent investigation failed",
    );
  }


  return response.json();
}


export async function investigateIncidentWithLangGraphAgent(
  incidentId: string,
  payload: AgentInvestigationRequest,
): Promise<LangGraphAgentInvestigation> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/incidents/${incidentId}/langgraph-agent-investigate`,
    {
      method: "POST",

      headers: {
        "Content-Type": "application/json",
      },

      body: JSON.stringify(payload),
    },
  );


  if (!response.ok) {
    const errorBody = await response
      .json()
      .catch(() => null);

    throw new Error(
      errorBody?.detail ??
        "LangGraph agent investigation failed",
    );
  }


  return response.json();
}