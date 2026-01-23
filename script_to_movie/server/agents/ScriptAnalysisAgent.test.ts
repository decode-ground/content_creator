import { describe, it, expect, beforeEach, vi } from "vitest";
import { ScriptAnalysisAgent } from "./ScriptAnalysisAgent";
import { invokeLLM } from "../_core/llm";

vi.mock("../_core/llm", () => ({
  invokeLLM: vi.fn(),
}));

describe("ScriptAnalysisAgent", () => {
  let agent: ScriptAnalysisAgent;

  beforeEach(() => {
    agent = new ScriptAnalysisAgent();
  });

  it("should initialize as ScriptAnalysisAgent", () => {
    expect(agent.name).toBe("ScriptAnalysisAgent");
  });

  it("should analyze screenplay structure", async () => {
    const screenplay = `
      INT. COFFEE SHOP - MORNING
      
      ALICE sits at a table. BOB enters.
      
      ALICE
      Hey Bob!
      
      BOB
      Hi Alice!
      
      INT. PARK - AFTERNOON
      
      Alice and Bob walk together.
    `;

    const mockResponse = {
      choices: [
        {
          message: {
            content: JSON.stringify({
              title: "Coffee Meeting",
              summary: "Two friends meet at a coffee shop and later walk in the park",
              scenes: [
                {
                  sceneNumber: 1,
                  title: "Coffee Shop Meeting",
                  setting: "INT. COFFEE SHOP - MORNING",
                  characters: ["Alice", "Bob"],
                  description: "Alice and Bob meet at a coffee shop",
                },
                {
                  sceneNumber: 2,
                  title: "Park Walk",
                  setting: "INT. PARK - AFTERNOON",
                  characters: ["Alice", "Bob"],
                  description: "Alice and Bob walk together in the park",
                },
              ],
              characters: [
                {
                  name: "Alice",
                  description: "A friendly woman",
                  visualDescription: "Woman with brown hair",
                },
                {
                  name: "Bob",
                  description: "Alice's friend",
                  visualDescription: "Man with blonde hair",
                },
              ],
              settings: [
                {
                  name: "Coffee Shop",
                  description: "A cozy coffee shop",
                  visualDescription: "Modern cafe with wooden tables",
                },
                {
                  name: "Park",
                  description: "A peaceful park",
                  visualDescription: "Green park with trees and benches",
                },
              ],
              totalDuration: 120,
              trailerScenes: [1, 2],
            }),
          },
        },
      ],
    };

    vi.mocked(invokeLLM).mockResolvedValueOnce(mockResponse);

    const result = await agent.analyzeScreenplay(screenplay);

    expect(result).toHaveProperty("title");
    expect(result).toHaveProperty("scenes");
    expect(result).toHaveProperty("characters");
    expect(result).toHaveProperty("settings");
    expect(result.scenes).toHaveLength(2);
    expect(result.characters).toHaveLength(2);
  });

  it("should extract character descriptions", async () => {
    const screenplay = `
      ALICE is a 30-year-old software engineer with a passion for art.
      BOB is a 32-year-old musician and Alice's best friend.
    `;

    const mockResponse = {
      choices: [
        {
          message: {
            content: JSON.stringify({
              characters: [
                {
                  name: "Alice",
                  description: "30-year-old software engineer with a passion for art",
                  visualDescription: "Professional woman, artistic style",
                },
                {
                  name: "Bob",
                  description: "32-year-old musician and Alice's best friend",
                  visualDescription: "Musician, casual style",
                },
              ],
            }),
          },
        },
      ],
    };

    vi.mocked(invokeLLM).mockResolvedValueOnce(mockResponse);

    const result = await agent.analyzeScreenplay(screenplay);

    expect(result.characters).toHaveLength(2);
    expect(result.characters[0].name).toBe("Alice");
    expect(result.characters[0].description).toContain("software engineer");
  });

  it("should identify scene locations", async () => {
    const screenplay = `
      INT. APARTMENT - NIGHT
      INT. STREET - DAY
      EXT. BEACH - SUNSET
    `;

    const mockResponse = {
      choices: [
        {
          message: {
            content: JSON.stringify({
              settings: [
                {
                  name: "Apartment",
                  description: "A residential apartment",
                  visualDescription: "Modern apartment interior",
                },
                {
                  name: "Street",
                  description: "An urban street",
                  visualDescription: "City street with buildings",
                },
                {
                  name: "Beach",
                  description: "A sandy beach",
                  visualDescription: "Beautiful beach at sunset",
                },
              ],
            }),
          },
        },
      ],
    };

    vi.mocked(invokeLLM).mockResolvedValueOnce(mockResponse);

    const result = await agent.analyzeScreenplay(screenplay);

    expect(result.settings).toHaveLength(3);
    expect(result.settings.map((s) => s.name)).toContain("Apartment");
    expect(result.settings.map((s) => s.name)).toContain("Beach");
  });

  it("should calculate total screenplay duration", async () => {
    const screenplay = "A screenplay with multiple scenes";

    const mockResponse = {
      choices: [
        {
          message: {
            content: JSON.stringify({
              totalDuration: 90,
              scenes: [
                { sceneNumber: 1, duration: 30 },
                { sceneNumber: 2, duration: 30 },
                { sceneNumber: 3, duration: 30 },
              ],
            }),
          },
        },
      ],
    };

    vi.mocked(invokeLLM).mockResolvedValueOnce(mockResponse);

    const result = await agent.analyzeScreenplay(screenplay);

    expect(result.totalDuration).toBe(90);
  });

  it("should identify trailer scenes", async () => {
    const screenplay = "A screenplay with key scenes";

    const mockResponse = {
      choices: [
        {
          message: {
            content: JSON.stringify({
              trailerScenes: [1, 3, 5],
              scenes: [
                { sceneNumber: 1, isKeyScene: true },
                { sceneNumber: 2, isKeyScene: false },
                { sceneNumber: 3, isKeyScene: true },
              ],
            }),
          },
        },
      ],
    };

    vi.mocked(invokeLLM).mockResolvedValueOnce(mockResponse);

    const result = await agent.analyzeScreenplay(screenplay);

    expect(result.trailerScenes).toContain(1);
    expect(result.trailerScenes).toContain(3);
    expect(result.trailerScenes).toContain(5);
  });

  it("should log analysis steps", async () => {
    const screenplay = "Test screenplay";

    const mockResponse = {
      choices: [
        {
          message: {
            content: JSON.stringify({
              scenes: [],
              characters: [],
              settings: [],
            }),
          },
        },
      ],
    };

    vi.mocked(invokeLLM).mockResolvedValueOnce(mockResponse);

    await agent.analyzeScreenplay(screenplay);

    expect(agent.executionLog.length).toBeGreaterThan(0);
    expect(agent.executionLog.some((log) => log.level === "info")).toBe(true);
  });

  it("should handle empty screenplay", async () => {
    const mockResponse = {
      choices: [
        {
          message: {
            content: JSON.stringify({
              error: "Screenplay is empty",
              scenes: [],
              characters: [],
              settings: [],
            }),
          },
        },
      ],
    };

    vi.mocked(invokeLLM).mockResolvedValueOnce(mockResponse);

    const result = await agent.analyzeScreenplay("");

    expect(result).toBeDefined();
  });
});
