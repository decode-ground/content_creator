import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { CheckCircle, AlertCircle, Loader2, Clock, ChevronDown, ChevronUp } from "lucide-react";
import { useState } from "react";

export interface WorkflowStep {
  id: string;
  agentName: string;
  status: string;
  input?: any;
  output?: any;
  reasoning?: string;
  duration?: number;
  error?: string;
}

export interface WorkflowVisualizationProps {
  steps: WorkflowStep[];
  currentStep: number;
  progress: number;
  status: string;
}

const AGENT_COLORS: Record<string, { bg: string; border: string; text: string }> = {
  ScriptAnalysisAgent: { bg: "from-blue-500/10 to-blue-600/10", border: "border-blue-500/30", text: "text-blue-400" },
  SceneBreakdownAgent: { bg: "from-cyan-500/10 to-cyan-600/10", border: "border-cyan-500/30", text: "text-cyan-400" },
  CharacterConsistencyAgent: { bg: "from-purple-500/10 to-purple-600/10", border: "border-purple-500/30", text: "text-purple-400" },
  SettingConsistencyAgent: { bg: "from-emerald-500/10 to-emerald-600/10", border: "border-emerald-500/30", text: "text-emerald-400" },
  StoryboardPromptAgent: { bg: "from-amber-500/10 to-amber-600/10", border: "border-amber-500/30", text: "text-amber-400" },
  VideoPromptAgent: { bg: "from-orange-500/10 to-orange-600/10", border: "border-orange-500/30", text: "text-orange-400" },
  VideoGenerationAgent: { bg: "from-pink-500/10 to-pink-600/10", border: "border-pink-500/30", text: "text-pink-400" },
  VideoAssemblyAgent: { bg: "from-rose-500/10 to-rose-600/10", border: "border-rose-500/30", text: "text-rose-400" },
};

function getAgentColors(agentName: string) {
  return AGENT_COLORS[agentName] || { bg: "from-slate-500/10 to-slate-600/10", border: "border-slate-500/30", text: "text-slate-400" };
}

function getStatusIcon(status: string | undefined, isActive: boolean) {
  if (status === "completed") return <CheckCircle className="w-5 h-5 text-emerald-500" />;
  if (status === "failed") return <AlertCircle className="w-5 h-5 text-red-500" />;
  if (status === "running" || isActive) return <Loader2 className="w-5 h-5 text-purple-500 animate-spin" />;
  return <Clock className="w-5 h-5 text-slate-500" />;
}

