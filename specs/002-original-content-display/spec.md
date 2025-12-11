# Feature Specification: Display Original Content Instead of LLM-Optimized Content

**Feature Branch**: `002-original-content-display`  
**Created**: 2025-01-27  
**Status**: Draft  
**Input**: User description: "功能調整，目前產出的是經過 LLM 優化的文章內容，現在要改回去原始內容，ui/ux 要調整 原版/提示詞修改建議 2種內容，AI 優化版blocks不要了"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View Original Conversation Content (Priority: P1)

A user wants to view the original conversation content from the conversation log instead of the LLM-optimized article content. They want to see the raw dialogue exchanges as they occurred in the original conversation.

**Why this priority**: This is the core change - switching from optimized content to original content. Without this, the feature provides no value.

**Independent Test**: Can be fully tested by displaying a blog post page and verifying that the original conversation content is shown instead of optimized content blocks. Delivers immediate value by showing users the authentic conversation that generated the blog post.

**Acceptance Scenarios**:

1. **Given** a blog post exists with associated conversation log, **When** a user views the blog post page, **Then** the system displays the original conversation content from the conversation log instead of LLM-optimized content blocks
2. **Given** original conversation content is displayed, **When** a user reads the content, **Then** they can see the actual dialogue exchanges (user messages and AI responses) as they appeared in the original conversation
3. **Given** a conversation log contains structured messages (user/system/assistant roles), **When** the content is displayed, **Then** the system preserves message roles and formatting to distinguish between different speakers
4. **Given** original conversation content is displayed, **When** the content is rendered, **Then** it maintains readability with appropriate formatting (line breaks, message separation, etc.)

---

### User Story 2 - View Prompt Modification Suggestions Alongside Original Content (Priority: P1)

A user wants to see prompt modification suggestions displayed alongside the original conversation content. They want to understand how their original prompts could be improved while viewing the original conversation.

**Why this priority**: This provides educational value by showing prompt optimization suggestions in context with the original prompts. This is a key differentiator that helps users learn prompt engineering.

**Independent Test**: Can be tested independently by verifying that prompt suggestions are displayed alongside original content, allowing users to see both the original prompts and optimization suggestions together. Delivers value by teaching users how to improve their AI interactions.

**Acceptance Scenarios**:

1. **Given** a blog post has associated prompt suggestions, **When** a user views the blog post page, **Then** the system displays prompt modification suggestions alongside the original conversation content
2. **Given** prompt suggestions are displayed, **When** a user views a specific section of original content, **Then** they can see the corresponding prompt analysis (original prompt, diagnosis, better candidates) for prompts in that section
3. **Given** prompt suggestions are displayed, **When** a user interacts with the suggestions, **Then** they can see the original prompt, AI diagnosis, and at least 3 alternative prompt candidates with explanations
4. **Given** prompt suggestions are displayed, **When** a user wants to copy a suggested prompt, **Then** they can copy it to clipboard with a single action

---

### User Story 3 - Remove AI-Optimized Content Blocks (Priority: P1)

A user wants the system to stop generating and storing AI-optimized content blocks. The system should no longer create or display these optimized blocks.

**Why this priority**: This is a core requirement - removing the optimized blocks that are no longer needed. This simplifies the system and aligns with the goal of showing original content.

**Independent Test**: Can be tested by verifying that new blog posts are generated without creating optimized content blocks, and existing blog posts no longer display optimized blocks. Delivers value by simplifying the system and focusing on original content.

**Acceptance Scenarios**:

1. **Given** a conversation log is processed to generate a blog post, **When** the blog post is created, **Then** the system does not create or store AI-optimized content blocks
2. **Given** an existing blog post with optimized content blocks, **When** a user views the blog post, **Then** the system does not display the optimized content blocks
3. **Given** the system processes a conversation log, **When** content blocks are referenced, **Then** the system uses original conversation content instead of optimized blocks

---

### Edge Cases

