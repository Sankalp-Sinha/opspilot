"use client";

import {
  FormEvent,
  useEffect,
  useState,
} from "react";

import AgentInvestigationPanel from "@/components/agent-investigation-panel";

import IncidentAnalysisPanel from "@/components/incident-analysis-panel";

import ToolInvestigationPanel from "@/components/tool-investigation-panel";

import {
  analyzeIncident,
  createIncident,
  createWorkspace,
  getAgentRunStats,
  getIncidentAnalyses,
  getIncidents,
  getWorkspaces,
  investigateIncidentWithAgent,
  investigateIncidentWithTool,
} from "@/lib/api";

import type {
  AgentInvestigation,
  AgentRunStats,
  Incident,
  IncidentAnalysis,
  ToolInvestigation,
  Workspace,
} from "@/types";


type LatestAnalyses = Record<
  string,
  IncidentAnalysis | null
>;


type InvestigationQuestions = Record<
  string,
  string
>;


type ToolInvestigations = Record<
  string,
  ToolInvestigation | null
>;

type AgentGoals = Record<
  string,
  string
>;


type AgentInvestigations = Record<
  string,
  AgentInvestigation | null
>;


export default function Home() {
  const [
    workspaces,
    setWorkspaces,
  ] = useState<Workspace[]>([]);

  const [
    incidents,
    setIncidents,
  ] = useState<Incident[]>([]);


  const [
    latestAnalyses,
    setLatestAnalyses,
  ] = useState<LatestAnalyses>({});


  const [
    investigationQuestions,
    setInvestigationQuestions,
  ] = useState<InvestigationQuestions>({});


  const [
    toolInvestigations,
    setToolInvestigations,
  ] = useState<ToolInvestigations>({});

  const [
    agentGoals,
    setAgentGoals,
  ] = useState<AgentGoals>({});


  const [
    agentInvestigations,
    setAgentInvestigations,
  ] = useState<AgentInvestigations>({});


  const [
    runningAgentIncidentId,
    setRunningAgentIncidentId,
  ] = useState<string | null>(null);


  const [
    agentRunStats,
    setAgentRunStats,
  ] = useState<AgentRunStats>({
    total: 0,
    queued: 0,
    running: 0,
    completed: 0,
    failed: 0,
  });


  const [
    workspaceName,
    setWorkspaceName,
  ] = useState("");

  const [
    workspaceSlug,
    setWorkspaceSlug,
  ] = useState("");


  const [
    selectedWorkspaceId,
    setSelectedWorkspaceId,
  ] = useState("");


  const [
    incidentTitle,
    setIncidentTitle,
  ] = useState("");

  const [
    incidentDescription,
    setIncidentDescription,
  ] = useState("");

  const [
    serviceName,
    setServiceName,
  ] = useState("");


  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    submitting,
    setSubmitting,
  ] = useState(false);


  const [
    analyzingIncidentId,
    setAnalyzingIncidentId,
  ] = useState<string | null>(null);


  const [
    investigatingIncidentId,
    setInvestigatingIncidentId,
  ] = useState<string | null>(null);


  const [
    message,
    setMessage,
  ] = useState("");

  const [
    error,
    setError,
  ] = useState("");


  async function loadLatestAnalyses(
    incidentData: Incident[]
  ) {
    const entries = await Promise.all(
      incidentData.map(async (incident) => {
        try {
          const analyses =
            await getIncidentAnalyses(
              incident.id
            );

          return [
            incident.id,
            analyses[0] ?? null,
          ] as const;
        } catch {
          return [
            incident.id,
            null,
          ] as const;
        }
      })
    );

    setLatestAnalyses(
      Object.fromEntries(entries)
    );
  }

  async function refreshAgentRunStats() {
    try {
      const stats =
        await getAgentRunStats();

      setAgentRunStats(
        stats
      );
    } catch {
      // Agent stats should not prevent
      // the main dashboard from loading.
    }
  }


  async function loadData() {
    try {
      setError("");

      const [
        workspaceData,
        incidentData,
      ] = await Promise.all([
        getWorkspaces(),
        getIncidents(),
      ]);

      setWorkspaces(workspaceData);
      setIncidents(incidentData);

      if (
        !selectedWorkspaceId &&
        workspaceData.length > 0
      ) {
        setSelectedWorkspaceId(
          workspaceData[0].id
        );
      }

      await Promise.all([
        loadLatestAnalyses(
          incidentData
        ),

        refreshAgentRunStats(),
      ]);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to load dashboard"
      );
    } finally {
      setLoading(false);
    }
  }


  useEffect(() => {
    void loadData();
  }, []);


  async function handleCreateWorkspace(
    event: FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    try {
      setSubmitting(true);
      setError("");
      setMessage("");

      const workspace =
        await createWorkspace({
          name: workspaceName,
          slug: workspaceSlug,
        });

      setWorkspaces((current) => [
        workspace,
        ...current,
      ]);

      setSelectedWorkspaceId(
        workspace.id
      );

      setWorkspaceName("");
      setWorkspaceSlug("");

      setMessage(
        "Workspace created successfully."
      );
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to create workspace"
      );
    } finally {
      setSubmitting(false);
    }
  }


  async function handleCreateIncident(
    event: FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    if (!selectedWorkspaceId) {
      setError(
        "Create or select a workspace first."
      );
      return;
    }

    try {
      setSubmitting(true);
      setError("");
      setMessage("");

      const incident =
        await createIncident({
          workspace_id:
            selectedWorkspaceId,

          title:
            incidentTitle,

          description:
            incidentDescription,

          service_name:
            serviceName || null,
        });

      setIncidents((current) => [
        incident,
        ...current,
      ]);

      setLatestAnalyses((current) => ({
        ...current,
        [incident.id]: null,
      }));

      setToolInvestigations(
        (current) => ({
          ...current,
          [incident.id]: null,
        })
      );

      setInvestigationQuestions(
        (current) => ({
          ...current,
          [incident.id]: "",
        })
      );

      setAgentGoals(
        (current) => ({
          ...current,

          [incident.id]: "",
        })
      );


setAgentInvestigations(
  (current) => ({
    ...current,

    [incident.id]: null,
  })
);

      setIncidentTitle("");
      setIncidentDescription("");
      setServiceName("");

      setMessage(
        "Incident created successfully."
      );
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to create incident"
      );
    } finally {
      setSubmitting(false);
    }
  }


  async function handleAnalyzeIncident(
    incidentId: string
  ) {
    try {
      setAnalyzingIncidentId(
        incidentId
      );

      setError("");
      setMessage("");

      const analysis =
        await analyzeIncident(
          incidentId
        );

      setLatestAnalyses((current) => ({
        ...current,
        [incidentId]: analysis,
      }));

      setMessage(
        "AI analysis completed successfully."
      );
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to analyze incident"
      );
    } finally {
      setAnalyzingIncidentId(null);
    }
  }


  function handleInvestigationQuestionChange(
    incidentId: string,
    question: string
  ) {
    setInvestigationQuestions(
      (current) => ({
        ...current,
        [incidentId]: question,
      })
    );
  }

  function handleAgentGoalChange(
    incidentId: string,
    goal: string
  ) {
    setAgentGoals(
      (current) => ({
        ...current,

        [incidentId]: goal,
      })
    );
  }

  async function handleAgentInvestigation(
    incidentId: string
  ) {
    const goal = (
      agentGoals[
        incidentId
      ] ?? ""
    ).trim();


    if (goal.length < 5) {
      setError(
        "Agent goal must contain at least 5 characters."
      );

      return;
    }


    try {
      setRunningAgentIncidentId(
        incidentId
      );

      setError("");
      setMessage("");


      const investigation =
        await investigateIncidentWithAgent(
          incidentId,
          {
            goal,
          }
        );


      setAgentInvestigations(
        (current) => ({
          ...current,

          [incidentId]:
            investigation,
        })
      );


      setMessage(
        `Agent investigation completed with ${investigation.tool_calls_count} tool call${
          investigation.tool_calls_count === 1
            ? ""
            : "s"
        }.`
      );

    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to run agent investigation"
      );

    } finally {
      setRunningAgentIncidentId(
        null
      );

      await refreshAgentRunStats();
    }
  }


  async function handleToolInvestigation(
    incidentId: string
  ) {
    const question = (
      investigationQuestions[
        incidentId
      ] ?? ""
    ).trim();

    if (question.length < 5) {
      setError(
        "Investigation question must contain at least 5 characters."
      );
      return;
    }

    try {
      setInvestigatingIncidentId(
        incidentId
      );

      setError("");
      setMessage("");

      const investigation =
        await investigateIncidentWithTool(
          incidentId,
          {
            question,
          }
        );

      setToolInvestigations(
        (current) => ({
          ...current,
          [incidentId]: investigation,
        })
      );

      setMessage(
        investigation.tool_called
          ? "Tool-assisted investigation completed successfully."
          : "Investigation completed without a tool call."
      );
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to investigate incident"
      );
    } finally {
      setInvestigatingIncidentId(
        null
      );
    }
  }


  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <div className="mx-auto max-w-7xl px-6 py-10">
        <header className="mb-10">
          <p className="mb-2 text-sm font-semibold uppercase tracking-widest text-cyan-400">
            Agentic Incident Operations
          </p>

          <h1 className="text-4xl font-bold">
            OpsPilot
          </h1>

          <p className="mt-3 max-w-2xl text-slate-400">
            Create incidents, perform
            structured AI triage, and run
            model-directed operational tool
            investigations.
          </p>
        </header>


        {message && (
          <div className="mb-6 rounded-lg border border-emerald-700 bg-emerald-950/50 px-4 py-3 text-emerald-300">
            {message}
          </div>
        )}


        {error && (
          <div className="mb-6 rounded-lg border border-red-700 bg-red-950/50 px-4 py-3 text-red-300">
            {error}
          </div>
        )}


        <section className="mb-8 grid gap-4 md:grid-cols-3">
          <div className="rounded-xl border border-slate-800 bg-slate-900 p-5">
            <p className="text-sm text-slate-400">
              Workspaces
            </p>

            <p className="mt-2 text-3xl font-bold">
              {workspaces.length}
            </p>
          </div>


          <div className="rounded-xl border border-slate-800 bg-slate-900 p-5">
            <p className="text-sm text-slate-400">
              Incidents
            </p>

            <p className="mt-2 text-3xl font-bold">
              {incidents.length}
            </p>
          </div>


          <div className="rounded-xl border border-slate-800 bg-slate-900 p-5">
            <p className="text-sm text-slate-400">
              Agent Runs
            </p>

            <p className="mt-2 text-3xl font-bold">
              {agentRunStats.total}
            </p>

            <p className="mt-2 text-xs text-slate-500">
              {agentRunStats.completed}
              {" completed · "}

              {agentRunStats.failed}
              {" failed"}
            </p>
          </div>
        </section>


        <section className="grid gap-8 lg:grid-cols-2">
          <form
            onSubmit={
              handleCreateWorkspace
            }
            className="rounded-xl border border-slate-800 bg-slate-900 p-6"
          >
            <h2 className="text-xl font-semibold">
              Create Workspace
            </h2>

            <p className="mt-1 text-sm text-slate-400">
              A workspace represents one
              company or tenant.
            </p>

            <div className="mt-6 space-y-4">
              <input
                value={workspaceName}
                onChange={(event) =>
                  setWorkspaceName(
                    event.target.value
                  )
                }
                placeholder="Workspace name"
                required
                minLength={2}
                className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 outline-none focus:border-cyan-500"
              />

              <input
                value={workspaceSlug}
                onChange={(event) =>
                  setWorkspaceSlug(
                    event.target.value
                  )
                }
                placeholder="workspace-slug"
                required
                minLength={2}
                pattern="[a-z0-9-]+"
                className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 outline-none focus:border-cyan-500"
              />

              <button
                type="submit"
                disabled={submitting}
                className="w-full rounded-lg bg-cyan-500 px-4 py-3 font-semibold text-slate-950 disabled:cursor-not-allowed disabled:opacity-50"
              >
                Create Workspace
              </button>
            </div>
          </form>


          <form
            onSubmit={
              handleCreateIncident
            }
            className="rounded-xl border border-slate-800 bg-slate-900 p-6"
          >
            <h2 className="text-xl font-semibold">
              Create Incident
            </h2>

            <p className="mt-1 text-sm text-slate-400">
              This is the operational problem
              our future agent will investigate.
            </p>

            <div className="mt-6 space-y-4">
              <select
                value={
                  selectedWorkspaceId
                }
                onChange={(event) =>
                  setSelectedWorkspaceId(
                    event.target.value
                  )
                }
                required
                className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 outline-none focus:border-cyan-500"
              >
                <option value="">
                  Select workspace
                </option>

                {workspaces.map(
                  (workspace) => (
                    <option
                      key={workspace.id}
                      value={workspace.id}
                    >
                      {workspace.name}
                    </option>
                  )
                )}
              </select>


              <input
                value={incidentTitle}
                onChange={(event) =>
                  setIncidentTitle(
                    event.target.value
                  )
                }
                placeholder="Incident title"
                required
                minLength={3}
                className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 outline-none focus:border-cyan-500"
              />


              <input
                value={serviceName}
                onChange={(event) =>
                  setServiceName(
                    event.target.value
                  )
                }
                placeholder="Service name, e.g. checkout-service"
                className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 outline-none focus:border-cyan-500"
              />


              <textarea
                value={
                  incidentDescription
                }
                onChange={(event) =>
                  setIncidentDescription(
                    event.target.value
                  )
                }
                placeholder="Describe what is going wrong..."
                required
                minLength={3}
                rows={4}
                className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 outline-none focus:border-cyan-500"
              />


              <button
                type="submit"
                disabled={submitting}
                className="w-full rounded-lg bg-cyan-500 px-4 py-3 font-semibold text-slate-950 disabled:cursor-not-allowed disabled:opacity-50"
              >
                Create Incident
              </button>
            </div>
          </form>
        </section>


        <section className="mt-8 rounded-xl border border-slate-800 bg-slate-900 p-6">
          <div className="mb-6">
            <h2 className="text-xl font-semibold">
              Recent Incidents
            </h2>

            <p className="mt-1 text-sm text-slate-400">
              Run structured AI triage and
              model-directed operational tool
              investigations.
            </p>
          </div>


          {loading ? (
            <p className="text-slate-400">
              Loading incidents...
            </p>
          ) : incidents.length === 0 ? (
            <p className="text-slate-400">
              No incidents yet.
            </p>
          ) : (
            <div className="space-y-5">
              {incidents.map((incident) => {
                const analysis =
                  latestAnalyses[
                    incident.id
                  ];

                const investigation =
                  toolInvestigations[
                    incident.id
                  ];

                const investigationQuestion =
                  investigationQuestions[
                    incident.id
                  ] ?? "";

                const isAnalyzing =
                  analyzingIncidentId ===
                  incident.id;

                const isInvestigating =
                  investigatingIncidentId ===
                  incident.id;
                
                const agentGoal =
                  agentGoals[
                    incident.id
                  ] ?? "";


                const agentInvestigation =
                  agentInvestigations[
                    incident.id
                  ];


                const isRunningAgent =
                  runningAgentIncidentId ===
                  incident.id;
                  

                return (
                  <article
                    key={incident.id}
                    className="rounded-xl border border-slate-800 bg-slate-950 p-5"
                  >
                    <div className="flex flex-wrap items-start justify-between gap-4">
                      <div>
                        <h3 className="font-semibold">
                          {incident.title}
                        </h3>

                        <p className="mt-1 text-sm text-cyan-400">
                          {incident.service_name ??
                            "No service specified"}
                        </p>
                      </div>

                      <span className="rounded-full bg-amber-500/10 px-3 py-1 text-xs font-medium text-amber-300">
                        {incident.status}
                      </span>
                    </div>


                    <p className="mt-4 text-sm leading-6 text-slate-400">
                      {incident.description}
                    </p>


                    <div className="mt-5 flex flex-wrap items-center justify-between gap-4">
                      <p className="text-xs text-slate-600">
                        {new Date(
                          incident.created_at
                        ).toLocaleString()}
                      </p>

                      <button
                        type="button"
                        onClick={() =>
                          void handleAnalyzeIncident(
                            incident.id
                          )
                        }
                        disabled={isAnalyzing}
                        className="rounded-lg bg-cyan-500 px-4 py-2 text-sm font-semibold text-slate-950 transition hover:bg-cyan-400 disabled:cursor-not-allowed disabled:opacity-50"
                      >
                        {isAnalyzing
                          ? "Analyzing..."
                          : analysis
                            ? "Re-analyze with AI"
                            : "Analyze with AI"}
                      </button>
                    </div>


                    {analysis && (
                      <IncidentAnalysisPanel
                        analysis={analysis}
                      />
                    )}


                    <div className="mt-6 rounded-xl border border-violet-500/20 bg-violet-500/5 p-5">
                      <div>
                        <p className="text-xs font-semibold uppercase tracking-widest text-violet-400">
                          Operational Investigation
                        </p>

                        <p className="mt-2 text-sm text-slate-400">
                          Ask a question and let the
                          model decide whether an
                          operational tool is needed.
                        </p>
                      </div>


                      <textarea
                        value={
                          investigationQuestion
                        }
                        onChange={(event) =>
                          handleInvestigationQuestionChange(
                            incident.id,
                            event.target.value
                          )
                        }
                        placeholder="Example: Search runtime evidence for errors or timeouts related to the failure"
                        rows={3}
                        maxLength={500}
                        className="mt-4 w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-sm outline-none focus:border-violet-500"
                      />


                      <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
                        <p className="text-xs text-slate-600">
                          {
                            investigationQuestion.length
                          }
                          /500
                        </p>

                        <button
                          type="button"
                          onClick={() =>
                            void handleToolInvestigation(
                              incident.id
                            )
                          }
                          disabled={
                            isInvestigating ||
                            investigationQuestion
                              .trim()
                              .length < 5
                          }
                          className="rounded-lg bg-violet-500 px-4 py-2 text-sm font-semibold text-white transition hover:bg-violet-400 disabled:cursor-not-allowed disabled:opacity-50"
                        >
                          {isInvestigating
                            ? "Investigating..."
                            : "Investigate with Tools"}
                        </button>
                      </div>
                    </div>


                    {investigation && (
                      <ToolInvestigationPanel
                        investigation={
                          investigation
                        }
                      />
                    )}
                    <div className="mt-6 rounded-xl border border-blue-500/20 bg-blue-500/5 p-5">
                      <div>
                        <p className="text-xs font-semibold uppercase tracking-widest text-blue-400">
                          Agentic Investigation
                        </p>

                        <p className="mt-2 text-sm text-slate-400">
                          Give the agent an operational goal.
                          It may dynamically choose zero or
                          multiple tools and stop when enough
                          evidence has been gathered.
                        </p>
                      </div>


                      <textarea
                        value={agentGoal}

                        onChange={(event) =>
                          handleAgentGoalChange(
                            incident.id,
                            event.target.value
                          )
                        }

                        placeholder="Example: Investigate the most likely cause of the HTTP 500 failures and verify important hypotheses using available operational evidence."

                        rows={4}

                        maxLength={1000}

                        className="mt-4 w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-sm outline-none focus:border-blue-500"
                      />


                      <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
                        <p className="text-xs text-slate-600">
                          {agentGoal.length}
                          /1000
                        </p>


                        <button
                          type="button"

                          onClick={() =>
                            void handleAgentInvestigation(
                              incident.id
                            )
                          }

                          disabled={
                            runningAgentIncidentId !== null ||
                            agentGoal.trim().length < 5
                          }

                          className="rounded-lg bg-blue-500 px-4 py-2 text-sm font-semibold text-white transition hover:bg-blue-400 disabled:cursor-not-allowed disabled:opacity-50"
                        >
                          {isRunningAgent
                            ? "Running Agent..."
                            : "Run Agent"}
                        </button>
                      </div>
                    </div>


                    {agentInvestigation && (
                      <AgentInvestigationPanel
                        investigation={
                          agentInvestigation
                        }
                      />
                    )}
                  </article>
                );
              })}
            </div>
          )}
        </section>
      </div>
    </main>
  );
}