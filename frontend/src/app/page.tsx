"use client";

import {
  FormEvent,
  useEffect,
  useState,
} from "react";

import {
  createIncident,
  createWorkspace,
  getIncidents,
  getWorkspaces,
} from "@/lib/api";

import type {
  Incident,
  Workspace,
} from "@/types";


export default function Home() {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [incidents, setIncidents] = useState<Incident[]>([]);

  const [workspaceName, setWorkspaceName] = useState("");
  const [workspaceSlug, setWorkspaceSlug] = useState("");

  const [
    selectedWorkspaceId,
    setSelectedWorkspaceId,
  ] = useState("");

  const [incidentTitle, setIncidentTitle] = useState("");
  const [
    incidentDescription,
    setIncidentDescription,
  ] = useState("");
  const [serviceName, setServiceName] = useState("");

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  const [message, setMessage] = useState("");
  const [error, setError] = useState("");


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

      const workspace = await createWorkspace({
        name: workspaceName,
        slug: workspaceSlug,
      });

      setWorkspaces((current) => [
        workspace,
        ...current,
      ]);

      setSelectedWorkspaceId(workspace.id);

      setWorkspaceName("");
      setWorkspaceSlug("");

      setMessage("Workspace created successfully.");
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
      setError("Create or select a workspace first.");
      return;
    }

    try {
      setSubmitting(true);
      setError("");
      setMessage("");

      const incident = await createIncident({
        workspace_id: selectedWorkspaceId,
        title: incidentTitle,
        description: incidentDescription,
        service_name: serviceName || null,
      });

      setIncidents((current) => [
        incident,
        ...current,
      ]);

      setIncidentTitle("");
      setIncidentDescription("");
      setServiceName("");

      setMessage("Incident created successfully.");
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
            Create operational incidents now. Later,
            our AI agent will investigate them using
            metrics, logs, deployments, and runbooks.
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
              0
            </p>
          </div>
        </section>


        <section className="grid gap-8 lg:grid-cols-2">
          <form
            onSubmit={handleCreateWorkspace}
            className="rounded-xl border border-slate-800 bg-slate-900 p-6"
          >
            <h2 className="text-xl font-semibold">
              Create Workspace
            </h2>

            <p className="mt-1 text-sm text-slate-400">
              A workspace represents one company or tenant.
            </p>

            <div className="mt-6 space-y-4">
              <input
                value={workspaceName}
                onChange={(event) =>
                  setWorkspaceName(event.target.value)
                }
                placeholder="Workspace name"
                required
                minLength={2}
                className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 outline-none focus:border-cyan-500"
              />

              <input
                value={workspaceSlug}
                onChange={(event) =>
                  setWorkspaceSlug(event.target.value)
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
                className="w-full rounded-lg bg-cyan-500 px-4 py-3 font-semibold text-slate-950 disabled:opacity-50"
              >
                Create Workspace
              </button>
            </div>
          </form>


          <form
            onSubmit={handleCreateIncident}
            className="rounded-xl border border-slate-800 bg-slate-900 p-6"
          >
            <h2 className="text-xl font-semibold">
              Create Incident
            </h2>

            <p className="mt-1 text-sm text-slate-400">
              This is the operational problem our future
              agent will investigate.
            </p>

            <div className="mt-6 space-y-4">
              <select
                value={selectedWorkspaceId}
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

                {workspaces.map((workspace) => (
                  <option
                    key={workspace.id}
                    value={workspace.id}
                  >
                    {workspace.name}
                  </option>
                ))}
              </select>

              <input
                value={incidentTitle}
                onChange={(event) =>
                  setIncidentTitle(event.target.value)
                }
                placeholder="Incident title"
                required
                minLength={3}
                className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 outline-none focus:border-cyan-500"
              />

              <input
                value={serviceName}
                onChange={(event) =>
                  setServiceName(event.target.value)
                }
                placeholder="Service name, e.g. checkout-service"
                className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 outline-none focus:border-cyan-500"
              />

              <textarea
                value={incidentDescription}
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
                className="w-full rounded-lg bg-cyan-500 px-4 py-3 font-semibold text-slate-950 disabled:opacity-50"
              >
                Create Incident
              </button>
            </div>
          </form>
        </section>


        <section className="mt-8 rounded-xl border border-slate-800 bg-slate-900 p-6">
          <div className="mb-6 flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold">
                Recent Incidents
              </h2>

              <p className="mt-1 text-sm text-slate-400">
                These will become inputs to our AI agent.
              </p>
            </div>
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
            <div className="space-y-4">
              {incidents.map((incident) => (
                <article
                  key={incident.id}
                  className="rounded-lg border border-slate-800 bg-slate-950 p-5"
                >
                  <div className="flex flex-wrap items-start justify-between gap-3">
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

                  <p className="mt-4 text-xs text-slate-600">
                    {new Date(
                      incident.created_at
                    ).toLocaleString()}
                  </p>
                </article>
              ))}
            </div>
          )}
        </section>
      </div>
    </main>
  );
}