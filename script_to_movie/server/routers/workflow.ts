import { z } from "zod";
import { protectedProcedure, router } from "../_core/trpc";
import { getProjectById, updateProjectStatus } from "../db";
import { WorkflowOrchestrator } from "../agents/WorkflowOrchestrator";
import { AgentContext } from "../agents/types";

export const workflowRouter = router({
  /**
   * Start a new workflow execution for a project
   */
  startWorkflow: protectedProcedure
    .input(
      z.object({
        projectId: z.number(),
        workflowType: z.enum(["full_pipeline", "storyboard_only", "video_only"]),
      })
    )
    .mutation(async ({ ctx, input }) => {
      try {
        const project = await getProjectById(input.projectId);
        if (!project) {
          throw new Error("Project not found");
        }

        // Initialize agent context
        const agentContext: AgentContext = {
          projectId: input.projectId,
          userId: ctx.user.id,
          conversationHistory: [],
          metadata: {
            workflowType: input.workflowType,
            startTime: new Date(),
          },
        };

        // Create workflow orchestrator
        const orchestrator = WorkflowOrchestrator.createDefaultPipeline(agentContext);

        // Initialize workflow
        const execution = orchestrator.initializeWorkflow();

        // Update project status
        await updateProjectStatus(input.projectId, "parsing", 5);

        return {
          success: true,
          executionId: execution.startTime.getTime().toString(),
          status: execution.status,
        };
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : "Unknown error";
        await updateProjectStatus(input.projectId, "failed", 0, errorMessage);
        throw error;
      }
    }),

  /**
   * Get workflow execution status
   */
  getWorkflowStatus: protectedProcedure
    .input(z.object({ projectId: z.number() }))
    .query(async ({ input }) => {
      const project = await getProjectById(input.projectId);
      if (!project) {
        throw new Error("Project not found");
      }

      return {
        projectId: input.projectId,
        status: project.status,
        progress: project.progress,
        error: project.errorMessage,
      };
    }),

  /**
   * Get workflow execution logs
   */
  getWorkflowLogs: protectedProcedure
    .input(z.object({ projectId: z.number() }))
    .query(async ({ input }) => {
      const project = await getProjectById(input.projectId);
      if (!project) {
        throw new Error("Project not found");
      }

      // In a real implementation, this would fetch logs from a database
      return {
        projectId: input.projectId,
        logs: [
          {
            timestamp: new Date(),
            agentName: "ScriptAnalysisAgent",
            message: "Analyzing screenplay structure...",
            level: "info",
          },
        ],
      };
    }),

  /**
   * Pause workflow execution
   */
  pauseWorkflow: protectedProcedure
    .input(z.object({ projectId: z.number() }))
    .mutation(async ({ input }) => {
      const project = await getProjectById(input.projectId);
      if (!project) {
        throw new Error("Project not found");
      }

      return {
        success: true,
        status: project.status,
      };
    }),

  /**
   * Resume workflow execution
   */
  resumeWorkflow: protectedProcedure
    .input(z.object({ projectId: z.number() }))
    .mutation(async ({ input }) => {
      const project = await getProjectById(input.projectId);
      if (!project) {
        throw new Error("Project not found");
      }

      return {
        success: true,
        status: project.status,
      };
    }),

  /**
   * Get agent descriptions and capabilities
   */
  getAgentInfo: protectedProcedure.query(async () => {
    return {
      agents: [
        {
          name: "ScriptAnalysisAgent",
          description: "Analyzes screenplay structure and narrative elements",
          capabilities: ["scene_extraction", "character_identification", "setting_extraction"],
        },
        {
          name: "SceneBreakdownAgent",
          description: "Breaks down script into detailed scenes",
          capabilities: ["scene_description", "duration_estimation", "transition_analysis"],
        },
        {
          name: "CharacterConsistencyAgent",
          description: "Maintains character consistency across scenes",
          capabilities: ["character_profiling", "visual_description", "consistency_validation"],
        },
        {
          name: "SettingConsistencyAgent",
          description: "Maintains setting consistency across scenes",
          capabilities: ["setting_profiling", "visual_description", "consistency_validation"],
        },
        {
          name: "StoryboardPromptAgent",
          description: "Generates optimized prompts for image generation",
          capabilities: ["prompt_generation", "prompt_optimization", "image_prompt_refinement"],
        },
        {
          name: "VideoPromptAgent",
          description: "Converts scenes to video generation prompts",
          capabilities: ["video_prompt_generation", "motion_description", "audio_suggestions"],
        },
        {
          name: "VideoGenerationAgent",
          description: "Manages video generation and processing",
          capabilities: ["video_generation", "quality_optimization", "file_management"],
        },
        {
          name: "VideoAssemblyAgent",
          description: "Assembles video clips into final movie",
          capabilities: ["video_assembly", "transition_management", "audio_mixing"],
        },
      ],
    };
  }),
});
