"use client";

import {
  useState,
} from "react";

import {
  investigateIncidentWithAgent,
  investigateIncidentWithLangChainAgent,
  investigateIncidentWithLangGraphAgent,
} from "@/lib/api";

import type {
  AgentInvestigation,
  AgentToolStep,
  LangChainAgentInvestigation,
  LangGraphAgentInvestigation,
} from "@/types";


type EngineKey =
  | "manual"
  | "langchain"
  | "langgraph";


type ComparisonResult =
  | AgentInvestigation
  | LangChainAgentInvestigation
  | LangGraphAgentInvestigation;


type RunningState = Record<
  EngineKey,
  boolean
>;


type ErrorState = Partial<
  Record<
    EngineKey,
    string
  >
>;


interface AgentOrchestrationComparisonProps {
  incidentId: string;

  onManualRunFinished?:
    () => void | Promise<void>;
}


const DEFAULT_GOAL =
  "Investigate the most likely cause of the HTTP 500 failures and verify important hypotheses using independent operational evidence.";


const ENGINE_ORDER: EngineKey[] = [
  "manual",
  "langchain",
  "langgraph",
];


function getErrorMessage(
  error: unknown,
): string {
  if (
    error instanceof Error
    && error.message
  ) {
    return error.message;
  }

  return "Unexpected investigation error";
}


function formatJson(
  value: unknown,
): string {
  return JSON.stringify(
    value,
    null,
    2,
  );
}


function ToolSteps({
  steps,
}: {
  steps: AgentToolStep[];
}) {
  if (steps.length === 0) {
    return (
      <div
        className="
          rounded-xl
          border
          border-slate-200
          bg-slate-50
          px-4
          py-3
          text-sm
          text-slate-600
        "
      >
        No tools were called.
      </div>
    );
  }


  return (
    <div className="space-y-3">
      {steps.map(
        (
          step,
          index,
        ) => (
          <div
            key={`${step.iteration}-${step.tool_name}-${index}`}
            className="
              rounded-xl
              border
              border-slate-200
              bg-white
              p-4
            "
          >
            <div
              className="
                mb-3
                flex
                flex-wrap
                items-center
                justify-between
                gap-2
              "
            >
              <div
                className="
                  text-sm
                  font-semibold
                  text-slate-900
                "
              >
                Step {step.iteration}
              </div>

              <div
                className="
                  rounded-full
                  bg-slate-100
                  px-3
                  py-1
                  font-mono
                  text-xs
                  text-slate-700
                "
              >
                {step.tool_name}
              </div>
            </div>


            <div className="space-y-3">
              <div>
                <div
                  className="
                    mb-1
                    text-xs
                    font-semibold
                    uppercase
                    tracking-wide
                    text-slate-500
                  "
                >
                  Arguments
                </div>

                <pre
                  className="
                    overflow-x-auto
                    rounded-lg
                    bg-slate-950
                    p-3
                    text-xs
                    text-slate-100
                  "
                >
                  {formatJson(
                    step.arguments,
                  )}
                </pre>
              </div>


              <div>
                <div
                  className="
                    mb-1
                    text-xs
                    font-semibold
                    uppercase
                    tracking-wide
                    text-slate-500
                  "
                >
                  Observation
                </div>

                <pre
                  className="
                    max-h-80
                    overflow-auto
                    rounded-lg
                    bg-slate-950
                    p-3
                    text-xs
                    text-slate-100
                  "
                >
                  {formatJson(
                    step.result,
                  )}
                </pre>
              </div>
            </div>
          </div>
        ),
      )}
    </div>
  );
}


function NodeTrace({
  nodes,
}: {
  nodes: string[];
}) {
  return (
    <div>
      <div
        className="
          mb-2
          text-xs
          font-semibold
          uppercase
          tracking-wide
          text-slate-500
        "
      >
        LangGraph Node Trace
      </div>

      <div
        className="
          flex
          flex-wrap
          items-center
          gap-2
        "
      >
        {nodes.map(
          (
            node,
            index,
          ) => (
            <div
              key={`${node}-${index}`}
              className="
                flex
                items-center
                gap-2
              "
            >
              <span
                className="
                  rounded-full
                  border
                  border-indigo-200
                  bg-indigo-50
                  px-3
                  py-1
                  text-xs
                  font-semibold
                  text-indigo-700
                "
              >
                {node}
              </span>

              {index < nodes.length - 1 && (
                <span
                  className="
                    text-sm
                    text-slate-400
                  "
                >
                  →
                </span>
              )}
            </div>
          ),
        )}
      </div>
    </div>
  );
}


