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