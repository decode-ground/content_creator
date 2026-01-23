# Agent Integration Guide

## Frontend-Agent Communication Flow

### 1. User Initiates Workflow

```
User clicks "Parse Script" button
    ↓
Frontend calls trpc.workflow.startWorkflow
    ↓
Backend initializes WorkflowOrchestrator
    ↓
First agent (ScriptAnalysisAgent) begins execution
    ↓
Frontend polls trpc.workflow.getWorkflowStatus
```

### 2. Real-Time Progress Updates

```typescript
// Frontend component
export function WorkflowProgress({ projectId }) {
  const [progress, setProgress] = useState(0);
  
  // Poll workflow status every 2 seconds
  useEffect(() => {
    const interval = setInterval(async () => {
      const status = await trpc.workflow.getWorkflowStatus.useQuery({ projectId });
      setProgress(status.progress);
      
      if (status.status === "completed" || status.status === "failed") {
        clearInterval(interval);
      }
    }, 2000);
    
    return () => clearInterval(interval);
  }, [projectId]);
  
  return (
    <div className="progress-bar" style={{ width: `${progress}%` }}>
      {progress}%
    </div>
  );
}
```

### 3. Agent Execution Logs Display

```typescript
// Display agent reasoning and outputs
export function AgentExecutionLogs({ projectId }) {
  const logs = trpc.workflow.getWorkflowLogs.useQuery({ projectId });
  
  return (
    <div className="logs-container">
      {logs.data?.logs.map((log) => (
        <div key={log.timestamp} className="log-entry">
          <span className="agent-name">{log.agentName}</span>
          <span className="timestamp">{log.timestamp}</span>
          <p className="message">{log.message}</p>
          
          {/* Show reasoning if available */}
          {log.reasoning && (
            <details>
              <summary>View Reasoning</summary>
              <pre>{log.reasoning}</pre>
            </details>
          )}
          
          {/* Show output if available */}
          {log.output && (
            <details>
              <summary>View Output</summary>
              <pre>{JSON.stringify(log.output, null, 2)}</pre>
            </details>
          )}
        </div>
      ))}
    </div>
  );
}
```

## Agent Execution Sequence

### Full Pipeline Execution

```
1. ScriptAnalysisAgent
   Input: { scriptContent, projectTitle }
   Output: { title, summary, sceneCount, characterCount, ... }
   Next: SceneBreakdownAgent
   
2. SceneBreakdownAgent
   Input: { scenes, scriptContent }
   Output: [{ sceneNumber, title, description, setting, characters, duration }]
   Next: CharacterConsistencyAgent & SettingConsistencyAgent (parallel)
   
3. CharacterConsistencyAgent (parallel with SettingConsistencyAgent)
   Input: { scenes, characters }
   Output: [{ name, description, visualDescription, appearances }]
   Next: StoryboardPromptAgent
   
4. SettingConsistencyAgent (parallel with CharacterConsistencyAgent)
   Input: { scenes, settings }
   Output: [{ name, description, visualDescription, appearances }]
   Next: StoryboardPromptAgent
   
5. StoryboardPromptAgent
   Input: { scenes, characters, settings }
   Output: [{ sceneId, optimizedPrompt, score }]
   Next: VideoPromptAgent
   
6. VideoPromptAgent
   Input: { scenes, characters, settings, storyboardPrompts }
   Output: [{ sceneId, videoPrompt, duration, audioSuggestions }]
   Next: VideoGenerationAgent
   
7. VideoGenerationAgent
   Input: { scenes, videoPrompts }
   Output: [{ sceneId, videoUrl, duration, status }]
   Next: VideoAssemblyAgent
   
8. VideoAssemblyAgent
   Input: { videoClips, transitionDuration }
   Output: { movieUrl, totalDuration, status }
   Done
```

## Prompt Engineering Integration

### Dynamic Prompt Optimization

