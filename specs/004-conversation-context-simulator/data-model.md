# Data Model: Conversation Context Simulator

## New/Updated Entities

### Conversation History Package (Transient)
A formatted string for the clipboard.
- **Header**: Instruction string.
- **History**: String containing messages 1 to N-1 inside `<History>` tags.
- **Task**: String containing message N inside `<Task>` tags.

### Fact Extract Memory Result (Transient/Cached)
The output of the compression API.
- **Extracted Facts**: A bulleted list or summarized text of key points from the conversation history.
- **Character Count**: Current count to validate against the user-defined limit.

## Service Interface (Proto Update)

I will add a new RPC to `BlogAgentService` for the Fact Extraction.

```proto
// In blog_agent.proto

service BlogAgentService {
  // ... existing rpcs ...
  
  // Extract key facts from a conversation for context simulation
  rpc ExtractConversationFacts(ExtractConversationFactsRequest) returns (ExtractConversationFactsResponse);
}

message ExtractConversationFactsRequest {
  string conversation_log_id = 1;
  int32 max_characters = 2; // User-defined limit from the form
}

message ExtractConversationFactsResponse {
  string extracted_facts = 1;
  int32 actual_characters = 2;
  bool limit_exceeded = 3;
}
```

## UI State (ConversationViewer)
- **activeLimit**: Number (default 5000) for the compression form.
- **isCompressing**: Boolean for loading state.
- **showLimitForm**: Boolean to toggle the compression limit modal/form.