export function WorkflowVisualization({ steps, currentStep, progress, status }: WorkflowVisualizationProps) {
  const [expandedStep, setExpandedStep] = useState<string | null>(null);

  return (
    <div className="space-y-6">
      {/* Progress Bar */}
      <Card className="border-slate-700 bg-gradient-to-br from-slate-800/50 to-slate-900/50">
        <CardHeader>
          <CardTitle className="text-white flex items-center justify-between">
            <span>Workflow Progress</span>
            <span className="text-lg font-bold text-purple-400">{progress}%</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="w-full bg-slate-700 rounded-full h-3">
              <div
                className="bg-gradient-to-r from-purple-500 to-pink-500 h-3 rounded-full transition-all duration-500"
                style={{ width: `${progress}%` }}
              />
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-slate-400">
                {status === "completed" && "Workflow completed"}
                {status === "failed" && "Workflow failed"}
                {status === "paused" && "Workflow paused"}
                {status === "running" && `Step ${currentStep + 1} of ${steps.length}`}
                {status === "pending" && "Workflow pending"}
              </span>
              <span className={`px-3 py-1 rounded-full text-xs font-medium capitalize ${
                status === "completed" ? "bg-emerald-500/20 text-emerald-400" :
                status === "failed" ? "bg-red-500/20 text-red-400" :
                status === "paused" ? "bg-yellow-500/20 text-yellow-400" :
                status === "running" ? "bg-purple-500/20 text-purple-400" :
                "bg-slate-500/20 text-slate-400"
              }`}>
                {status}
              </span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Agent Pipeline */}
      <Card className="border-slate-700 bg-gradient-to-br from-slate-800/50 to-slate-900/50">
        <CardHeader>
          <CardTitle className="text-white">Agent Pipeline</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {steps.map((step, index) => {
              const isActive = index === currentStep;
              const colors = getAgentColors(step.agentName);
              const isExpanded = expandedStep === step.id;

              return (
                <div key={step.id}>
                  <button
                    onClick={() => setExpandedStep(isExpanded ? null : step.id)}
                    className={`w-full p-4 rounded-lg border transition-all ${colors.border} bg-gradient-to-r ${colors.bg} hover:border-slate-600`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3 flex-1">
                        <div className="flex-shrink-0">
                          {getStatusIcon(step.status, isActive)}
                        </div>
                        <div className="text-left flex-1">
                          <div className="flex items-center gap-2">
                            <span className={`font-medium ${colors.text}`}>{step.agentName}</span>
                            {isActive && <span className="text-xs px-2 py-1 rounded bg-purple-500/30 text-purple-300">Running</span>}
                            {step.status === "completed" && <span className="text-xs px-2 py-1 rounded bg-emerald-500/30 text-emerald-300">Done</span>}
                            {step.status === "failed" && <span className="text-xs px-2 py-1 rounded bg-red-500/30 text-red-300">Failed</span>}
                          </div>
                          {step.duration && <p className="text-xs text-slate-400 mt-1">{step.duration}ms</p>}
                        </div>
                      </div>
                      <div className="flex-shrink-0">
                        {isExpanded ? (
                          <ChevronUp className="w-5 h-5 text-slate-400" />
                        ) : (
                          <ChevronDown className="w-5 h-5 text-slate-400" />
                        )}
                      </div>
                    </div>
                  </button>

                  {/* Expanded Details */}
                  {isExpanded && (
                    <div className="mt-2 p-4 rounded-lg bg-slate-900/50 border border-slate-700 space-y-3">
                      {/* Reasoning */}
                      {step.reasoning && (
                        <div>
                          <h4 className="text-sm font-semibold text-slate-300 mb-2">Reasoning</h4>
                          <p className="text-sm text-slate-400 bg-slate-800/50 p-3 rounded border border-slate-700 max-h-32 overflow-y-auto">
                            {step.reasoning}
                          </p>
                        </div>
                      )}

                      {/* Input */}
                      {step.input && (
                        <div>
                          <h4 className="text-sm font-semibold text-slate-300 mb-2">Input</h4>
                          <pre className="text-xs text-slate-400 bg-slate-800/50 p-3 rounded border border-slate-700 overflow-x-auto max-h-32">
                            {JSON.stringify(step.input, null, 2).substring(0, 500)}
                          </pre>
                        </div>
                      )}

                      {/* Output */}
                      {step.output && (
                        <div>
                          <h4 className="text-sm font-semibold text-slate-300 mb-2">Output</h4>
                          <pre className="text-xs text-slate-400 bg-slate-800/50 p-3 rounded border border-slate-700 overflow-x-auto max-h-32">
                            {JSON.stringify(step.output, null, 2).substring(0, 500)}
                          </pre>
                        </div>
                      )}

                      {/* Error */}
                      {step.error && (
                        <div>
                          <h4 className="text-sm font-semibold text-red-400 mb-2">Error</h4>
                          <p className="text-sm text-red-300 bg-red-500/10 p-3 rounded border border-red-500/30">{step.error}</p>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Connection Line */}
                  {index < steps.length - 1 && (
                    <div className="flex justify-center py-1">
                      <div className="w-0.5 h-4 bg-gradient-to-b from-slate-600 to-slate-700" />
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Workflow Statistics */}
      {steps.length > 0 && (
        <Card className="border-slate-700 bg-gradient-to-br from-slate-800/50 to-slate-900/50">
          <CardHeader>
            <CardTitle className="text-white">Statistics</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-sm text-slate-400 mb-1">Total Steps</p>
                <p className="text-2xl font-bold text-white">{steps.length}</p>
              </div>
              <div>
                <p className="text-sm text-slate-400 mb-1">Completed</p>
                <p className="text-2xl font-bold text-emerald-400">{steps.filter(s => s.status === "completed").length}</p>
              </div>
              <div>
                <p className="text-sm text-slate-400 mb-1">Running</p>
                <p className="text-2xl font-bold text-purple-400">{steps.filter(s => s.status === "running").length}</p>
              </div>
              <div>
                <p className="text-sm text-slate-400 mb-1">Failed</p>
                <p className="text-2xl font-bold text-red-400">{steps.filter(s => s.status === "failed").length}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
