import type {
  AgentInvestigation,
} from "@/types";


interface AgentInvestigationPanelProps {
  investigation: AgentInvestigation;
}


interface JsonBlockProps {
  value: unknown;
}


function JsonBlock({
  value,
}: JsonBlockProps) {
  return (
    <pre className="mt-3 overflow-x-auto rounded-lg border border-slate-800 bg-slate-950 p-4 text-xs leading-6 text-slate-300">
      {JSON.stringify(
        value,
        null,
        2
      )}
    </pre>
  );
}


function getStopReasonLabel(
  stopReason:
    AgentInvestigation["stop_reason"]
): string {
  switch (stopReason) {
    case "model_finished":
      return "Model Finished";

    case "tool_budget_exhausted":
      return "Tool Budget Exhausted";
  }
}


export default function AgentInvestigationPanel({
  investigation,
}: AgentInvestigationPanelProps) {
  return (
    <div className="mt-5 rounded-xl border border-blue-500/20 bg-blue-500/5 p-5">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-widest text-blue-400">
            Agent Execution Trace
          </p>

          <p className="mt-1 text-xs text-slate-500">
            Multi-step decide, act, observe loop
          </p>
        </div>

        <span className="rounded-full border border-blue-500/40 bg-blue-500/10 px-3 py-1 text-xs font-semibold text-blue-300">
          {investigation.tool_calls_count}
          {" "}
          Tool
          {investigation.tool_calls_count === 1
            ? " Call"
            : " Calls"}
        </span>
      </div>


      <div className="mt-5 rounded-lg border border-slate-800 bg-slate-950/70 p-4">
        <p className="text-xs uppercase tracking-wide text-slate-500">
          Investigation Goal
        </p>

        <p className="mt-2 text-sm leading-6 text-slate-300">
          {investigation.goal}
        </p>
      </div>


      <div className="mt-6">
        <h4 className="text-sm font-semibold text-slate-200">
          Execution Timeline
        </h4>

        <p className="mt-1 text-xs text-slate-500">
          Each step was dynamically selected by the agent.
        </p>
      </div>


      {investigation.steps.length === 0 ? (
        <div className="mt-4 rounded-lg border border-slate-800 bg-slate-950/70 p-4">
          <p className="text-sm text-slate-400">
            No operational tools were needed.
            The agent answered from the stored
            incident context.
          </p>
        </div>
      ) : (
        <div className="mt-5 space-y-5">
          {investigation.steps.map(
            (step) => (
              <div
                key={
                  `${step.iteration}-${step.tool_name}`
                }
                className="relative border-l-2 border-blue-500/30 pl-6"
              >
                <div className="absolute -left-[7px] top-0 h-3 w-3 rounded-full bg-blue-400" />


                <div className="flex flex-wrap items-center gap-3">
                  <span className="rounded-full bg-blue-500/10 px-2.5 py-1 text-xs font-semibold text-blue-300">
                    Step {step.iteration}
                  </span>

                  <code className="text-sm font-semibold text-cyan-300">
                    {step.tool_name}
                  </code>
                </div>


                <div className="mt-4">
                  <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                    Arguments
                  </p>

                  <JsonBlock
                    value={step.arguments}
                  />
                </div>


                <div className="mt-4">
                  <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                    Observation
                  </p>

                  <JsonBlock
                    value={step.result}
                  />
                </div>
              </div>
            )
          )}
        </div>
      )}


      <div className="mt-7 rounded-lg border border-emerald-500/20 bg-emerald-500/5 p-5">
        <p className="text-xs font-semibold uppercase tracking-wide text-emerald-400">
          Final Agent Conclusion
        </p>

        <p className="mt-3 whitespace-pre-wrap text-sm leading-7 text-slate-300">
          {investigation.final_answer}
        </p>
      </div>


      <div className="mt-5 grid gap-3 sm:grid-cols-2">
        <div className="rounded-lg border border-slate-800 bg-slate-950/70 p-4">
          <p className="text-xs uppercase tracking-wide text-slate-500">
            Stop Reason
          </p>

          <p className="mt-2 text-sm font-medium text-slate-200">
            {getStopReasonLabel(
              investigation.stop_reason
            )}
          </p>
        </div>


        <div className="rounded-lg border border-slate-800 bg-slate-950/70 p-4">
          <p className="text-xs uppercase tracking-wide text-slate-500">
            Model
          </p>

          <p className="mt-2 break-words text-sm font-medium text-slate-200">
            {investigation.model_name}
          </p>
        </div>
      </div>


      <div className="mt-5 border-t border-slate-800 pt-4 text-xs text-slate-600">
        Run ID: {investigation.run_id}
      </div>
    </div>
  );
}