function ResultCard({
  title,
  description,
  result,
  error,
}: {
  title: string;
  description: string;
  result?: ComparisonResult;
  error?: string;
}) {
  if (error) {
    return (
      <div
        className="
          rounded-2xl
          border
          border-red-200
          bg-red-50
          p-5
        "
      >
        <h3
          className="
            font-semibold
            text-red-900
          "
        >
          {title}
        </h3>

        <p
          className="
            mt-1
            text-sm
            text-red-700
          "
        >
          {error}
        </p>
      </div>
    );
  }


  if (!result) {
    return (
      <div
        className="
          rounded-2xl
          border
          border-dashed
          border-slate-300
          bg-slate-50
          p-5
        "
      >
        <h3
          className="
            font-semibold
            text-slate-900
          "
        >
          {title}
        </h3>

        <p
          className="
            mt-1
            text-sm
            text-slate-600
          "
        >
          {description}
        </p>

        <p
          className="
            mt-4
            text-sm
            text-slate-500
          "
        >
          Run this engine to see its
          execution trace.
        </p>
      </div>
    );
  }


  const modelCallsCount =
    "model_calls_count" in result
      ? result.model_calls_count
      : null;


  const stopReason =
    "stop_reason" in result
      ? result.stop_reason
      : null;


  const nodeTrace =
    "node_trace" in result
      ? result.node_trace
      : null;


  const harness =
    "harness" in result
      ? result.harness
      : "manual_loop";


  const runId =
    "run_id" in result
      ? result.run_id
      : null;


  return (
    <div
      className="
        rounded-2xl
        border
        border-slate-200
        bg-white
        p-5
        shadow-sm
      "
    >
      <div
        className="
          flex
          flex-wrap
          items-start
          justify-between
          gap-3
        "
      >
        <div>
          <h3
            className="
              text-lg
              font-semibold
              text-slate-950
            "
          >
            {title}
          </h3>

          <p
            className="
              mt-1
              text-sm
              text-slate-600
            "
          >
            {description}
          </p>
        </div>

        <span
          className="
            rounded-full
            bg-slate-100
            px-3
            py-1
            font-mono
            text-xs
            text-slate-700
          "
        >
          {harness}
        </span>
      </div>


      <div
        className="
          mt-5
          grid
          grid-cols-2
          gap-3
          lg:grid-cols-4
        "
      >
        <div
          className="
            rounded-xl
            bg-slate-50
            p-3
          "
        >
          <div
            className="
              text-xs
              text-slate-500
            "
          >
            Tool Calls
          </div>

          <div
            className="
              mt-1
              text-xl
              font-semibold
              text-slate-950
            "
          >
            {result.tool_calls_count}
          </div>
        </div>


        <div
          className="
            rounded-xl
            bg-slate-50
            p-3
          "
        >
          <div
            className="
              text-xs
              text-slate-500
            "
          >
            Model Calls
          </div>

          <div
            className="
              mt-1
              text-xl
              font-semibold
              text-slate-950
            "
          >
            {modelCallsCount ?? "—"}
          </div>
        </div>


        <div
          className="
            rounded-xl
            bg-slate-50
            p-3
          "
        >
          <div
            className="
              text-xs
              text-slate-500
            "
          >
            Steps
          </div>

          <div
            className="
              mt-1
              text-xl
              font-semibold
              text-slate-950
            "
          >
            {result.steps.length}
          </div>
        </div>


        <div
          className="
            rounded-xl
            bg-slate-50
            p-3
          "
        >
          <div
            className="
              text-xs
              text-slate-500
            "
          >
            Stop Reason
          </div>

          <div
            className="
              mt-1
              break-words
              text-sm
              font-semibold
              text-slate-950
            "
          >
            {stopReason ?? "framework_managed"}
          </div>
        </div>
      </div>


      {nodeTrace && (
        <div className="mt-5">
          <NodeTrace
            nodes={nodeTrace}
          />
        </div>
      )}


      <div className="mt-5">
        <div
          className="
            mb-2
            text-xs
            font-semibold
            uppercase
            tracking-wide
            text-slate-500
          "
        >
          Execution Steps
        </div>

        <ToolSteps
          steps={result.steps}
        />
      </div>


      <div
        className="
          mt-5
          rounded-xl
          border
          border-emerald-200
          bg-emerald-50
          p-4
        "
      >
        <div
          className="
            text-xs
            font-semibold
            uppercase
            tracking-wide
            text-emerald-700
          "
        >
          Final Conclusion
        </div>

        <p
          className="
            mt-2
            whitespace-pre-wrap
            text-sm
            leading-6
            text-emerald-950
          "
        >
          {result.final_answer}
        </p>
      </div>


      <div
        className="
          mt-4
          space-y-1
          text-xs
          text-slate-500
        "
      >
        <div>
          Model: {result.model_name}
        </div>

        {runId && (
          <div>
            Run ID: {runId}
          </div>
        )}
      </div>
    </div>
  );
}