- What happens when a conversation log has no associated prompt suggestions? → System displays only original content without prompt suggestion sections
- How does the system handle very long conversations when displaying original content? → System displays the full conversation with appropriate scrolling and pagination if needed
- What happens when prompt suggestions exist but don't correspond to specific sections in the original conversation? → System displays prompt suggestions in a dedicated section separate from the conversation content
- How does the system handle conversations with mixed languages or special formatting? → System preserves original formatting and displays content as-is from the conversation log
- What happens when a conversation log has malformed or incomplete messages? → System displays the content as stored, preserving any formatting issues that exist in the original data
- How does the system handle conversations with embedded code blocks, images, or other media? → System preserves and displays all original content including code blocks and media references

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST display original conversation content from conversation logs instead of LLM-optimized content blocks when showing blog posts
- **FR-002**: System MUST preserve message structure and roles (user/system/assistant) when displaying original conversation content
- **FR-003**: System MUST display prompt modification suggestions alongside original conversation content
- **FR-004**: System MUST associate prompt suggestions with corresponding sections or messages in the original conversation when possible
- **FR-005**: System MUST allow users to view both original content and prompt suggestions simultaneously using Side-by-Side Layout (70/30 split on desktop, stacked on mobile)
- **FR-006**: System MUST stop generating AI-optimized content blocks during blog post creation
- **FR-007**: System MUST stop storing AI-optimized content blocks in the content_blocks table for new blog posts
- **FR-008**: System MUST not display existing AI-optimized content blocks when rendering blog posts
- **FR-009**: System MUST maintain backward compatibility with existing blog posts that may have optimized content blocks stored (system ignores them during display)
- **FR-010**: System MUST preserve original conversation formatting (line breaks, code blocks, markdown) when displaying content
- **FR-011**: System MUST support copying prompt suggestions to clipboard
- **FR-012**: System MUST display prompt analysis components (original prompt, diagnosis, better candidates, expected effect) when showing prompt suggestions

### Key Entities *(include if feature involves data)*

- **Conversation Log**: Represents the source of original content. Key attributes: raw_content (original file content), parsed_content (structured messages with roles). Relationships: source for blog post display content.

- **Blog Post**: Represents the blog post entity. Key attributes: title, summary, tags, content (legacy field, may be used for fallback). Relationships: references Conversation Log for original content, may reference Prompt Suggestions.

- **Prompt Suggestion**: Represents prompt analysis and optimization suggestions. Key attributes: original_prompt, analysis, better_candidates, expected_effect. Relationships: associated with Conversation Log, displayed alongside original content.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can view original conversation content instead of optimized content in 100% of blog post views
- **SC-002**: System displays prompt modification suggestions alongside original content for at least 90% of blog posts that have associated prompt suggestions
- **SC-003**: System stops generating optimized content blocks for 100% of new blog posts created after feature implementation
- **SC-004**: Users can distinguish between original conversation content and prompt suggestions with 100% clarity using Side-by-Side Layout
- **SC-005**: Users can copy prompt suggestions to clipboard successfully in under 2 seconds per action
- **SC-006**: Original conversation content preserves message structure and formatting in 100% of displayed cases
- **SC-007**: System displays original content and prompt suggestions simultaneously without requiring page navigation in at least 80% of viewport sizes (desktop, tablet, mobile)

## Assumptions

- Users want to see the authentic original conversation content rather than LLM-processed versions
- Prompt suggestions provide educational value and should remain visible alongside original content
- Existing blog posts with optimized content blocks can be migrated or ignored (backward compatibility)
- Original conversation content is stored in conversation_logs.raw_content or conversation_logs.parsed_content
- Side-by-Side Layout (Option B) is the selected UI/UX approach for displaying original content and prompt suggestions
- Users primarily want to learn from original prompts and their optimizations, not from optimized article content

## Dependencies

- Access to conversation_logs table with raw_content and parsed_content fields
- Access to prompt_suggestions table for displaying prompt analysis
- Existing UI components for displaying prompt suggestions (can be reused)
- Frontend framework capable of implementing the selected UI/UX approach

## Selected UI/UX Approach

**Option B: Side-by-Side Layout (Desktop) / Stacked Layout (Mobile)** has been selected as the final UI/UX approach.

### Description

Display original conversation content on the left (70% width on desktop) and prompt suggestions sidebar on the right (30% width on desktop). On mobile, stack them vertically with prompt suggestions below.

### Rationale

1. It aligns with the existing UI/UX pattern already implemented for prompt suggestions
2. It allows simultaneous viewing of original content and prompt suggestions
3. It provides good user experience on desktop while adapting to mobile
4. It maintains the educational value of showing both content types together
5. It leverages existing Intersection Observer implementation for section tracking

### Implementation Details