```typescript
// In agent execution
async execute(input: ScriptAnalysisInput): Promise<AgentResult> {
  // Step 1: Generate initial prompt
  const initialPrompt = this.generatePrompt(input);
  
  // Step 2: Optimize prompt
  const optimization = await PromptOptimizer.optimizePrompt(
    initialPrompt,
    `Analyzing screenplay: ${input.projectTitle}`,
    "accuracy"
  );
  
  // Step 3: Log optimization for debugging
  console.log("Prompt Optimization:", {
    originalScore: 50,
    optimizedScore: optimization.score,
    improvements: optimization.improvements
  });
  
  // Step 4: Execute with optimized prompt
  const result = await this.reasonWithLLM(optimization.optimizedPrompt);
  
  return this.success(result.conclusion, result.reasoning, "NextAgent");
}
```

### Few-Shot Prompting

```typescript
// Create few-shot examples for better results
const fewShotPrompt = PromptOptimizer.createFewShotPrompt(
  `Analyze this screenplay scene and extract key information:`,
  [
    {
      input: `INT. COFFEE SHOP - MORNING\nJohn sits at a table, nervously checking his watch...`,
      output: `{"setting": "Coffee Shop", "characters": ["John"], "mood": "tense", "duration": 30}`
    },
    {
      input: `EXT. ROOFTOP - NIGHT\nSarah and Tom stand at the edge, looking at the city...`,
      output: `{"setting": "Rooftop", "characters": ["Sarah", "Tom"], "mood": "romantic", "duration": 45}`
    }
  ]
);

// Use in agent
const result = await this.reasonWithLLM(fewShotPrompt);
```

## Error Recovery & Refinement

### Automatic Prompt Refinement on Failure

```typescript
async executeWithRetry(input: any, maxRetries: number = 3): Promise<AgentResult> {
  let lastError: string | null = null;
  
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      const result = await this.execute(input);
      
      if (result.success) {
        return result;
      }
      
      lastError = result.error;
      
      // Refine prompt based on error
      if (attempt < maxRetries) {
        const refinedPrompt = await this.refinePromptForError(
          this.currentPrompt,
          lastError
        );
        this.currentPrompt = refinedPrompt;
      }
    } catch (error) {
      lastError = error instanceof Error ? error.message : "Unknown error";
    }
  }
  
  return this.failure(lastError || "Max retries exceeded");
}

private async refinePromptForError(prompt: string, error: string): Promise<string> {
  const refinement = await PromptOptimizer.optimizePrompt(
    prompt,
    `Previous error: ${error}. Refine the prompt to avoid this error.`,
    "accuracy"
  );
  
  return refinement.optimizedPrompt;
}
```

## Streaming Agent Outputs

### Real-Time Streaming to Frontend

```typescript
// Backend: Stream agent reasoning
export async function* streamAgentExecution(agent: Agent, input: any) {
  const result = await agent.execute(input);
  
  // Yield reasoning in real-time
  if (result.reasoning) {
    yield {
      type: "reasoning",
      data: result.reasoning,
      timestamp: new Date()
    };
  }
  
  // Yield output
  yield {
    type: "output",
    data: result.data,
    timestamp: new Date()
  };
  
  // Yield next agent
  if (result.nextAgent) {
    yield {
      type: "next_agent",
      data: result.nextAgent,
      timestamp: new Date()
    };
  }
}

// Frontend: Consume streaming updates
async function* watchAgentExecution(projectId: number) {
  const eventSource = new EventSource(`/api/workflow/stream/${projectId}`);
  
  eventSource.onmessage = (event) => {
    const update = JSON.parse(event.data);
    yield update;
  };
}
```

## Agent Performance Monitoring

### Track Agent Metrics

```typescript
interface AgentExecutionMetrics {
  agentName: string;
  executionTime: number;
  promptOptimizationScore: number;
  outputQuality: number;
  success: boolean;
  retryCount: number;
}

// Log metrics after each execution
function logAgentMetrics(metrics: AgentExecutionMetrics) {
  console.log(`[${metrics.agentName}]`, {
    duration: `${metrics.executionTime}ms`,
    promptScore: metrics.promptOptimizationScore,
    quality: metrics.outputQuality,
    success: metrics.success,
    retries: metrics.retryCount
  });
  
  // Store in database for analytics
  db.agentMetrics.insert(metrics);
}
```

## UI Components for Agent Visualization

### Workflow Visualization

