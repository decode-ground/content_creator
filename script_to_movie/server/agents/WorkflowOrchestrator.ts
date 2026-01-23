import { Agent } from "./Agent";
import { AgentContext, WorkflowExecution, WorkflowStep } from "./types";
import { ScriptAnalysisAgent } from "./ScriptAnalysisAgent";

/**
 * WorkflowOrchestrator - Manages the execution of agents in sequence
 * Handles workflow state, error recovery, and progress tracking
 */
export class WorkflowOrchestrator {
  private agents: Map<string, Agent> = new Map();
  private execution: WorkflowExecution | null = null;
  private context: AgentContext;

  constructor(context: AgentContext) {
    this.context = context;
  }

  /**
   * Register an agent with the orchestrator
   */
  registerAgent(agent: Agent): void {
    this.agents.set(agent.getName(), agent);
  }

  /**
   * Initialize the workflow
   */
  initializeWorkflow(): WorkflowExecution {
    this.execution = {
      projectId: this.context.projectId,
      steps: [],
      currentStep: 0,
      status: "pending",
      startTime: new Date(),
    };
    return this.execution;
  }

  /**
   * Execute the complete workflow
   */
  async executeWorkflow(
    startAgent: string,
    initialInput: any,
    onProgress?: (step: WorkflowStep) => void
  ): Promise<WorkflowExecution> {
    if (!this.execution) {
      this.initializeWorkflow();
    }

    if (!this.execution) {
      throw new Error("Failed to initialize workflow");
    }

    this.execution.status = "running";
    this.execution!.startTime = new Date();

    let currentAgent = startAgent;
    let currentInput = initialInput;

    try {
      while (currentAgent && this.execution!.status === "running") {
        const agent = this.agents.get(currentAgent);
        if (!agent) {
          throw new Error(`Agent ${currentAgent} not found`);
        }

        // Create workflow step
        const step: WorkflowStep = {
          id: `${currentAgent}-${Date.now()}`,
          agentName: currentAgent,
          input: currentInput,
          status: "running",
          startTime: new Date(),
        };

        this.execution!.steps.push(step);
        const stepIndex = this.execution!.steps.length - 1;
        this.execution!.currentStep = stepIndex;

        try {
          // Execute the agent
          const result = await agent.execute(currentInput);

          // Update step with results
          step.status = result.success ? "completed" : "failed";
          step.output = result.data;
          step.endTime = new Date();

          if (!result.success) {
            step.error = result.error;
            this.execution!.status = "failed";
            this.execution!.error = result.error;
            break;
          }

          // Notify progress
          if (onProgress) {
            onProgress(step);
          }

          // Determine next agent
          currentAgent = result.nextAgent || "";
          currentInput = result.data;
        } catch (error) {
          step.status = "failed";
          step.error = error instanceof Error ? error.message : "Unknown error";
          step.endTime = new Date();
          this.execution!.status = "failed";
          this.execution!.error = step.error;
          break;
        }
      }

      if (this.execution!.status === "running") {
        this.execution!.status = "completed";
      }
    } catch (error) {
      this.execution!.status = "failed";
      this.execution!.error = error instanceof Error ? error.message : "Unknown error";
    }

    this.execution!.endTime = new Date();
    return this.execution;
  }

  /**
   * Pause workflow execution
   */
  pauseWorkflow(): void {
    if (this.execution) {
      this.execution.status = "paused";
    }
  }

  /**
   * Resume workflow execution
   */
  async resumeWorkflow(onProgress?: (step: WorkflowStep) => void): Promise<WorkflowExecution> {
    if (!this.execution) {
      throw new Error("No workflow to resume");
    }

    if (this.execution.currentStep >= this.execution.steps.length) {
      throw new Error("Workflow already completed");
    }

    const lastStep = this.execution.steps[this.execution.currentStep];
    const nextAgent = lastStep.agentName; // In a real scenario, we'd get this from the result
    const nextInput = lastStep.output;

    const result = await this.executeWorkflow(nextAgent, nextInput, onProgress);
    return result;
  }

  /**
   * Get current workflow execution status
   */
  getExecutionStatus(): WorkflowExecution | null {
    return this.execution;
  }

  /**
   * Get workflow progress as percentage
   */
  getProgress(): number {
    if (!this.execution || this.execution.steps.length === 0) {
      return 0;
    }

    const completedSteps = this.execution.steps.filter((s) => s.status === "completed").length;
    return Math.round((completedSteps / this.execution.steps.length) * 100);
  }

  /**
   * Get execution logs for debugging
   */
  getExecutionLogs(): WorkflowStep[] {
    return this.execution?.steps || [];
  }

  /**
   * Reset workflow
   */
  resetWorkflow(): void {
    this.execution = null;
  }

  /**
   * Create a default workflow for script-to-movie pipeline
   */
  static createDefaultPipeline(context: AgentContext): WorkflowOrchestrator {
    const orchestrator = new WorkflowOrchestrator(context);

    // Register agents in order
    orchestrator.registerAgent(new ScriptAnalysisAgent(context));
    // TODO: Register other agents as they are created
    // orchestrator.registerAgent(new SceneBreakdownAgent(context));
    // orchestrator.registerAgent(new CharacterConsistencyAgent(context));
    // orchestrator.registerAgent(new SettingConsistencyAgent(context));
    // orchestrator.registerAgent(new StoryboardPromptAgent(context));
    // orchestrator.registerAgent(new VideoPromptAgent(context));
    // orchestrator.registerAgent(new VideoGenerationAgent(context));
    // orchestrator.registerAgent(new VideoAssemblyAgent(context));

    return orchestrator;
  }
}

/**
 * Workflow execution state machine
 */
export enum WorkflowState {
  PENDING = "pending",
  RUNNING = "running",
  PAUSED = "paused",
  COMPLETED = "completed",
  FAILED = "failed",
}

/**
 * Workflow event for real-time updates
 */
export interface WorkflowEvent {
  type: "started" | "step_completed" | "step_failed" | "completed" | "failed" | "paused" | "resumed";
  timestamp: Date;
  data: any;
}
