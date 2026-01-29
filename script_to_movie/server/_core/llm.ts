import Anthropic from "@anthropic-ai/sdk";
import { ENV } from "./env";

export type Role = "system" | "user" | "assistant";

export type TextContent = {
  type: "text";
  text: string;
};

export type ImageContent = {
  type: "image_url";
  image_url: {
    url: string;
    detail?: "auto" | "low" | "high";
  };
};

export type MessageContent = string | TextContent | ImageContent;

export type Message = {
  role: Role;
  content: MessageContent | MessageContent[];
};

export type Tool = {
  type: "function";
  function: {
    name: string;
    description?: string;
    parameters?: Record<string, unknown>;
  };
};

export type ToolChoicePrimitive = "none" | "auto" | "required";
export type ToolChoiceByName = { name: string };
export type ToolChoiceExplicit = {
  type: "function";
  function: {
    name: string;
  };
};

export type ToolChoice =
  | ToolChoicePrimitive
  | ToolChoiceByName
  | ToolChoiceExplicit;

export type JsonSchema = {
  name: string;
  schema: Record<string, unknown>;
  strict?: boolean;
};

export type OutputSchema = JsonSchema;

export type ResponseFormat =
  | { type: "text" }
  | { type: "json_object" }
  | { type: "json_schema"; json_schema: JsonSchema };

export type InvokeParams = {
  messages: Message[];
  tools?: Tool[];
  toolChoice?: ToolChoice;
  tool_choice?: ToolChoice;
  maxTokens?: number;
  max_tokens?: number;
  outputSchema?: OutputSchema;
  output_schema?: OutputSchema;
  responseFormat?: ResponseFormat;
  response_format?: ResponseFormat;
};

export type ToolCall = {
  id: string;
  type: "function";
  function: {
    name: string;
    arguments: string;
  };
};

export type InvokeResult = {
  id: string;
  created: number;
  model: string;
  choices: Array<{
    index: number;
    message: {
      role: Role;
      content: string | Array<TextContent | ImageContent>;
      tool_calls?: ToolCall[];
    };
    finish_reason: string | null;
  }>;
  usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
};

const MODEL = "claude-sonnet-4-20250514";

let anthropicClient: Anthropic | null = null;

function getClient(): Anthropic {
  if (!anthropicClient) {
    if (!ENV.anthropicApiKey) {
      throw new Error("ANTHROPIC_API_KEY is not configured");
    }
    anthropicClient = new Anthropic({
      apiKey: ENV.anthropicApiKey,
    });
  }
  return anthropicClient;
}

function extractTextContent(content: MessageContent | MessageContent[]): string {
  if (typeof content === "string") {
    return content;
  }
  if (Array.isArray(content)) {
    return content
      .map((part) => {
        if (typeof part === "string") return part;
        if (part.type === "text") return part.text;
        return "";
      })
      .join("\n");
  }
  if (content.type === "text") {
    return content.text;
  }
  return "";
}

function convertToAnthropicMessages(
  messages: Message[]
): { system: string | undefined; messages: Anthropic.MessageParam[] } {
  let systemPrompt: string | undefined;
  const anthropicMessages: Anthropic.MessageParam[] = [];

  for (const msg of messages) {
    if (msg.role === "system") {
      systemPrompt = extractTextContent(msg.content);
      continue;
    }

    const content = extractTextContent(msg.content);
    anthropicMessages.push({
      role: msg.role as "user" | "assistant",
      content,
    });
  }

  // Ensure messages alternate between user and assistant
  // If first message isn't user, prepend empty user message
  if (anthropicMessages.length > 0 && anthropicMessages[0].role !== "user") {
    anthropicMessages.unshift({ role: "user", content: "Continue." });
  }

  return { system: systemPrompt, messages: anthropicMessages };
}

function convertTools(tools: Tool[]): Anthropic.Tool[] {
  return tools.map((tool) => ({
    name: tool.function.name,
    description: tool.function.description || "",
    input_schema: {
      type: "object" as const,
      properties: (tool.function.parameters as any)?.properties || {},
      required: (tool.function.parameters as any)?.required || [],
    },
  }));
}