```typescript
export function WorkflowVisualization({ projectId }) {
  const execution = trpc.workflow.getWorkflowStatus.useQuery({ projectId });
  const logs = trpc.workflow.getWorkflowLogs.useQuery({ projectId });
  
  return (
    <div className="workflow-viz">
      {/* Agent pipeline */}
      <div className="agent-pipeline">
        {AGENT_SEQUENCE.map((agentName, index) => (
          <AgentCard
            key={agentName}
            name={agentName}
            status={getAgentStatus(logs.data, agentName)}
            isActive={execution.data?.currentAgent === agentName}
            order={index + 1}
          />
        ))}
      </div>
      
      {/* Progress bar */}
      <ProgressBar progress={execution.data?.progress || 0} />
      
      {/* Execution logs */}
      <ExecutionLogs logs={logs.data} />
    </div>
  );
}

function AgentCard({ name, status, isActive, order }) {
  return (
    <div className={`agent-card ${status} ${isActive ? "active" : ""}`}>
      <div className="agent-order">{order}</div>
      <div className="agent-name">{name}</div>
      <div className="agent-status">
        {status === "completed" && <CheckIcon />}
        {status === "running" && <SpinnerIcon />}
        {status === "failed" && <ErrorIcon />}
        {status === "pending" && <ClockIcon />}
      </div>
    </div>
  );
}
```

### Prompt Inspection Panel

```typescript
export function PromptInspectionPanel({ agentName, projectId }) {
  const logs = trpc.workflow.getWorkflowLogs.useQuery({ projectId });
  const agentLog = logs.data?.find(l => l.agentName === agentName);
  
  return (
    <div className="prompt-panel">
      <h3>Prompt Inspection: {agentName}</h3>
      
      {/* Original prompt */}
      <section>
        <h4>Original Prompt</h4>
        <pre>{agentLog?.originalPrompt}</pre>
      </section>
      
      {/* Optimized prompt */}
      <section>
        <h4>Optimized Prompt</h4>
        <pre>{agentLog?.optimizedPrompt}</pre>
        <div className="score">Score: {agentLog?.promptScore}/100</div>
      </section>
      
      {/* Improvements */}
      <section>
        <h4>Improvements Made</h4>
        <ul>
          {agentLog?.improvements.map((imp) => (
            <li key={imp}>{imp}</li>
          ))}
        </ul>
      </section>
      
      {/* Agent reasoning */}
      <section>
        <h4>Agent Reasoning</h4>
        <pre>{agentLog?.reasoning}</pre>
      </section>
      
      {/* Output */}
      <section>
        <h4>Agent Output</h4>
        <pre>{JSON.stringify(agentLog?.output, null, 2)}</pre>
      </section>
    </div>
  );
}
```

## Best Practices

1. **Prompt Caching**: Cache optimized prompts to reduce API calls
2. **Parallel Execution**: Run independent agents in parallel
3. **Error Recovery**: Implement automatic prompt refinement on failures
4. **Progress Tracking**: Update frontend with real-time progress
5. **Logging**: Log all agent executions for debugging and analytics
6. **Validation**: Validate agent outputs before passing to next agent
7. **Monitoring**: Track agent performance metrics over time
8. **User Feedback**: Allow users to provide feedback on agent outputs

## Testing Agents

```typescript
// Unit test for agent
describe("ScriptAnalysisAgent", () => {
  it("should analyze screenplay structure", async () => {
    const agent = new ScriptAnalysisAgent(mockContext);
    const result = await agent.execute({
      scriptContent: mockScript,
      projectTitle: "Test Script"
    });
    
    expect(result.success).toBe(true);
    expect(result.data.sceneCount).toBeGreaterThan(0);
    expect(result.data.characterCount).toBeGreaterThan(0);
    expect(result.nextAgent).toBe("SceneBreakdownAgent");
  });
});
```

## Summary

The agent integration provides:
- **Modular Architecture**: Each agent handles specific tasks
- **Real-Time Tracking**: Frontend monitors agent execution
- **Prompt Optimization**: Automatic refinement for better outputs
- **Error Recovery**: Intelligent retry and refinement
- **Performance Monitoring**: Track agent metrics
- **User Visibility**: Show reasoning and outputs
- **Extensibility**: Easy to add new agents