- **Desktop Layout**: Left column (70% width) shows original conversation messages, right sidebar (30% width, sticky) shows prompt suggestions
- **Mobile Layout**: Stacked vertically - original content first, prompt suggestions below
- **Section Tracking**: Uses Intersection Observer API to detect which section of original content is currently visible and automatically updates the sidebar to show corresponding prompt suggestions
- **Responsive Breakpoints**: Desktop ≥ 1024px (side-by-side), Mobile < 1024px (stacked)

### Additional Requirements

- **FR-013**: System MUST implement Side-by-Side Layout with 70/30 split on desktop viewports (≥ 1024px)
- **FR-014**: System MUST implement stacked vertical layout on mobile viewports (< 1024px) with original content above prompt suggestions
- **FR-015**: System MUST use Intersection Observer API to track visible sections of original content and update prompt suggestions sidebar accordingly
- **FR-016**: System MUST make the prompt suggestions sidebar sticky on desktop to remain visible while scrolling original content
- **FR-017**: System MUST support hover interactions to highlight corresponding prompt suggestions when hovering over sections of original content

---

## Alternative UI/UX Approaches (Not Selected)

The following UI/UX approaches were considered but not selected:

### Option A: Tab-Based View

**Description**: Display tabs at the top of the blog post page allowing users to switch between "原版" (Original) and "提示詞修改建議" (Prompt Suggestions) views.

**Pros**:
- Simple and intuitive interface
- Clear separation between content types
- Easy to implement
- Works well on all screen sizes

**Cons**:
- Users cannot view both simultaneously without switching tabs
- May require additional clicks to compare content

**Implementation**: Two tabs - one shows original conversation content, the other shows prompt suggestions organized by conversation sections.

---

### Option B: Side-by-Side Layout (Desktop) / Stacked Layout (Mobile)

**Description**: Display original conversation content on the left (70% width on desktop) and prompt suggestions sidebar on the right (30% width on desktop). On mobile, stack them vertically with prompt suggestions below.

**Pros**:
- Allows simultaneous viewing of both content types
- Familiar pattern from existing implementation
- Good use of screen real estate on desktop
- Responsive design adapts to mobile

**Cons**:
- Requires more complex layout management
- May be cramped on smaller screens

**Implementation**: Left column shows original conversation messages, right sidebar shows prompt suggestions that correspond to the currently visible section (using Intersection Observer).

---

### Option C: Toggle Button with Split View

**Description**: Display original conversation content by default with a toggle button. When toggled, show both original content and prompt suggestions in a split view (50/50 or adjustable).

**Pros**:
- Flexible - users can choose to view one or both
- Preserves screen space when prompt suggestions aren't needed
- Allows users to focus on original content first

**Cons**:
- Requires user interaction to see prompt suggestions
- Split view may reduce readability of both sections

**Implementation**: Default view shows original content. Toggle button switches to split view showing both side-by-side.

---

### Option D: Accordion/Expandable Sections

**Description**: Display original conversation content with expandable sections for prompt suggestions. Each section of the conversation that has associated prompt suggestions can be expanded to show the suggestions inline.

**Pros**:
- Contextual - suggestions appear near relevant conversation sections
- Clean, focused view of original content
- Works well on mobile devices
- Reduces visual clutter

**Cons**:
- Requires user interaction to see suggestions
- May be harder to compare multiple prompt suggestions
- More complex to implement section detection

**Implementation**: Original conversation displayed with inline expandable cards showing prompt suggestions for specific messages or sections.

---

### Option E: Two-Column Grid with Synchronized Scrolling

**Description**: Display original conversation content and prompt suggestions in two equal columns (50/50) with synchronized scrolling. When user scrolls one column, the other scrolls to maintain context.

**Pros**:
- Maximum visibility of both content types
- Synchronized scrolling maintains context
- Good for detailed comparison

**Cons**:
- May be overwhelming with too much information
- Requires sophisticated scrolling synchronization
- Less optimal for mobile devices

**Implementation**: Two-column grid layout with scroll synchronization logic to keep related content aligned.


## Out of Scope

- Migrating or deleting existing optimized content blocks from the database (system will ignore them during display)
- Creating new content optimization features
- Generating new types of content blocks
- Real-time editing of original conversation content
- Exporting original content in formats other than display
- Batch operations on multiple blog posts
