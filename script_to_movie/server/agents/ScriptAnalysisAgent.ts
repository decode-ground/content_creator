import { Agent } from "./Agent";
import { AgentConfig, AgentContext, AgentResult } from "./types";

export interface ScriptAnalysisInput {
  scriptContent: string;
  projectTitle: string;
}

export interface ScriptAnalysisOutput {
  title: string;
  summary: string;
  sceneCount: number;
  characterCount: number;
  settingCount: number;
  estimatedDuration: number;
  narrativeArc: string;
  themes: string[];
  trailerKeyScenes: number[];
}

/**
 * ScriptAnalysisAgent - First agent in the pipeline
 * Performs high-level analysis of the screenplay to understand structure and narrative
 * Uses chain-of-thought reasoning to break down the analysis into steps
 */
export class ScriptAnalysisAgent extends Agent {
  constructor(context: AgentContext) {
    const config: AgentConfig = {
      name: "ScriptAnalysisAgent",
      description: "Analyzes screenplay structure, narrative arc, and key elements",
      systemPrompt: `You are an expert screenplay analyst with deep knowledge of film structure, narrative theory, and character development.
Your role is to analyze screenplays and extract key structural elements.
When analyzing, consider:
1. Three-act structure and narrative arc
2. Character introductions and development
3. Setting/location changes
4. Scene transitions and pacing
5. Thematic elements
6. Key turning points for trailer material`,
    };
    super(config, context);
  }

  async execute(input: ScriptAnalysisInput): Promise<AgentResult<ScriptAnalysisOutput>> {
    const startTime = Date.now();

    try {
      // Step 1: Initial structure analysis
      const structureAnalysis = await this.analyzeStructure(input.scriptContent);

      // Step 2: Extract narrative elements
      const narrativeElements = await this.extractNarrativeElements(input.scriptContent);

      // Step 3: Identify key scenes for trailer
      const trailerScenes = await this.identifyTrailerScenes(input.scriptContent, structureAnalysis);

      // Step 4: Synthesize findings
      const output: ScriptAnalysisOutput = {
        title: input.projectTitle,
        summary: structureAnalysis.summary,
        sceneCount: structureAnalysis.sceneCount,
        characterCount: narrativeElements.characterCount,
        settingCount: narrativeElements.settingCount,
        estimatedDuration: structureAnalysis.estimatedDuration,
        narrativeArc: structureAnalysis.narrativeArc,
        themes: narrativeElements.themes,
        trailerKeyScenes: trailerScenes,
      };

      const duration = Date.now() - startTime;
      this.logExecution(input, output, structureAnalysis.reasoning, duration);

      return this.success(
        output,
        `Analyzed screenplay structure: ${structureAnalysis.sceneCount} scenes, ${narrativeElements.characterCount} characters`,
        "SceneBreakdownAgent"
      );
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Unknown error";
      return this.failure(errorMessage, "Failed during script analysis");
    }
  }

  /**
   * Step 1: Analyze screenplay structure using chain-of-thought
   */
  private async analyzeStructure(scriptContent: string): Promise<{
    summary: string;
    sceneCount: number;
    estimatedDuration: number;
    narrativeArc: string;
    reasoning: string;
  }> {
    const { reasoning, conclusion } = await this.reasonWithLLM(`
Analyze the structure of this screenplay:

${scriptContent.substring(0, 5000)}...

Please analyze:
1. How many distinct scenes are there?
2. What is the narrative arc (setup, confrontation, resolution)?
3. What is the estimated total duration?
4. What are the major plot points?
5. What is the overall story summary?
`);

    // Parse the conclusion to extract structured data
    const sceneCountMatch = conclusion.match(/(\d+)\s*(?:scenes?|scene)/i);
    const durationMatch = conclusion.match(/(\d+)\s*(?:minutes?|mins?)/i);

    return {
      summary: conclusion.substring(0, 500),
      sceneCount: sceneCountMatch ? parseInt(sceneCountMatch[1]) : 5,
      estimatedDuration: durationMatch ? parseInt(durationMatch[1]) * 60 : 300,
      narrativeArc: conclusion.includes("three-act") ? "Three-Act Structure" : "Non-Linear",
      reasoning,
    };
  }

  /**
   * Step 2: Extract narrative elements (characters, settings, themes)
   */
  private async extractNarrativeElements(scriptContent: string): Promise<{
    characterCount: number;
    settingCount: number;
    themes: string[];
  }> {
    const schema = {
      type: "object",
      properties: {
        characterCount: { type: "number", description: "Number of distinct characters" },
        settingCount: { type: "number", description: "Number of distinct settings/locations" },
        themes: {
          type: "array",
          items: { type: "string" },
          description: "Major themes in the story",
        },
      },
      required: ["characterCount", "settingCount", "themes"],
      additionalProperties: false,
    };

    const result = await this.structuredLLMCall<{
      characterCount: number;
      settingCount: number;
      themes: string[];
    }>(
      `Extract narrative elements from this screenplay excerpt:

${scriptContent.substring(0, 3000)}...

Identify:
1. How many distinct characters appear?
2. How many distinct settings/locations?
3. What are the main themes?`,
      schema
    );

    return result;
  }

  /**
   * Step 3: Identify key scenes for trailer
   */
  private async identifyTrailerScenes(
    scriptContent: string,
    structureAnalysis: any
  ): Promise<number[]> {
    const { conclusion } = await this.reasonWithLLM(`
Based on the screenplay structure with ${structureAnalysis.sceneCount} scenes and narrative arc of ${structureAnalysis.narrativeArc},
which scenes would be most impactful for a movie trailer?

Consider:
1. Opening hook (scene that grabs attention)
2. Major turning points
3. Climactic moments
4. Character introductions
5. Visual spectacle or emotional peaks

Provide 3-5 scene numbers that would make the best trailer.`);

    // Extract scene numbers from conclusion
    const sceneNumbers = conclusion
      .match(/\d+/g)
      ?.map((n) => parseInt(n))
      .filter((n) => n <= structureAnalysis.sceneCount)
      .slice(0, 5) || [1, Math.floor(structureAnalysis.sceneCount / 2), structureAnalysis.sceneCount];

    return sceneNumbers;
  }
}