export default function AgentOrchestrationComparison({
  incidentId,
  onManualRunFinished,
}: AgentOrchestrationComparisonProps) {
  const [
    goal,
    setGoal,
  ] = useState(
    DEFAULT_GOAL,
  );


  const [
    manualResult,
    setManualResult,
  ] = useState<
    AgentInvestigation | undefined
  >();


  const [
    langChainResult,
    setLangChainResult,
  ] = useState<
    LangChainAgentInvestigation
    | undefined
  >();


  const [
    langGraphResult,
    setLangGraphResult,
  ] = useState<
    LangGraphAgentInvestigation
    | undefined
  >();


  const [
    running,
    setRunning,
  ] = useState<RunningState>({
    manual: false,
    langchain: false,
    langgraph: false,
  });


  const [
    errors,
    setErrors,
  ] = useState<ErrorState>({});


  const [
    runAllRunning,
    setRunAllRunning,
  ] = useState(false);


  const setEngineRunning = (
    engine: EngineKey,
    value: boolean,
  ) => {
    setRunning(
      (current) => ({
        ...current,
        [engine]: value,
      }),
    );
  };


  const clearEngineError = (
    engine: EngineKey,
  ) => {
    setErrors(
      (current) => ({
        ...current,
        [engine]: undefined,
      }),
    );
  };


  const setEngineError = (
    engine: EngineKey,
    message: string,
  ) => {
    setErrors(
      (current) => ({
        ...current,
        [engine]: message,
      }),
    );
  };


  const executeEngine = async (
    engine: EngineKey,
    investigationGoal: string,
  ) => {
    clearEngineError(engine);

    setEngineRunning(
      engine,
      true,
    );


    try {
      const payload = {
        goal: investigationGoal,
      };


      if (engine === "manual") {
        const result =
          await investigateIncidentWithAgent(
            incidentId,
            payload,
          );

        setManualResult(result);

        await onManualRunFinished?.();

        return;
      }


      if (engine === "langchain") {
        const result =
          await investigateIncidentWithLangChainAgent(
            incidentId,
            payload,
          );

        setLangChainResult(result);

        return;
      }


      const result =
        await investigateIncidentWithLangGraphAgent(
          incidentId,
          payload,
        );

      setLangGraphResult(result);
    } catch (error) {
      setEngineError(
        engine,
        getErrorMessage(error),
      );
    } finally {
      setEngineRunning(
        engine,
        false,
      );
    }
  };


  const validateGoal = (): string | null => {
    const cleanedGoal = goal.trim();

    if (cleanedGoal.length < 5) {
      return null;
    }

    return cleanedGoal;
  };


  const handleRunEngine = async (
    engine: EngineKey,
  ) => {
    const cleanedGoal =
      validateGoal();

    if (!cleanedGoal) {
      setEngineError(
        engine,
        "Goal must contain at least 5 characters.",
      );

      return;
    }


    await executeEngine(
      engine,
      cleanedGoal,
    );
  };


  const handleRunAll = async () => {
    const cleanedGoal =
      validateGoal();

    if (!cleanedGoal) {
      setErrors({
        manual:
          "Goal must contain at least 5 characters.",

        langchain:
          "Goal must contain at least 5 characters.",

        langgraph:
          "Goal must contain at least 5 characters.",
      });

      return;
    }


    setRunAllRunning(true);


    try {
      /*
       * Run sequentially rather than in parallel.
       *
       * This gives cleaner comparisons and avoids
       * sending three simultaneous model workloads
       * to the provider.
       */
      for (
        const engine
        of ENGINE_ORDER
      ) {
        await executeEngine(
          engine,
          cleanedGoal,
        );
      }
    } finally {
      setRunAllRunning(false);
    }
  };


  const handleClear = () => {
    setManualResult(undefined);

    setLangChainResult(undefined);

    setLangGraphResult(undefined);

    setErrors({});
  };


  const anyEngineRunning =
    running.manual
    || running.langchain
    || running.langgraph;


  const controlsDisabled =
    runAllRunning
    || anyEngineRunning;


  return (
    <section
      className="
        mt-6
        rounded-2xl
        border
        border-indigo-200
        bg-indigo-50/40
        p-5
      "
    >
      <div>
        <h2
          className="
            text-lg
            font-semibold
            text-slate-950
          "
        >
          Agent Orchestration Comparison
        </h2>

        <p
          className="
            mt-1
            text-sm
            text-slate-600
          "
        >
          Run the same investigation goal
          through the manual loop, LangChain
          create_agent, and explicit LangGraph
          orchestration.
        </p>
      </div>


      <div className="mt-5">
        <label
          className="
            text-sm
            font-medium
            text-slate-800
          "
        >
          Investigation Goal
        </label>

        <textarea
          value={goal}
          onChange={(
            event,
          ) => {
            setGoal(
              event.target.value,
            );
          }}
          rows={5}
          className="
            mt-2
            w-full
            rounded-xl
            border
            border-slate-300
            bg-white
            px-4
            py-3
            text-sm
            text-slate-900
            outline-none
            transition
            focus:border-indigo-500
            focus:ring-2
            focus:ring-indigo-100
          "
          placeholder="Describe the investigation goal..."
        />
      </div>


      <div
        className="
          mt-4
          flex
          flex-wrap
          gap-3
        "
      >
        <button
          type="button"
          disabled={controlsDisabled}
          onClick={() => {
            void handleRunEngine(
              "manual",
            );
          }}
          className="
            rounded-xl
            bg-blue-600
            px-4
            py-2
            text-sm
            font-semibold
            text-white
            transition
            hover:bg-blue-700
            disabled:cursor-not-allowed
            disabled:opacity-50
          "
        >
          {running.manual
            ? "Running Manual..."
            : "Run Manual Loop"}
        </button>


        <button
          type="button"
          disabled={controlsDisabled}
          onClick={() => {
            void handleRunEngine(
              "langchain",
            );
          }}
          className="
            rounded-xl
            bg-violet-600
            px-4
            py-2
            text-sm
            font-semibold
            text-white
            transition
            hover:bg-violet-700
            disabled:cursor-not-allowed
            disabled:opacity-50
          "
        >
          {running.langchain
            ? "Running LangChain..."
            : "Run LangChain Agent"}
        </button>


        <button
          type="button"
          disabled={controlsDisabled}
          onClick={() => {
            void handleRunEngine(
              "langgraph",
            );
          }}
          className="
            rounded-xl
            bg-emerald-600
            px-4
            py-2
            text-sm
            font-semibold
            text-white
            transition
            hover:bg-emerald-700
            disabled:cursor-not-allowed
            disabled:opacity-50
          "
        >
          {running.langgraph
            ? "Running LangGraph..."
            : "Run LangGraph"}
        </button>


        <button
          type="button"
          disabled={controlsDisabled}
          onClick={() => {
            void handleRunAll();
          }}
          className="
            rounded-xl
            bg-slate-950
            px-4
            py-2
            text-sm
            font-semibold
            text-white
            transition
            hover:bg-slate-800
            disabled:cursor-not-allowed
            disabled:opacity-50
          "
        >
          {runAllRunning
            ? "Running All..."
            : "Run All Sequentially"}
        </button>


        <button
          type="button"
          disabled={controlsDisabled}
          onClick={handleClear}
          className="
            rounded-xl
            border
            border-slate-300
            bg-white
            px-4
            py-2
            text-sm
            font-semibold
            text-slate-700
            transition
            hover:bg-slate-50
            disabled:cursor-not-allowed
            disabled:opacity-50
          "
        >
          Clear Results
        </button>
      </div>


      <div
        className="
          mt-6
          grid
          gap-5
          xl:grid-cols-3
        "
      >
        <ResultCard
          title="Manual Loop"
          description="
            Application-owned while loop,
            bind_tools, explicit execution,
            and manual ToolMessage handling.
          "
          result={manualResult}
          error={errors.manual}
        />


        <ResultCard
          title="LangChain create_agent"
          description="
            Framework-managed agent harness
            with automatic model-tool loop.
          "
          result={langChainResult}
          error={errors.langchain}
        />


        <ResultCard
          title="LangGraph StateGraph"
          description="
            Explicit shared state, named nodes,
            conditional edges, and graph cycles.
          "
          result={langGraphResult}
          error={errors.langgraph}
        />
      </div>
    </section>
  );
}