function getToolChoice(
  toolChoice: ToolChoice | undefined,
  tools: Tool[] | undefined
): Anthropic.ToolChoice | undefined {
  if (!toolChoice || !tools || tools.length === 0) return undefined;

  if (toolChoice === "none") return undefined;
  if (toolChoice === "auto") return { type: "auto" };
  if (toolChoice === "required") {
    if (tools.length === 1) {
      return { type: "tool", name: tools[0].function.name };
    }
    return { type: "any" };
  }
  if ("name" in toolChoice) {
    return { type: "tool", name: toolChoice.name };
  }
  if (toolChoice.type === "function") {
    return { type: "tool", name: toolChoice.function.name };
  }
  return undefined;
}

function getOutputSchema(params: InvokeParams): OutputSchema | undefined {
  if (params.outputSchema) return params.outputSchema;
  if (params.output_schema) return params.output_schema;
  if (params.responseFormat?.type === "json_schema") {
    return params.responseFormat.json_schema;
  }
  if (params.response_format?.type === "json_schema") {
    return params.response_format.json_schema;
  }
  return undefined;
}

export async function invokeLLM(params: InvokeParams): Promise<InvokeResult> {
  const client = getClient();
  const maxTokens = params.maxTokens || params.max_tokens || 8192;
  const { system, messages } = convertToAnthropicMessages(params.messages);

  const outputSchema = getOutputSchema(params);

  // If we have an output schema, use tool_use pattern for structured output
  if (outputSchema) {
    const structuredTool: Anthropic.Tool = {
      name: outputSchema.name,
      description: `Output structured data according to the schema for: ${outputSchema.name}`,
      input_schema: {
        type: "object" as const,
        ...(outputSchema.schema as object),
      },
    };

    const response = await client.messages.create({
      model: MODEL,
      max_tokens: maxTokens,
      system,
      messages,
      tools: [structuredTool],
      tool_choice: { type: "tool", name: outputSchema.name },
    });

    // Extract the tool use result
    const toolUseBlock = response.content.find(
      (block): block is Anthropic.ToolUseBlock => block.type === "tool_use"
    );

    const jsonContent = toolUseBlock
      ? JSON.stringify(toolUseBlock.input)
      : "{}";

    return {
      id: response.id,
      created: Date.now(),
      model: response.model,
      choices: [
        {
          index: 0,
          message: {
            role: "assistant",
            content: jsonContent,
          },
          finish_reason: response.stop_reason || "stop",
        },
      ],
      usage: {
        prompt_tokens: response.usage.input_tokens,
        completion_tokens: response.usage.output_tokens,
        total_tokens: response.usage.input_tokens + response.usage.output_tokens,
      },
    };
  }

  // If we have regular tools
  if (params.tools && params.tools.length > 0) {
    const anthropicTools = convertTools(params.tools);
    const toolChoice = getToolChoice(
      params.toolChoice || params.tool_choice,
      params.tools
    );

    const response = await client.messages.create({
      model: MODEL,
      max_tokens: maxTokens,
      system,
      messages,
      tools: anthropicTools,
      tool_choice: toolChoice,
    });

    // Convert tool use blocks to OpenAI-style tool_calls
    const toolCalls: ToolCall[] = [];
    let textContent = "";

    for (const block of response.content) {
      if (block.type === "text") {
        textContent += block.text;
      } else if (block.type === "tool_use") {
        toolCalls.push({
          id: block.id,
          type: "function",
          function: {
            name: block.name,
            arguments: JSON.stringify(block.input),
          },
        });
      }
    }

    return {
      id: response.id,
      created: Date.now(),
      model: response.model,
      choices: [
        {
          index: 0,
          message: {
            role: "assistant",
            content: textContent,
            tool_calls: toolCalls.length > 0 ? toolCalls : undefined,
          },
          finish_reason: response.stop_reason || "stop",
        },
      ],
      usage: {
        prompt_tokens: response.usage.input_tokens,
        completion_tokens: response.usage.output_tokens,
        total_tokens: response.usage.input_tokens + response.usage.output_tokens,
      },
    };
  }

  // Standard message without tools
  const response = await client.messages.create({
    model: MODEL,
    max_tokens: maxTokens,
    system,
    messages,
  });

  let textContent = "";
  for (const block of response.content) {
    if (block.type === "text") {
      textContent += block.text;
    }
  }

  return {
    id: response.id,
    created: Date.now(),
    model: response.model,
    choices: [
      {
        index: 0,
        message: {
          role: "assistant",
          content: textContent,
        },
        finish_reason: response.stop_reason || "stop",
      },
    ],
    usage: {
      prompt_tokens: response.usage.input_tokens,
      completion_tokens: response.usage.output_tokens,
      total_tokens: response.usage.input_tokens + response.usage.output_tokens,
    },
  };
}
