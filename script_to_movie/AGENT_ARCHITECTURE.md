# Script-to-Movie: Agentic Workflow Architecture

## Overview

The Script-to-Movie platform uses a **multi-agent orchestration system** where specialized AI agents work together in a coordinated pipeline to transform screenplays into complete video productions. Each agent is responsible for a specific task and uses advanced prompting techniques to achieve high-quality outputs.

## Architecture Principles

### 1. **Agent-Based Decomposition**
The complex task of script-to-movie generation is broken down into specialized agents, each handling a specific domain:
- Script analysis and structure
- Scene breakdown and description
- Character consistency management
- Setting/location management
- Image prompt optimization
- Video prompt generation
- Video synthesis
- Video assembly

### 2. **Chain-of-Thought Reasoning**
Each agent uses chain-of-thought prompting to break down complex tasks into logical steps:
```
REASONING: [Step-by-step analysis]
CONCLUSION: [Final output]
```

### 3. **Prompt Engineering & Optimization**
The `PromptOptimizer` class refines prompts iteratively using meta-prompting to improve LLM outputs:
- Clarity and specificity enhancement
- Few-shot example generation
- Template-based prompt construction
- Quality scoring and validation

### 4. **Workflow Orchestration**
The `WorkflowOrchestrator` coordinates agent execution:
- Sequential agent handoffs
- State management and checkpointing
- Error recovery and retry logic
- Progress tracking and reporting

## Agent System

### Base Agent Class

All agents inherit from the `Agent` base class, which provides:

```typescript
abstract class Agent {
  // Core execution method
  abstract execute(input: any): Promise<AgentResult>;
  
  // Reasoning with chain-of-thought
  protected reasonWithLLM(userMessage: string): Promise<{ reasoning, conclusion }>;
  
  // Structured JSON outputs
  protected structuredLLMCall<T>(userMessage: string, schema): Promise<T>;
  
  // Tool usage
  protected useTool(toolName: string, input: any): Promise<any>;
}
```

### Agent Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                    Script Input (Screenplay)                     │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
        ┌────────────────────────────────────┐
        │   ScriptAnalysisAgent              │
        │ - Analyze structure                │
        │ - Extract narrative arc            │
        │ - Identify key scenes              │
        └────────────┬───────────────────────┘
                     │
                     ▼
        ┌────────────────────────────────────┐
        │   SceneBreakdownAgent              │
        │ - Break into individual scenes     │
        │ - Generate descriptions            │
        │ - Estimate durations               │
        └────────────┬───────────────────────┘
                     │
        ┌────────────┴──────────────┐
        │                           │
        ▼                           ▼
┌──────────────────────┐  ┌──────────────────────┐
│ CharacterConsistency │  │ SettingConsistency   │
│ Agent                │  │ Agent                │
│ - Extract chars      │  │ - Extract settings   │
│ - Visual desc        │  │ - Visual desc        │
│ - Consistency check  │  │ - Consistency check  │
└──────────┬───────────┘  └──────────┬───────────┘
           │                         │
           └────────────┬────────────┘
                        │
                        ▼
        ┌────────────────────────────────────┐
        │   StoryboardPromptAgent            │
        │ - Optimize image prompts           │
        │ - Incorporate consistency          │
        │ - Generate visual descriptions     │
        └────────────┬───────────────────────┘
                     │
                     ▼
        ┌────────────────────────────────────┐
        │   VideoPromptAgent                 │
        │ - Convert to video prompts         │
        │ - Add motion/timing                │
        │ - Audio suggestions                │
        └────────────┬───────────────────────┘
                     │
                     ▼
        ┌────────────────────────────────────┐
        │   VideoGenerationAgent             │
        │ - Generate video clips             │
        │ - Handle retries                   │
        │ - Manage storage                   │
        └────────────┬───────────────────────┘
                     │
                     ▼
        ┌────────────────────────────────────┐
        │   VideoAssemblyAgent               │
        │ - Assemble clips                   │
        │ - Add transitions                  │
        │ - Mix audio                        │
        └────────────┬───────────────────────┘
                     │
                     ▼
        ┌────────────────────────────────────┐
        │    Final Movie Output              │
        └────────────────────────────────────┘
