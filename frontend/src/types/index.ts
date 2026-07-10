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

export interface ToolInvestigationRequest {
  question: string;
}


export interface ToolExecution {
  name: string;

  arguments: Record<string, unknown>;

  result: Record<string, unknown>;
}


export interface ToolInvestigation {
  incident_id: string;

  question: string;

  tool_called: boolean;

  tool_execution: ToolExecution | null;

  final_answer: string;

  model_name: string;
}

export type AgentStopReason =
  | "model_finished"
  | "tool_budget_exhausted";


export interface AgentToolStep {
  iteration: number;

  tool_name: string;

  arguments: Record<
    string,
    unknown
  >;

  result: Record<
    string,
    unknown
  >;
}


export interface AgentInvestigationRequest {
  goal: string;
}


export interface AgentInvestigation {
  run_id: string;

  incident_id: string;

  goal: string;

  status: "completed";

  steps: AgentToolStep[];

  tool_calls_count: number;

  final_answer: string;

  stop_reason: AgentStopReason;

  model_name: string;
}


export interface AgentRunStats {
  total: number;

  queued: number;

  running: number;

  completed: number;

  failed: number;
}

export interface LangChainAgentInvestigation {
  incident_id: string;
  goal: string;

  steps: AgentToolStep[];

  tool_calls_count: number;
  model_calls_count: number;

  final_answer: string;
  model_name: string;

  harness: "langchain_create_agent";
}


export interface LangGraphAgentInvestigation {
  incident_id: string;
  goal: string;

  steps: AgentToolStep[];

  tool_calls_count: number;
  model_calls_count: number;

  node_trace: string[];

  final_answer: string;

  stop_reason:
    | "model_finished"
    | "tool_budget_exhausted";

  model_name: string;

  harness: "langgraph_state_graph";
}