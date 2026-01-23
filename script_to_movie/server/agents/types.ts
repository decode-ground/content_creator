/**
 * Core types for the agentic workflow system
 */

export interface AgentMessage {
  role: "user" | "assistant" | "system";
  content: string;
}

export interface AgentContext {
  projectId: number;
  userId: number;
  conversationHistory: AgentMessage[];
  metadata: Record<string, any>;
}

export interface AgentResult<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  reasoning?: string;
  nextAgent?: string;
}

export interface AgentConfig {
  name: string;
  description: string;
  systemPrompt: string;
  tools?: AgentTool[];
}

export interface AgentTool {
  name: string;
  description: string;
  execute: (input: any) => Promise<any>;
}

export interface WorkflowStep {
  id: string;
  agentName: string;
  input: any;
  output?: any;
  status: "pending" | "running" | "completed" | "failed";
  error?: string;
  startTime?: Date;
  endTime?: Date;
}

export interface WorkflowExecution {
  projectId: number;
  steps: WorkflowStep[];
  currentStep: number;
  status: "pending" | "running" | "completed" | "failed" | "paused";
  startTime: Date;
  endTime?: Date;
  error?: string;
}

export interface PromptTemplate {
  name: string;
  template: string;
  variables: string[];
  examples?: Array<{ input: Record<string, string>; output: string }>;
}

export interface PromptOptimizationResult {
  originalPrompt: string;
  optimizedPrompt: string;
  improvements: string[];
  score: number;
}

export interface AgentExecutionLog {
  projectId: number;
  agentName: string;
  timestamp: Date;
  input: any;
  output: any;
  reasoning: string;
  duration: number;
  success: boolean;
}
