# Tasks: Display Original Content Instead of LLM-Optimized Content

**Input**: Design documents from `/specs/002-original-content-display/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (gRPC Protocol Updates)

**Purpose**: Update gRPC protocol definitions to support conversation messages

- [x] T001 Update gRPC proto file to add ConversationMessage message type in share/proto/blog_agent.proto
- [x] T002 Update GetBlogPostWithPromptsResponse to include conversation_messages field in share/proto/blog_agent.proto
- [x] T003 Add PromptSuggestion message type to proto file in share/proto/blog_agent.proto
- [x] T004 Regenerate gRPC Python code from updated proto file using scripts/generate-proto.sh
- [x] T005 Regenerate gRPC TypeScript code from updated proto file using scripts/generate-proto.sh

---

## Phase 2: Foundational (Backend Data Models)

**Purpose**: Create backend models and update service layer to support conversation messages

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T006 [P] Create ConversationMessage Pydantic model in python-workspace/apps/server/src/blog_agent/storage/models.py
- [x] T007 [P] Update repository to extract conversation messages from parsed_content in python-workspace/apps/server/src/blog_agent/storage/repository.py
- [x] T008 Update BlogService.get_blog_post_with_prompts to return conversation_messages in python-workspace/apps/server/src/blog_agent/services/blog_service.py
- [x] T009 Update BlogService.get_blog_post_with_prompts to query conversation_logs table in python-workspace/apps/server/src/blog_agent/services/blog_service.py
- [x] T010 Update BlogService.get_blog_post_with_prompts to return empty content_blocks array for backward compatibility in python-workspace/apps/server/src/blog_agent/services/blog_service.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - View Original Conversation Content (Priority: P1) 🎯 MVP

**Goal**: Display original conversation content from conversation logs instead of LLM-optimized content blocks when viewing blog posts

**Independent Test**: Display a blog post page and verify that original conversation content is shown instead of optimized content blocks. Users can see actual dialogue exchanges (user messages and AI responses) as they appeared in the original conversation.

### Implementation for User Story 1

- [x] T011 [P] [US1] Create ConversationViewer component to display conversation messages in typescript-workspace/apps/web/components/conversation-viewer.tsx
- [x] T012 [US1] Implement message role styling (user vs assistant) in ConversationViewer component in typescript-workspace/apps/web/components/conversation-viewer.tsx
- [x] T013 [US1] Add Markdown rendering support for message content in ConversationViewer component in typescript-workspace/apps/web/components/conversation-viewer.tsx
- [x] T014 [US1] Add message ID attributes for Intersection Observer tracking in ConversationViewer component in typescript-workspace/apps/web/components/conversation-viewer.tsx
- [x] T015 [US1] Update blog-post-client.tsx to use ConversationViewer instead of content blocks in typescript-workspace/apps/web/app/blog/[id]/blog-post-client.tsx
- [x] T016 [US1] Update page.tsx to fetch conversation_messages from GetBlogPostWithPrompts API in typescript-workspace/apps/web/app/blog/[id]/page.tsx
- [x] T017 [US1] Update page.tsx to pass conversation_messages to BlogPostClient component in typescript-workspace/apps/web/app/blog/[id]/page.tsx
- [x] T018 [US1] Update gRPC client function getBlogPostWithPrompts to handle conversation_messages response in typescript-workspace/apps/web/lib/grpc-client.ts
- [x] T019 [US1] Add error handling for missing conversation_log in backend service in python-workspace/apps/server/src/blog_agent/services/blog_service.py
- [x] T020 [US1] Add error handling for malformed parsed_content in backend service in python-workspace/apps/server/src/blog_agent/services/blog_service.py

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently. Users can view original conversation content instead of optimized blocks.

---

## Phase 4: User Story 2 - View Prompt Modification Suggestions Alongside Original Content (Priority: P1)

**Goal**: Display prompt modification suggestions alongside original conversation content, allowing users to see both original prompts and optimization suggestions together

**Independent Test**: Verify that prompt suggestions are displayed alongside original content, allowing users to see both the original prompts and optimization suggestions together. Users can see corresponding prompt analysis when viewing specific sections of original content.

### Implementation for User Story 2

- [x] T021 [P] [US2] Update BlogService.get_blog_post_with_prompts to query prompt_suggestions table in python-workspace/apps/server/src/blog_agent/services/blog_service.py
- [x] T022 [US2] Convert prompt_suggestions to PromptSuggestion proto messages in BlogService in python-workspace/apps/server/src/blog_agent/services/blog_service.py
- [x] T023 [US2] Update GetBlogPostWithPromptsResponse to include prompt_suggestions field in share/proto/blog_agent.proto
- [x] T024 [US2] Implement prompt-to-message matching logic in frontend (match original_prompt with user messages) in typescript-workspace/apps/web/app/blog/[id]/blog-post-client.tsx
- [x] T025 [US2] Update ConversationViewer to highlight messages with associated prompt suggestions in typescript-workspace/apps/web/components/conversation-viewer.tsx
- [x] T026 [US2] Update PromptSidebar to work with conversation messages instead of content blocks in typescript-workspace/apps/web/components/prompt-sidebar.tsx
- [x] T027 [US2] Update Intersection Observer to track conversation message indices instead of block IDs in typescript-workspace/apps/web/app/blog/[id]/blog-post-client.tsx
- [x] T028 [US2] Update hover interactions to highlight corresponding prompt suggestions for conversation messages in typescript-workspace/apps/web/app/blog/[id]/blog-post-client.tsx
- [x] T029 [US2] Ensure PromptCard component displays all prompt analysis components (original prompt, diagnosis, better candidates, expected effect) in typescript-workspace/apps/web/components/prompt-card.tsx
- [x] T030 [US2] Implement copy-to-clipboard functionality for prompt suggestions in PromptCard component in typescript-workspace/apps/web/components/prompt-card.tsx

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently. Users can view original conversation content with prompt suggestions displayed alongside.

---

## Phase 5: User Story 3 - Remove AI-Optimized Content Blocks (Priority: P1)

**Goal**: Stop generating and storing AI-optimized content blocks. System should no longer create or display these optimized blocks.

**Independent Test**: Verify that new blog posts are generated without creating optimized content blocks, and existing blog posts no longer display optimized blocks. System uses original conversation content instead of optimized blocks.

### Implementation for User Story 3

- [x] T031 [US3] Remove _create_content_blocks method call from BlogEditor.edit method in python-workspace/apps/server/src/blog_agent/workflows/editor.py
- [x] T032 [US3] Remove content_blocks from EditEvent return value in BlogEditor.edit method in python-workspace/apps/server/src/blog_agent/workflows/editor.py
- [x] T033 [US3] Update workflow to skip content_blocks creation step in python-workspace/apps/server/src/blog_agent/workflows/blog_workflow.py
- [x] T034 [US3] Ensure blog_post.content field is still populated for backward compatibility in python-workspace/apps/server/src/blog_agent/workflows/editor.py
- [x] T035 [US3] Update frontend to ignore content_blocks in GetBlogPostWithPromptsResponse in typescript-workspace/apps/web/app/blog/[id]/page.tsx
- [x] T036 [US3] Remove content_blocks rendering logic from MarkdownRenderer component in typescript-workspace/apps/web/components/markdown-renderer.tsx
- [x] T037 [US3] Update MarkdownRenderer fallback to use blog_post.content if conversation_messages unavailable in typescript-workspace/apps/web/components/markdown-renderer.tsx
- [x] T038 [US3] Add logging to track when content_blocks are skipped during blog post creation in python-workspace/apps/server/src/blog_agent/workflows/editor.py

**Checkpoint**: All user stories should now be independently functional. System no longer generates content blocks and displays original conversation content instead.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T039 [P] Add TypeScript type definitions for ConversationMessage interface in typescript-workspace/apps/web/types/conversation.ts (Types auto-generated from proto)
- [x] T040 [P] Add TypeScript type definitions for PromptSuggestion interface in typescript-workspace/apps/web/types/prompt.ts (Types auto-generated from proto)
- [x] T041 Update Side-by-Side Layout responsive breakpoints (desktop ≥ 1024px, mobile < 1024px) in typescript-workspace/apps/web/app/blog/[id]/blog-post-client.tsx
- [x] T042 Ensure ConversationViewer preserves original formatting (line breaks, code blocks, markdown) in typescript-workspace/apps/web/components/conversation-viewer.tsx
- [x] T043 Add error handling for conversations with no messages in ConversationViewer component in typescript-workspace/apps/web/components/conversation-viewer.tsx
- [x] T044 Add error handling for conversations with malformed message structure in backend service in python-workspace/apps/server/src/blog_agent/services/blog_service.py
- [x] T045 Update mobile layout to stack conversation content above prompt suggestions in typescript-workspace/apps/web/app/blog/[id]/blog-post-client.tsx
- [x] T046 Ensure sticky sidebar behavior works correctly on desktop viewport in typescript-workspace/apps/web/components/prompt-sidebar.tsx
- [x] T047 Add loading states for conversation messages fetch in frontend in typescript-workspace/apps/web/app/blog/[id]/page.tsx (Handled by Next.js notFound)
- [x] T048 Add error states for conversation messages fetch failures in frontend in typescript-workspace/apps/web/app/blog/[id]/page.tsx (Handled by Next.js notFound)
- [x] T049 Run quickstart.md validation to ensure all implementation steps are correct
- [x] T050 Update documentation to reflect changes in display logic in specs/002-original-content-display/README.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion (proto updates) - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (US1 → US2 → US3)
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) - Depends on US1 for ConversationViewer component
- **User Story 3 (P1)**: Can start after Foundational (Phase 2) - Independent, can run in parallel with US1/US2

### Within Each User Story

- Models/Proto updates before service layer
- Service layer before frontend components
- Core components before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks (T001-T005) marked [P] can run in parallel
- Foundational tasks T006-T007 marked [P] can run in parallel
- Once Foundational phase completes:
  - US1 and US3 can start in parallel (different files, no dependencies)
  - US2 should wait for US1 ConversationViewer component
- Within US1: T011-T014 can run in parallel (component creation)
- Within US2: T021-T023 can run in parallel (backend updates)
- Within US3: T031-T034 can run in parallel (workflow updates)
- All Polish tasks marked [P] can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all component creation tasks together:
Task: "Create ConversationViewer component to display conversation messages"
Task: "Implement message role styling (user vs assistant) in ConversationViewer component"
Task: "Add Markdown rendering support for message content in ConversationViewer component"
Task: "Add message ID attributes for Intersection Observer tracking in ConversationViewer component"

# Then proceed with integration:
Task: "Update blog-post-client.tsx to use ConversationViewer instead of content blocks"
Task: "Update page.tsx to fetch conversation_messages from GetBlogPostWithPrompts API"
```

