import { invokeLLM } from "./_core/llm";

export interface SceneBreakdown {
  sceneNumber: number;
  title: string;
  description: string;
  setting: string;
  characters: string[];
  duration: number;
  order: number;
}

export interface CharacterProfile {
  name: string;
  description: string;
  visualDescription: string;
  appearances: number;
}

export interface SettingProfile {
  name: string;
  description: string;
  visualDescription: string;
  appearances: number;
}

export interface ScriptAnalysisResult {
  title: string;
  summary: string;
  scenes: SceneBreakdown[];
  characters: CharacterProfile[];
  settings: SettingProfile[];
  totalDuration: number;
  trailerScenes: number[]; // Indices of scenes to include in trailer
}

/**
 * Analyzes a screenplay script and extracts structured information
 */
export async function analyzeScript(scriptContent: string): Promise<ScriptAnalysisResult> {
  const response = await invokeLLM({
    messages: [
      {
        role: "system",
        content: `You are a professional screenplay analyst. Analyze the provided screenplay and extract:
1. A concise title
2. A brief summary
3. Individual scenes with descriptions
4. Character profiles with visual descriptions
5. Setting/location profiles with visual descriptions
6. Estimated duration for each scene
7. Key scenes for a trailer that represent the entire story

Respond in JSON format with the following structure:
{
  "title": "string",
  "summary": "string (2-3 sentences)",
  "scenes": [
    {
      "sceneNumber": number,
      "title": "string",
      "description": "string (detailed scene description)",
      "setting": "string (location name)",
      "characters": ["character names"],
      "duration": number (estimated seconds)
    }
  ],
  "characters": [
    {
      "name": "string",
      "description": "string (character background and personality)",
      "visualDescription": "string (physical appearance for image generation)",
      "appearances": number
    }
  ],
  "settings": [
    {
      "name": "string",
      "description": "string (detailed setting description)",
      "visualDescription": "string (visual style and atmosphere for image generation)",
      "appearances": number
    }
  ],
  "totalDuration": number (total estimated seconds),
  "trailerScenes": [number] (scene indices to include in trailer - aim for 3-5 key scenes)
}`,
      },
      {
        role: "user",
        content: `Please analyze this screenplay:\n\n${scriptContent}`,
      },
    ],
    response_format: {
      type: "json_schema",
      json_schema: {
        name: "script_analysis",
        strict: true,
        schema: {
          type: "object",
          properties: {
            title: { type: "string" },
            summary: { type: "string" },
            scenes: {
              type: "array",
              items: {
                type: "object",
                properties: {
                  sceneNumber: { type: "number" },
                  title: { type: "string" },
                  description: { type: "string" },
                  setting: { type: "string" },
                  characters: {
                    type: "array",
                    items: { type: "string" },
                  },
                  duration: { type: "number" },
                },
                required: ["sceneNumber", "title", "description", "setting", "characters", "duration"],
                additionalProperties: false,
              },
            },
            characters: {
              type: "array",
              items: {
                type: "object",
                properties: {
                  name: { type: "string" },
                  description: { type: "string" },
                  visualDescription: { type: "string" },
                  appearances: { type: "number" },
                },
                required: ["name", "description", "visualDescription", "appearances"],
                additionalProperties: false,
              },
            },
            settings: {
              type: "array",
              items: {
                type: "object",
                properties: {
                  name: { type: "string" },
                  description: { type: "string" },
                  visualDescription: { type: "string" },
                  appearances: { type: "number" },
                },
                required: ["name", "description", "visualDescription", "appearances"],
                additionalProperties: false,
              },
            },
            totalDuration: { type: "number" },
            trailerScenes: {
              type: "array",
              items: { type: "number" },
            },
          },
          required: ["title", "summary", "scenes", "characters", "settings", "totalDuration", "trailerScenes"],
          additionalProperties: false,
        },
      },
    },
  });

  const content = response.choices[0]?.message.content;
  if (!content || typeof content !== "string") {
    throw new Error("Failed to get response from LLM");
  }

  const parsed = JSON.parse(content);
  
  // Ensure scenes have order field
  const scenesWithOrder = parsed.scenes.map((scene: any, index: number) => ({
    ...scene,
    order: index,
  }));

  return {
    ...parsed,
    scenes: scenesWithOrder,
  } as ScriptAnalysisResult;
}

/**
 * Generates a detailed prompt for storyboard image generation
 */
export function generateStoryboardPrompt(
  sceneDescription: string,
  setting: SettingProfile,
  characters: CharacterProfile[],
  visualStyle: string = "cinematic"
): string {
  const characterDescriptions = characters
    .map((c) => `${c.name}: ${c.visualDescription}`)
    .join(", ");

  return `Create a cinematic still frame for a film scene with the following details:

Scene: ${sceneDescription}

Setting: ${setting.name}
${setting.visualDescription}

Characters in scene:
${characterDescriptions}

Visual Style: ${visualStyle}, professional cinematography, high production value
Composition: Wide shot establishing the scene with characters and environment clearly visible
Lighting: Professional film lighting, dramatic and atmospheric
Quality: 4K, highly detailed, photorealistic

Generate a single, cohesive image that captures the essence of this scene.`;
}

/**
 * Generates an optimized prompt for video generation
 */
export function generateVideoPrompt(
  sceneDescription: string,
  setting: SettingProfile,
  characters: CharacterProfile[],
  duration: number = 5
): string {
  const characterDescriptions = characters
    .map((c) => `${c.name}: ${c.visualDescription}`)
    .join("; ");

  const durationText = duration <= 5 ? "short" : duration <= 15 ? "medium" : "long";

  return `Create a ${durationText} cinematic video (${duration} seconds) for a film scene:

Scene Description: ${sceneDescription}

Setting: ${setting.name}
Visual Style: ${setting.visualDescription}

Characters: ${characterDescriptions}

Requirements:
- Professional cinematography with smooth camera movements
- Natural lighting and atmospheric effects
- Characters should move naturally and realistically
- Audio: Include appropriate ambient sounds and subtle background music
- Pacing: Appropriate for a ${durationText} duration scene
- Quality: High production value, cinematic quality
- Consistency: Maintain visual consistency with the established setting and character appearances

Create a cohesive video that tells this part of the story effectively.`;
}

/**
 * Validates scene consistency across the script
 */
export function validateSceneConsistency(
  scenes: SceneBreakdown[],
  characters: CharacterProfile[],
  settings: SettingProfile[]
): { isValid: boolean; issues: string[] } {
  const issues: string[] = [];

  // Check if all characters in scenes exist in character list
  const characterNames = new Set(characters.map((c) => c.name));
  scenes.forEach((scene) => {
    scene.characters.forEach((char) => {
      if (!characterNames.has(char)) {
        issues.push(`Scene ${scene.sceneNumber}: Character "${char}" not found in character list`);
      }
    });
  });

  // Check if all settings in scenes exist in settings list
  const settingNames = new Set(settings.map((s) => s.name));
  scenes.forEach((scene) => {
    if (!settingNames.has(scene.setting)) {
      issues.push(`Scene ${scene.sceneNumber}: Setting "${scene.setting}" not found in settings list`);
    }
  });

  // Check for reasonable scene durations
  scenes.forEach((scene) => {
    if (scene.duration < 5 || scene.duration > 300) {
      issues.push(`Scene ${scene.sceneNumber}: Duration ${scene.duration}s seems unreasonable (expected 5-300s)`);
    }
  });

  return {
    isValid: issues.length === 0,
    issues,
  };
}
