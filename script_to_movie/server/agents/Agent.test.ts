import { describe, it, expect, beforeEach, vi } from "vitest";
import { Agent } from "./Agent";
import { invokeLLM } from "../_core/llm";

// Mock the LLM
vi.mock("../_core/llm", () => ({
  invokeLLM: vi.fn(),
}));

describe("Agent", () => {
  let agent: Agent;

  beforeEach(() => {
    agent = new Agent("TestAgent", "You are a test agent");
  });

  it("should initialize with name and system prompt", () => {
    expect(agent.name).toBe("TestAgent");
    expect(agent.systemPrompt).toBe("You are a test agent");
  });

  it("should have empty reasoning initially", () => {
    expect(agent.reasoning).toBe("");
  });

  it("should have empty output initially", () => {
    expect(agent.output).toEqual({});
  });

  it("should have empty executionLog initially", () => {
    expect(agent.executionLog).toEqual([]);
  });

  it("should add messages to reasoning", () => {
    agent.think("First thought");
    expect(agent.reasoning).toContain("First thought");

    agent.think("Second thought");
    expect(agent.reasoning).toContain("Second thought");
  });

  it("should set output", () => {
    const testOutput = { result: "test", data: [1, 2, 3] };
    agent.setOutput(testOutput);
    expect(agent.output).toEqual(testOutput);
  });

  it("should log execution steps", () => {
    agent.log("Step 1", "info");
    agent.log("Error occurred", "error");

    expect(agent.executionLog).toHaveLength(2);
    expect(agent.executionLog[0]).toEqual({ message: "Step 1", level: "info" });
    expect(agent.executionLog[1]).toEqual({ message: "Error occurred", level: "error" });
  });

  it("should build messages array for LLM", async () => {
    agent.think("Analyzing input");
    agent.log("Processing started", "info");

    const mockResponse = {
      choices: [
        {
          message: {
            content: JSON.stringify({ analysis: "complete" }),
          },
        },
      ],
    };

    vi.mocked(invokeLLM).mockResolvedValueOnce(mockResponse);

    const result = await agent.callLLM("Test input");

    expect(result).toEqual({ analysis: "complete" });
    expect(vi.mocked(invokeLLM)).toHaveBeenCalled();
  });

  it("should handle LLM errors gracefully", async () => {
    vi.mocked(invokeLLM).mockRejectedValueOnce(new Error("LLM service error"));

    await expect(agent.callLLM("Test input")).rejects.toThrow("LLM service error");
  });

  it("should parse JSON responses from LLM", async () => {
    const mockResponse = {
      choices: [
        {
          message: {
            content: JSON.stringify({
              scenes: [{ id: 1, title: "Scene 1" }],
              characters: [{ name: "Alice" }],
            }),
          },
        },
      ],
    };

    vi.mocked(invokeLLM).mockResolvedValueOnce(mockResponse);

    const result = await agent.callLLM("Extract scenes");

    expect(result).toHaveProperty("scenes");
    expect(result).toHaveProperty("characters");
    expect(result.scenes).toHaveLength(1);
  });

  it("should accumulate reasoning across multiple thinks", () => {
    agent.think("Step 1: Read input");
    agent.think("Step 2: Analyze structure");
    agent.think("Step 3: Extract data");

    const reasoning = agent.reasoning;
    expect(reasoning).toContain("Step 1");
    expect(reasoning).toContain("Step 2");
    expect(reasoning).toContain("Step 3");
  });

  it("should handle complex reasoning chains", async () => {
    agent.think("Analyzing screenplay structure");
    agent.think("Identifying main characters");
    agent.think("Extracting key scenes");

    const mockResponse = {
      choices: [
        {
          message: {
            content: JSON.stringify({
              sceneCount: 5,
              characterCount: 3,
              duration: 120,
            }),
          },
        },
      ],
    };

    vi.mocked(invokeLLM).mockResolvedValueOnce(mockResponse);

    const result = await agent.callLLM("Summarize analysis");

    expect(result.sceneCount).toBe(5);
    expect(result.characterCount).toBe(3);
  });
});