---

## Parallel Example: User Story 3

```bash
# Launch all workflow update tasks together:
Task: "Remove _create_content_blocks method call from BlogEditor.edit method"
Task: "Remove content_blocks from EditEvent return value in BlogEditor.edit method"
Task: "Update workflow to skip content_blocks creation step"
Task: "Ensure blog_post.content field is still populated for backward compatibility"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (proto updates)
2. Complete Phase 2: Foundational (backend models and service updates)
3. Complete Phase 3: User Story 1 (display original conversation content)
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (frontend ConversationViewer)
   - Developer B: User Story 3 (backend workflow updates)
3. After US1 completes:
   - Developer A: User Story 2 (prompt suggestions integration)
   - Developer B: Polish & Cross-Cutting Concerns
4. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- All three user stories are P1 priority, but US1 is marked as MVP since it's the core change
- US2 depends on US1 for the ConversationViewer component
- US3 is independent and can run in parallel with US1

---

## Task Summary

- **Total Tasks**: 50
- **Phase 1 (Setup)**: 5 tasks
- **Phase 2 (Foundational)**: 5 tasks
- **Phase 3 (US1)**: 10 tasks
- **Phase 4 (US2)**: 10 tasks
- **Phase 5 (US3)**: 8 tasks
- **Phase 6 (Polish)**: 12 tasks

**Parallel Opportunities Identified**:
- Setup phase: 5 parallel tasks
- Foundational phase: 2 parallel tasks
- US1: 4 parallel component tasks
- US2: 3 parallel backend tasks
- US3: 4 parallel workflow tasks
- Polish: Multiple parallel tasks

**Independent Test Criteria**:
- **US1**: Display blog post page and verify original conversation content is shown instead of optimized blocks
- **US2**: Verify prompt suggestions are displayed alongside original content with proper association
- **US3**: Verify new blog posts are generated without content blocks and existing posts don't display them

**Suggested MVP Scope**: User Story 1 only (Phase 1 + Phase 2 + Phase 3)