```

## Prompt Engineering Strategy

### 1. **ScriptAnalysisAgent Prompts**

**System Prompt:**
```
You are an expert screenplay analyst with deep knowledge of film structure, 
narrative theory, and character development. Analyze screenplays and extract 
key structural elements considering:
1. Three-act structure and narrative arc
2. Character introductions and development
3. Setting/location changes
4. Scene transitions and pacing
5. Thematic elements
6. Key turning points for trailer material
```

**User Prompt (Chain-of-Thought):**
```
Analyze the structure of this screenplay:

[SCREENPLAY EXCERPT]

Please analyze:
1. How many distinct scenes are there?
2. What is the narrative arc (setup, confrontation, resolution)?
3. What is the estimated total duration?
4. What are the major plot points?
5. What is the overall story summary?

REASONING: [Your detailed reasoning]
CONCLUSION: [Your final conclusion]
```

### 2. **CharacterConsistencyAgent Prompts**

**Structured Output (JSON Schema):**
```json
{
  "characters": [
    {
      "name": "string",
      "description": "string",
      "visualDescription": "string (for image generation)",
      "appearances": "number",
      "keyTraits": ["string"]
    }
  ]
}
```

### 3. **StoryboardPromptAgent Prompts**

**Optimized Image Prompt:**
```
Create a cinematic still frame for a film scene with the following details:

Scene: {scene_description}

Setting: {setting_name}
{setting_visual_description}

Characters in scene:
{character_descriptions}

Visual Style: cinematic, professional cinematography, high production value
Composition: Wide shot establishing the scene with characters and environment
Lighting: Professional film lighting, dramatic and atmospheric
Quality: 4K, highly detailed, photorealistic

Generate a single, cohesive image that captures the essence of this scene.
```

### 4. **VideoPromptAgent Prompts**

**Video Generation Prompt:**
```
Create a {duration} second cinematic video for a film scene:

Scene Description: {scene_description}

Setting: {setting_name}
Visual Style: {setting_visual_description}

Characters: {characters_description}

Requirements:
- Professional cinematography with smooth camera movements
- Natural lighting and atmospheric effects
- Characters should move naturally and realistically
- Audio: Include appropriate ambient sounds and subtle background music
- Pacing: Appropriate for a {duration} second scene
- Quality: High production value, cinematic quality
- Consistency: Maintain visual consistency with established setting and characters
```

## Prompt Optimization Process

The `PromptOptimizer` uses meta-prompting to iteratively improve prompts:

```typescript
// Original prompt
const original = "Generate a scene description";

// Optimization
const optimized = await PromptOptimizer.optimizePrompt(
  original,
  "Scene from a sci-fi thriller",
  "accuracy"
);

// Result includes:
// - optimizedPrompt: Improved version with better structure
// - improvements: ["Added specificity", "Clarified output format", ...]
// - score: 0-100 quality score
```

## Workflow Execution

### 1. **Initialization**
```typescript
const context: AgentContext = {
  projectId: 123,
  userId: 456,
  conversationHistory: [],
  metadata: { workflowType: "full_pipeline" }
};

const orchestrator = WorkflowOrchestrator.createDefaultPipeline(context);
const execution = orchestrator.initializeWorkflow();
```

### 2. **Execution**
```typescript
const result = await orchestrator.executeWorkflow(
  "ScriptAnalysisAgent",
  { scriptContent: "..." },
  (step) => console.log(`Step completed: ${step.agentName}`)
);
```

### 3. **State Tracking**
```typescript
// Get current status
const status = orchestrator.getExecutionStatus();
// { status: "running", currentStep: 2, steps: [...] }

// Get progress
const progress = orchestrator.getProgress();
// 45 (percentage)

