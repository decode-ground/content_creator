import { describe, it, expect, beforeEach, vi } from "vitest";
import { PromptOptimizer } from "./PromptOptimizer";
import { invokeLLM } from "../_core/llm";

vi.mock("../_core/llm", () => ({
  invokeLLM: vi.fn(),
}));

describe("PromptOptimizer", () => {
  let optimizer: PromptOptimizer;

  beforeEach(() => {
    optimizer = new PromptOptimizer();
  });

  it("should initialize with default templates", () => {
    expect(optimizer.templates).toBeDefined();
    expect(Object.keys(optimizer.templates).length).toBeGreaterThan(0);
  });

  it("should have script analysis template", () => {
    expect(optimizer.templates.scriptAnalysis).toBeDefined();
  });

  it("should have storyboard prompt template", () => {
    expect(optimizer.templates.storyboardPrompt).toBeDefined();
  });

  it("should have video prompt template", () => {
    expect(optimizer.templates.videoPrompt).toBeDefined();
  });

  it("should generate few-shot examples", async () => {
    const mockResponse = {
      choices: [
        {
          message: {
            content: JSON.stringify({
              examples: [
                {
                  input: "INT. OFFICE - DAY",
                  output: "A professional office setting with desks and computers",
                },
                {
                  input: "EXT. BEACH - SUNSET",
                  output: "A beautiful beach scene with golden sunset light",
                },
              ],
            }),
          },
        },
      ],
    };

    vi.mocked(invokeLLM).mockResolvedValueOnce(mockResponse);

    const examples = await optimizer.generateExamples("scene_description", 2);

    expect(examples).toHaveLength(2);
    expect(examples[0]).toHaveProperty("input");
    expect(examples[0]).toHaveProperty("output");
  });

  it("should optimize prompt for quality", async () => {
    const originalPrompt = "Describe this scene";

    const mockResponse = {
      choices: [
        {
          message: {
            content: JSON.stringify({
              optimizedPrompt: "Provide a detailed, vivid description of this scene including lighting, mood, and visual elements",
              qualityScore: 85,
              improvements: ["Added specificity", "Included visual elements"],
            }),
          },
        },
      ],
    };

    vi.mocked(invokeLLM).mockResolvedValueOnce(mockResponse);

    const result = await optimizer.optimizePrompt(originalPrompt, "scene_description");

    expect(result).toHaveProperty("optimizedPrompt");
    expect(result).toHaveProperty("qualityScore");
    expect(result.qualityScore).toBeGreaterThan(0);
    expect(result.qualityScore).toBeLessThanOrEqual(100);
  });

  it("should score prompt quality", async () => {
    const prompt = "Analyze the screenplay structure and extract all scenes";

    const mockResponse = {
      choices: [
        {
          message: {
            content: JSON.stringify({
              score: 78,
              feedback: "Good specificity, could be more structured",
              suggestions: ["Add output format requirements", "Specify character extraction"],
            }),
          },
        },
      ],
    };

    vi.mocked(invokeLLM).mockResolvedValueOnce(mockResponse);

    const result = await optimizer.scorePrompt(prompt);

    expect(result).toHaveProperty("score");
    expect(result.score).toBeGreaterThanOrEqual(0);
    expect(result.score).toBeLessThanOrEqual(100);
  });

  it("should refine prompt based on output quality", async () => {
    const prompt = "Extract scenes from screenplay";
    const output = { scenes: [] }; // Poor output - no scenes extracted

    const mockResponse = {
      choices: [
        {
          message: {
            content: JSON.stringify({
              refinedPrompt: "Carefully analyze the screenplay and extract ALL scenes, including scene number, title, setting, characters, and description",
              reason: "Original prompt was too vague, resulted in empty output",
            }),
          },
        },
      ],
    };

    vi.mocked(invokeLLM).mockResolvedValueOnce(mockResponse);

    const result = await optimizer.refinePrompt(prompt, output);

    expect(result).toHaveProperty("refinedPrompt");
    expect(result.refinedPrompt).not.toBe(prompt);
  });

  it("should generate prompt variants", async () => {
    const basePrompt = "Analyze screenplay structure";

    const mockResponse = {
      choices: [
        {
          message: {
            content: JSON.stringify({
              variants: [
                "Break down the screenplay structure into components",
                "Examine and categorize screenplay elements",
                "Decompose screenplay into structural parts",
              ],
            }),
          },
        },
      ],
    };

    vi.mocked(invokeLLM).mockResolvedValueOnce(mockResponse);

    const variants = await optimizer.generateVariants(basePrompt, 3);

    expect(variants).toHaveLength(3);
    expect(variants[0]).not.toBe(basePrompt);
  });

  it("should combine multiple prompts for complex tasks", async () => {
    const prompts = [
      "Analyze screenplay structure",
      "Extract character descriptions",
      "Identify key scenes",
    ];

    const mockResponse = {
      choices: [
        {
          message: {
            content: JSON.stringify({
              combinedPrompt: "Analyze the screenplay by: 1) Breaking down its structure, 2) Extracting detailed character descriptions, 3) Identifying key scenes that drive the narrative",
            }),
          },
        },
      ],
    };

    vi.mocked(invokeLLM).mockResolvedValueOnce(mockResponse);

    const result = await optimizer.combinePrompts(prompts);

    expect(result).toBeDefined();
    expect(result.length).toBeGreaterThan(0);
  });

  it("should track optimization history", async () => {
    const mockResponse = {
      choices: [
        {
          message: {
            content: JSON.stringify({
              score: 85,
            }),
          },
        },
      ],
    };

    vi.mocked(invokeLLM).mockResolvedValueOnce(mockResponse);

    const initialCount = optimizer.optimizationHistory.length;

    await optimizer.scorePrompt("Test prompt");

    expect(optimizer.optimizationHistory.length).toBeGreaterThan(initialCount);
  });

  it("should provide template with variables", () => {
    const template = optimizer.templates.scriptAnalysis;
    expect(template).toContain("{screenplay}");
  });

  it("should fill template variables", () => {
    const template = "Analyze this screenplay: {screenplay}";
    const screenplay = "INT. OFFICE - DAY";

    const filled = optimizer.fillTemplate(template, { screenplay });

    expect(filled).toContain("INT. OFFICE - DAY");
    expect(filled).not.toContain("{screenplay}");
  });
});
