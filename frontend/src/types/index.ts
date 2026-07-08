export interface Workspace {
  id: string;
  name: string;
  slug: string;
  created_at: string;
}


export interface WorkspaceCreatePayload {
  name: string;
  slug: string;
}


export interface Incident {
  id: string;
  workspace_id: string;
  title: string;
  description: string;
  service_name: string | null;
  status: string;
  created_at: string;
}


export interface IncidentCreatePayload {
  workspace_id: string;
  title: string;
  description: string;
  service_name?: string | null;
}


export type Severity =
  | "low"
  | "medium"
  | "high"
  | "critical";


export type IncidentCategory =
  | "application"
  | "database"
  | "network"
  | "deployment"
  | "dependency"
  | "security"
  | "capacity"
  | "unknown";


export interface IncidentAnalysis {
  id: string;
  incident_id: string;

  severity: Severity;
  category: IncidentCategory;

  affected_service: string;

  likely_impact: string;
  recommended_next_step: string;
  analysis_summary: string;

  confidence: number;

  model_name: string;
  prompt_version: string;

  created_at: string;
}