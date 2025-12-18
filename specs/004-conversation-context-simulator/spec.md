# Feature Specification: Conversation Context Simulator (Manual Simulator)

**Feature Branch**: `004-conversation-context-simulator`  
**Created**: 2025-12-19  
**Status**: Draft  
**Input**: User description: "Add a 'Manual Simulator' feature to each conversation message allowing users to copy the conversation context for pasting into LLM web UIs. Includes a 'Fact Extract Memory' service to compress history when it exceeds length limits, with UI options for both original and compressed versions."

## Clarifications

### Session 2025-12-19
- Q: Which messages should be included in the context export package (especially concerning system prompts)? → A: Include only user and assistant messages (skip system prompt).
- Q: What feedback should the user receive after the "Copy" action is successful? → A: Display a brief "Copied to clipboard" toast/notification.
- Q: What specific format should the conversation history package use for the structured text? → A: Use explicit headers: Instruction Header, `<History>`, and `<Task>`.
- Q: How should the system handle the compression limit for the "Fact Extract Memory" service? → A: Pop a form with default value 5000 and then call API.
- Q: What happens if the compressed version still exceeds the user-defined character limit? → A: Copy the best-effort compressed version and show a warning that the limit was exceeded.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - One-Click Context Export (Priority: P1)

As a user, I want to quickly export the current conversation history into a format that I can paste into ChatGPT, Claude, or DeepSeek, so that I can continue the conversation there with the same context.

**Why this priority**: This is the core functionality that enables the "Manual Simulator" workflow.

**Independent Test**: Can be fully tested by clicking the copy icon on a message and verifying the clipboard content contains the formatted history up to that point.

**Acceptance Scenarios**:

1. **Given** I am viewing a conversation with 5 messages, **When** I click the "Copy" icon on the 3rd message, **Then** my clipboard should contain a formatted package (XML tags) containing messages 1, 2, and 3 (user/assistant only).
2. **Given** I have copied the history package, **When** I paste it into ChatGPT, **Then** ChatGPT should acknowledge the history and be ready for a new prompt as defined in the package.

---

### User Story 2 - Compressed Context for Long Conversations (Priority: P2)

As a user, when my conversation history is too long (e.g., over 5000 characters), I want to be able to copy a compressed version that extracts only the essential facts, so that I don't hit the token limit of the target LLM.

**Why this priority**: Long conversations are common, and without compression, the manual simulator would fail due to context window limits.

**Independent Test**: Can be fully tested by triggering the "Compressed version" action on a long conversation and verifying the clipboard contains a shorter, fact-extracted summary instead of the full raw text.

**Acceptance Scenarios**:

1. **Given** a message in a long conversation, **When** I click the "More" icon and select "Compressed version", **Then** the system calls the compression API and places the summarized facts into my clipboard.
2. **Given** the compressed content is being generated, **When** the length exceeds the configured threshold (e.g., 5000 chars), **Then** the UI should display a warning or indicator about the length restriction.

---

### User Story 3 - Selective Original/Compressed Copy (Priority: P3)

As a user, I want to choose between copying the full original history or the compressed version from a single message, so that I have control over the amount of information shared.

**Why this priority**: Provides flexibility and better UX for power users.

**Independent Test**: Can be tested by verifying both the direct "Copy" icon and the "More" menu items are available and function correctly on each message.

**Acceptance Scenarios**:

1. **Given** a message, **When** I hover over it, **Then** I should see a "Copy" icon (for original) and a "More" icon (for the menu).
2. **Given** the "More" menu is open, **When** I select "Compressed version", **Then** the compression workflow starts.

---

### Edge Cases

- **Empty History**: What happens when trying to copy from the first message? (It should only include that message).
- **API Failure**: How does the system handle a failure in the Fact Extract Memory API? (It should notify the user and fall back to suggesting the original version or showing an error).
- **Extreme Length**: What if even the compressed version exceeds 5000 characters? (UI should warn the user that content might be truncated by the target LLM).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a "Copy" icon button on every message in the conversation view.
- **FR-002**: The "Copy" action MUST generate a formatted text package using structure markers (e.g., XML-like tags) to isolate context.
- **FR-003**: System MUST provide a "More" (ellipsis) icon next to the copy button that opens a dropdown menu.
- **FR-004**: The dropdown menu MUST contain a "Compressed version" option.
- **FR-005**: System MUST implement a "Fact Extract Memory" capability that takes conversation history and returns a summarized version focused on key facts.
- **FR-006**: When "Compressed version" is selected, the system MUST invoke the compression capability and copy the result to the clipboard.
- **FR-007**: UI MUST display a length indicator when the content (original or compressed) exceeds a defined threshold (e.g., 5000 characters).
- **FR-008**: The copy package MUST include all user and assistant conversation messages *up to and including* the message where the action was triggered. System messages MUST be excluded.
- **FR-009**: The formatted package MUST include a standard instruction header explaining to the target platform how to process the content blocks.
- **FR-010**: System MUST display a brief "Copied to clipboard" toast or notification upon successful copy to the clipboard.
- **FR-011**: When the "Compressed version" is selected, the system MUST show a form allowing the user to specify the maximum character limit (default: 5000) before invoking the compression capability.
- **FR-012**: If the compressed version still exceeds the user-defined character limit, the system MUST copy the best-effort compressed version to the clipboard and show a warning indicating the limit was exceeded.

### Key Entities *(include if feature involves data)*

- **Conversation History Package**: A structured text object containing:
    - Instruction header.
    - History block with previous messages (Role: Content).
    - Task block with the current/latest prompt.
- **Compressed Memory Extract**: A summarized version of the conversation history preserving essential facts while reducing total character count.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can copy the context package with a single action in under 200ms (excluding compression processing time).
- **SC-002**: The formatted package is correctly parsed and followed by leading LLM platforms in 95% of test cases.
- **SC-003**: The compression process reduces the character count of conversations > 10,000 characters by at least 50% while retaining core facts.
- **SC-004**: Users are informed of length overflows via UI indicators before they attempt to use the content on target platforms.

## Assumptions

- **A-001**: The "Fact Extract Memory" capability will be provided by a backend service capable of context-aware summarization.
- **A-002**: Target platforms generally follow instructions provided in structured text blocks within a single prompt.
- **A-003**: A 5000-character limit is a reasonable safe default for most web interfaces, though it may vary.
