import { invokeLLM } from "../_core/llm";
import { PromptOptimizationResult, PromptTemplate } from "./types";

/**
 * PromptOptimizer - Refines and optimizes prompts for better LLM outputs
 * Uses meta-prompting to improve prompt quality iteratively
 */
export class PromptOptimizer {
  /**
   * Optimize a prompt for better results
   */
  static async optimizePrompt(
    originalPrompt: string,
    context: string,
    targetQuality: "accuracy" | "creativity" | "structure" = "accuracy"
  ): Promise<PromptOptimizationResult> {
    const optimizationPrompt = this.buildOptimizationPrompt(originalPrompt, context, targetQuality);

    const response = await invokeLLM({
      messages: [
        {
          role: "system",
          content: `You are an expert prompt engineer specializing in optimizing LLM prompts for better outputs.
Your task is to improve prompts by making them more specific, clear, and effective.
Consider clarity, specificity, structure, and the target quality level.`,
        },
        {
          role: "user",
          content: optimizationPrompt,
        },
      ],
    });

    const content = response.choices[0]?.message.content;
    if (!content || typeof content !== "string") {
      throw new Error("Failed to optimize prompt");
    }

    // Parse the optimization response
    const optimizedPrompt = this.extractOptimizedPrompt(content);
    const improvements = this.extractImprovements(content);
    const score = this.calculatePromptScore(optimizedPrompt);

    return {
      originalPrompt,
      optimizedPrompt,
      improvements,
      score,
    };
  }

  /**
   * Build a meta-prompt for prompt optimization
   */
  private static buildOptimizationPrompt(
    prompt: string,
    context: string,
    targetQuality: string
  ): string {
    return `Please optimize this prompt for better LLM outputs:

ORIGINAL PROMPT:
${prompt}

CONTEXT:
${context}

TARGET QUALITY: ${targetQuality}

Analyze the prompt and provide:
1. OPTIMIZED_PROMPT: [Improved version of the prompt]
2. IMPROVEMENTS: [List of specific improvements made]
3. REASONING: [Why these changes improve the prompt]

Focus on:
- Clarity and specificity
- Structured output format
- Clear instructions and examples
- Reducing ambiguity
- Aligning with target quality level`;
  }

  /**
   * Extract optimized prompt from response
   */
  private static extractOptimizedPrompt(response: string): string {
    const match = response.match(/OPTIMIZED_PROMPT:\s*([\s\S]*?)(?=\d\.|IMPROVEMENTS:|$)/i);
    return match ? match[1].trim() : response;
  }

  /**
   * Extract improvements from response
   */
  private static extractImprovements(response: string): string[] {
    const match = response.match(/IMPROVEMENTS:\s*([\s\S]*?)(?=\d\.|REASONING:|$)/i);
    if (!match) return [];

    return match[1]
      .split("\n")
      .filter((line) => line.trim())
      .map((line) => line.replace(/^[-•*]\s*/, "").trim());
  }

  /**
   * Calculate a quality score for the prompt (0-100)
   */
  private static calculatePromptScore(prompt: string): number {
    let score = 50; // Base score

    // Check for clarity indicators
    if (prompt.includes("step") || prompt.includes("first") || prompt.includes("then")) score += 10;
    if (prompt.includes("example") || prompt.includes("e.g.")) score += 10;
    if (prompt.includes("format") || prompt.includes("structure")) score += 10;
    if (prompt.includes("constraint") || prompt.includes("avoid")) score += 5;
    if (prompt.includes("reason") || prompt.includes("explain")) score += 5;

    // Penalize for vagueness
    if (prompt.includes("something") || prompt.includes("anything")) score -= 5;
    if (prompt.length < 50) score -= 10;

    return Math.min(100, Math.max(0, score));
  }

  /**
   * Create a prompt template for reuse
   */
  static createTemplate(
    name: string,
    template: string,
    variables: string[],
    examples?: Array<{ input: Record<string, string>; output: string }>
  ): PromptTemplate {
    return {
      name,
      template,
      variables,
      examples,
    };
  }

  /**
   * Render a template with variables
   */
  static renderTemplate(template: PromptTemplate, variables: Record<string, string>): string {
    let result = template.template;

    for (const [key, value] of Object.entries(variables)) {
      result = result.replace(new RegExp(`\\{${key}\\}`, "g"), value);
    }

    // Add examples if available
    if (template.examples && template.examples.length > 0) {
      const examplesText = template.examples
        .map((ex) => `Input: ${JSON.stringify(ex.input)}\nOutput: ${ex.output}`)
        .join("\n\n");

      result = result.replace("{examples}", examplesText);
    }

    return result;
  }

  /**
   * Create few-shot examples for better prompt performance
   */
  static createFewShotPrompt(
    basePrompt: string,
    examples: Array<{ input: string; output: string }>
  ): string {
    const examplesText = examples
      .map(
        (ex, i) => `
Example ${i + 1}:
INPUT: ${ex.input}
OUTPUT: ${ex.output}`
      )
      .join("\n");

    return `${basePrompt}

Here are some examples to guide your response:
${examplesText}

Now, please provide your response following the same format and quality as the examples above.`;
  }
}

/**
 * Pre-built prompt templates for common tasks
 */
export const PROMPT_TEMPLATES = {
  sceneAnalysis: PromptOptimizer.createTemplate(
    "scene_analysis",
    `Analyze this screenplay scene:

SCENE:
{scene_content}

Please identify:
1. Main action/conflict
2. Characters involved
3. Setting/location
4. Emotional beats
5. Visual opportunities

{examples}`,
    ["scene_content", "examples"]
  ),

  characterDescription: PromptOptimizer.createTemplate(
    "character_description",
    `Create a detailed character description for visual generation:

CHARACTER NAME: {character_name}
BACKGROUND: {character_background}
ROLE: {character_role}

Generate a visual description that includes:
1. Physical appearance
2. Distinctive features
3. Clothing style
4. Mannerisms
5. Overall impression

{examples}`,
    ["character_name", "character_background", "character_role", "examples"]
  ),

  imageGeneration: PromptOptimizer.createTemplate(
    "image_generation",
    `Create a cinematic image prompt:

SCENE: {scene_description}
SETTING: {setting_description}
CHARACTERS: {characters_description}
MOOD: {mood}

Generate a detailed image prompt that includes:
1. Composition and framing
2. Lighting and atmosphere
3. Character positioning
4. Visual style
5. Technical quality specifications

{examples}`,
    ["scene_description", "setting_description", "characters_description", "mood", "examples"]
  ),

  videoPrompt: PromptOptimizer.createTemplate(
    "video_generation",
    `Create a video generation prompt:

SCENE: {scene_description}
DURATION: {duration}
CHARACTERS: {characters_description}
SETTING: {setting_description}

Generate a detailed video prompt including:
1. Camera movements
2. Character actions and interactions
3. Transitions and pacing
4. Audio/music suggestions
5. Visual effects (if any)

{examples}`,
    ["scene_description", "duration", "characters_description", "setting_description", "examples"]
  ),
};
