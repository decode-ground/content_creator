import { invokeLLM } from "../_core/llm";
import { AgentConfig, AgentContext, AgentMessage, AgentResult, AgentTool } from "./types";

/**
 * Base Agent class - foundation for all specialized agents in the workflow
 * Each agent handles a specific task in the script-to-movie pipeline
 */
export abstract class Agent {
  protected config: AgentConfig;
  protected context: AgentContext;

  constructor(config: AgentConfig, context: AgentContext) {
    this.config = config;
    this.context = context;
  }

  /**
   * Main execution method - to be implemented by subclasses
   */
  abstract execute(input: any): Promise<AgentResult>;

  /**
   * Invoke LLM with reasoning and chain-of-thought
   */
  protected async reasonWithLLM(
    userMessage: string,
    systemPrompt?: string
  ): Promise<{ reasoning: string; conclusion: string }> {
    const messages: AgentMessage[] = [
      {
        role: "system",
        content:
          systemPrompt ||
          this.config.systemPrompt +
            `\n\nYou are an expert agent in the script-to-movie production pipeline. 
Think step-by-step and explain your reasoning before providing conclusions.
Format your response as:
REASONING: [Your detailed reasoning]
CONCLUSION: [Your final conclusion/answer]`,
      },
      ...this.context.conversationHistory,
      { role: "user", content: userMessage },
    ];

    const response = await invokeLLM({
      messages: messages.map((m) => ({
        role: m.role,
        content: m.content,
      })),
    });

    const content = response.choices[0]?.message.content;
    if (!content || typeof content !== "string") {
      throw new Error("Failed to get response from LLM");
    }

    // Parse reasoning and conclusion
    const reasoningMatch = content.match(/REASONING:\s*([\s\S]*?)(?=CONCLUSION:|$)/);
    const conclusionMatch = content.match(/CONCLUSION:\s*([\s\S]*?)$/);

    const reasoning = reasoningMatch ? reasoningMatch[1].trim() : "";
    const conclusion = conclusionMatch ? conclusionMatch[1].trim() : content;

    // Add to conversation history
    this.context.conversationHistory.push(
      { role: "user", content: userMessage },
      { role: "assistant", content }
    );

    return { reasoning, conclusion };
  }

  /**
   * Invoke LLM with structured JSON output
   */
  protected async structuredLLMCall<T>(
    userMessage: string,
    schema: any,
    systemPrompt?: string
  ): Promise<T> {
    const messages: AgentMessage[] = [
      {
        role: "system",
        content: systemPrompt || this.config.systemPrompt,
      },
      ...this.context.conversationHistory,
      { role: "user", content: userMessage },
    ];

    const response = await invokeLLM({
      messages: messages.map((m) => ({
        role: m.role,
        content: m.content,
      })),
      response_format: {
        type: "json_schema",
        json_schema: {
          name: "structured_output",
          strict: true,
          schema,
        },
      },
    });

    const content = response.choices[0]?.message.content;
    if (!content || typeof content !== "string") {
      throw new Error("Failed to get structured response from LLM");
    }

    const parsed = JSON.parse(content);

    // Add to conversation history
    this.context.conversationHistory.push(
      { role: "user", content: userMessage },
      { role: "assistant", content }
    );

    return parsed as T;
  }

  /**
   * Use a tool from the agent's toolkit
   */
  protected async useTool(toolName: string, input: any): Promise<any> {
    const tool = this.config.tools?.find((t) => t.name === toolName);
    if (!tool) {
      throw new Error(`Tool ${toolName} not found`);
    }

    return await tool.execute(input);
  }

  /**
   * Log agent execution for debugging and analytics
   */
  protected logExecution(input: any, output: any, reasoning: string, duration: number) {
    console.log(`[${this.config.name}] Execution Log:`, {
      projectId: this.context.projectId,
      agentName: this.config.name,
      timestamp: new Date(),
      input,
      output,
      reasoning,
      duration,
    });
  }

  /**
   * Create a successful result
   */
  protected success<T>(data: T, reasoning?: string, nextAgent?: string): AgentResult<T> {
    return {
      success: true,
      data,
      reasoning,
      nextAgent,
    };
  }

  /**
   * Create a failed result
   */
  protected failure(error: string, reasoning?: string): AgentResult {
    return {
      success: false,
      error,
      reasoning,
    };
  }

  /**
   * Get agent name
   */
  getName(): string {
    return this.config.name;
  }

  /**
   * Get agent description
   */
  getDescription(): string {
    return this.config.description;
  }
}
