import type {
  IncidentAnalysis,
  Severity,
} from "@/types";


interface IncidentAnalysisPanelProps {
  analysis: IncidentAnalysis;
}


function getSeverityClasses(
  severity: Severity
): string {
  switch (severity) {
    case "critical":
      return (
        "border-red-500/40 " +
        "bg-red-500/10 " +
        "text-red-300"
      );

    case "high":
      return (
        "border-orange-500/40 " +
        "bg-orange-500/10 " +
        "text-orange-300"
      );

    case "medium":
      return (
        "border-amber-500/40 " +
        "bg-amber-500/10 " +
        "text-amber-300"
      );

    case "low":
      return (
        "border-emerald-500/40 " +
        "bg-emerald-500/10 " +
        "text-emerald-300"
      );
  }
}


export default function IncidentAnalysisPanel({
  analysis,
}: IncidentAnalysisPanelProps) {
  const confidencePercentage = Math.round(
    analysis.confidence * 100
  );

  return (
    <div className="mt-5 rounded-xl border border-cyan-500/20 bg-cyan-500/5 p-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-widest text-cyan-400">
            AI Triage Analysis
          </p>

          <p className="mt-1 text-xs text-slate-500">
            Structured incident assessment
          </p>
        </div>

        <span
          className={
            "rounded-full border px-3 py-1 " +
            "text-xs font-semibold uppercase " +
            getSeverityClasses(analysis.severity)
          }
        >
          {analysis.severity}
        </span>
      </div>


      <div className="mt-5 grid gap-3 sm:grid-cols-3">
        <div className="rounded-lg border border-slate-800 bg-slate-950/70 p-4">
          <p className="text-xs uppercase tracking-wide text-slate-500">
            Category
          </p>

          <p className="mt-2 font-medium text-slate-200">
            {analysis.category}
          </p>
        </div>


        <div className="rounded-lg border border-slate-800 bg-slate-950/70 p-4">
          <p className="text-xs uppercase tracking-wide text-slate-500">
            Confidence
          </p>

          <p className="mt-2 font-medium text-slate-200">
            {confidencePercentage}%
          </p>
        </div>


        <div className="rounded-lg border border-slate-800 bg-slate-950/70 p-4">
          <p className="text-xs uppercase tracking-wide text-slate-500">
            Affected Service
          </p>

          <p className="mt-2 break-words font-medium text-slate-200">
            {analysis.affected_service}
          </p>
        </div>
      </div>


      <div className="mt-5 space-y-4">
        <div>
          <h4 className="text-sm font-semibold text-slate-200">
            Analysis Summary
          </h4>

          <p className="mt-2 text-sm leading-6 text-slate-400">
            {analysis.analysis_summary}
          </p>
        </div>


        <div>
          <h4 className="text-sm font-semibold text-slate-200">
            Likely Impact
          </h4>

          <p className="mt-2 text-sm leading-6 text-slate-400">
            {analysis.likely_impact}
          </p>
        </div>


        <div>
          <h4 className="text-sm font-semibold text-slate-200">
            Recommended Next Step
          </h4>

          <p className="mt-2 text-sm leading-6 text-cyan-200">
            {analysis.recommended_next_step}
          </p>
        </div>
      </div>


      <div className="mt-5 flex flex-wrap gap-x-4 gap-y-2 border-t border-slate-800 pt-4 text-xs text-slate-600">
        <span>
          Model: {analysis.model_name}
        </span>

        <span>
          Prompt: {analysis.prompt_version}
        </span>

        <span>
          {new Date(
            analysis.created_at
          ).toLocaleString()}
        </span>
      </div>
    </div>
  );
}