// Get logs
const logs = orchestrator.getExecutionLogs();
// [{ agentName, input, output, reasoning, duration, success }]
```

## Integration with Frontend

### 1. **Real-Time Workflow Tracking**

The frontend polls the workflow status endpoint:
```typescript
const workflowStatus = trpc.workflow.getWorkflowStatus.useQuery({ projectId });
// Returns: { status, progress, error }
```

### 2. **Agent Execution Logs**

Display agent reasoning and outputs:
```typescript
const logs = trpc.workflow.getWorkflowLogs.useQuery({ projectId });
// Returns: [{ agentName, message, level, timestamp }]
```

### 3. **Workflow Control**

Users can pause/resume workflows:
```typescript
await trpc.workflow.pauseWorkflow.mutate({ projectId });
await trpc.workflow.resumeWorkflow.mutate({ projectId });
```

### 4. **Agent Information**

Display available agents and capabilities:
```typescript
const agentInfo = trpc.workflow.getAgentInfo.useQuery();
// Returns: [{ name, description, capabilities }]
```

## Error Handling & Recovery

### 1. **Agent-Level Error Handling**
```typescript
try {
  const result = await agent.execute(input);
  if (!result.success) {
    // Retry with refined prompt
    const optimized = await PromptOptimizer.optimizePrompt(
      originalPrompt,
      errorContext,
      "accuracy"
    );
    // Retry with optimized prompt
  }
} catch (error) {
  // Log and propagate
  step.error = error.message;
  step.status = "failed";
}
```

### 2. **Workflow-Level Recovery**
```typescript
if (execution.status === "failed") {
  // Option 1: Retry from last successful step
  await orchestrator.resumeWorkflow();
  
  // Option 2: Rollback to checkpoint
  await orchestrator.resetWorkflow();
  // Re-execute with refined parameters
}
```

## Performance Optimization

### 1. **Prompt Caching**
```typescript
// Cache optimized prompts for reuse
const promptCache = new Map<string, string>();

const getOptimizedPrompt = async (key: string, generator: () => Promise<string>) => {
  if (promptCache.has(key)) {
    return promptCache.get(key);
  }
  const prompt = await generator();
  promptCache.set(key, prompt);
  return prompt;
};
```

### 2. **Parallel Agent Execution**
```typescript
// Execute independent agents in parallel
const [characters, settings] = await Promise.all([
  characterAgent.execute(input),
  settingAgent.execute(input)
]);
```

### 3. **Streaming Outputs**
```typescript
// Stream agent reasoning and outputs to frontend
const response = await invokeLLM({
  messages,
  stream: true  // Enable streaming
});

for await (const chunk of response) {
  // Send to frontend in real-time
  broadcastUpdate({ type: "agent_output", data: chunk });
}
```

## Monitoring & Analytics

### 1. **Agent Performance Metrics**
```typescript
interface AgentMetrics {
  agentName: string;
  averageDuration: number;
  successRate: number;
  errorRate: number;
  averagePromptScore: number;
}
```

### 2. **Workflow Analytics**
```typescript
interface WorkflowAnalytics {
  totalExecutions: number;
  averageCompletionTime: number;
  successRate: number;
  commonFailurePoints: string[];
  agentMetrics: AgentMetrics[];
}
```

## Future Enhancements

1. **Multi-Agent Collaboration**: Agents can collaborate on complex tasks
2. **Dynamic Agent Selection**: Choose agents based on input characteristics
3. **Feedback Loops**: Users can provide feedback to improve agent outputs
4. **Prompt Learning**: System learns optimal prompts over time
5. **Custom Agents**: Users can create custom agents for specific needs
6. **Agent Marketplace**: Share and discover community-built agents

## Summary

The agentic workflow architecture provides:
- **Modularity**: Each agent handles a specific task
- **Reasoning**: Chain-of-thought for explainable AI
- **Optimization**: Iterative prompt refinement
- **Orchestration**: Coordinated multi-agent execution
- **Tracking**: Real-time progress and logging
- **Reliability**: Error handling and recovery
- **Extensibility**: Easy to add new agents and workflows
