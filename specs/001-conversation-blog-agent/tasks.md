# Tasks: AI Conversation to Blog Agent System

**Input**: Design documents from `/specs/001-conversation-blog-agent/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Multi-language workspace**: `python-workspace/`, `typescript-workspace/`, `share/`
- Paths follow the structure defined in plan.md

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project root structure (python-workspace/, typescript-workspace/, share/, scripts/, docker/)
- [ ] T002 [P] Initialize Python workspace with uv in python-workspace/pyproject.toml
- [ ] T003 [P] Initialize TypeScript workspace with pnpm in typescript-workspace/package.json and pnpm-workspace.yaml
- [ ] T004 [P] Create share/proto/ directory and copy blog_agent.proto from contracts/
- [ ] T005 [P] Create scripts/generate-proto.sh for generating Python and TypeScript code from .proto
- [ ] T006 [P] Create scripts/setup-dev.sh for development environment setup
- [ ] T007 [P] Create docker/postgresql.Dockerfile with pgvector extension
- [ ] T008 [P] Create docker/server.Dockerfile for Python gRPC server
- [ ] T009 Create docker-compose.yaml for local development stack
- [ ] T010 [P] Configure Python linting (ruff) and formatting (black) in python-workspace/apps/server/pyproject.toml
- [ ] T011 [P] Configure TypeScript linting (ESLint) and formatting (Prettier) in typescript-workspace/
- [ ] T012 [P] Setup shared TypeScript config packages in typescript-workspace/packages/typescript-config/
- [ ] T013 [P] Setup shared ESLint config in typescript-workspace/packages/eslint-config/

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T014 Setup PostgreSQL database schema and migrations in python-workspace/apps/server/src/blog_agent/storage/migrations/
- [ ] T015 [P] Create database connection utility in python-workspace/apps/server/src/blog_agent/storage/db.py
- [ ] T016 [P] Implement base Pydantic models in python-workspace/apps/server/src/blog_agent/storage/models.py (ConversationLog, BlogPost, ProcessingHistory, ContentExtract, ReviewFindings, PromptSuggestion)
- [ ] T017 [P] Create repository pattern base class in python-workspace/apps/server/src/blog_agent/storage/repository.py
- [ ] T018 [P] Setup structured logging (structlog) in python-workspace/apps/server/src/blog_agent/utils/logging.py
- [ ] T019 [P] Setup error handling infrastructure in python-workspace/apps/server/src/blog_agent/utils/errors.py
- [ ] T020 [P] Create environment configuration management in python-workspace/apps/server/src/blog_agent/config.py
- [ ] T021 [P] Generate gRPC Python code from share/proto/blog_agent.proto to python-workspace/apps/server/src/blog_agent/proto/
- [ ] T022 [P] Generate gRPC TypeScript code from share/proto/blog_agent.proto to typescript-workspace/apps/proto-gen/src/
- [ ] T023 [P] Create shared gRPC client package in typescript-workspace/packages/rpc-client/src/index.ts
- [ ] T024 [P] Setup LLM service abstraction in python-workspace/apps/server/src/blog_agent/services/llm_service.py
- [ ] T025 [P] Setup PostgreSQL + pgvector integration in python-workspace/apps/server/src/blog_agent/services/vector_store.py
- [ ] T026 Create gRPC server skeleton in python-workspace/apps/server/src/blog_agent/main.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Basic Conversation to Blog Conversion (Priority: P1) 🎯 MVP

**Goal**: Transform raw conversation logs into well-formatted blog posts with title, content, and metadata

**Independent Test**: Provide a simple conversation log file and verify that a structured blog post is generated with title, summary, tags, and content sections in Markdown format

### Implementation for User Story 1

- [ ] T027 [P] [US1] Create Markdown parser in python-workspace/apps/server/src/blog_agent/parsers/markdown_parser.py
- [ ] T028 [P] [US1] Create JSON parser in python-workspace/apps/server/src/blog_agent/parsers/json_parser.py
- [ ] T029 [P] [US1] Create CSV parser in python-workspace/apps/server/src/blog_agent/parsers/csv_parser.py
- [ ] T030 [US1] Create parser factory in python-workspace/apps/server/src/blog_agent/parsers/__init__.py to auto-detect format
- [ ] T031 [US1] Implement language detection utility in python-workspace/apps/server/src/blog_agent/utils/language_detector.py
- [ ] T032 [US1] Implement message role inference with heuristics in python-workspace/apps/server/src/blog_agent/parsers/role_inference.py (FR-028)
- [ ] T033 [US1] Create content extractor workflow step in python-workspace/apps/server/src/blog_agent/workflows/extractor.py
- [ ] T034 [US1] Create basic blog editor workflow step in python-workspace/apps/server/src/blog_agent/workflows/editor.py (simple version without review/extension)
- [ ] T035 [US1] Create blog workflow orchestrator in python-workspace/apps/server/src/blog_agent/workflows/blog_workflow.py (extractor → editor)
- [ ] T036 [US1] Implement ConversationLog repository methods in python-workspace/apps/server/src/blog_agent/storage/repository.py (create, get, list)
- [ ] T037 [US1] Implement BlogPost repository methods in python-workspace/apps/server/src/blog_agent/storage/repository.py (create, get, list)
- [ ] T038 [US1] Implement ProcessingHistory repository methods in python-workspace/apps/server/src/blog_agent/storage/repository.py (create, update, get)
- [ ] T039 [US1] Implement ProcessConversation gRPC handler in python-workspace/apps/server/src/blog_agent/main.py
- [ ] T040 [US1] Implement error handling with full technical details in python-workspace/apps/server/src/blog_agent/main.py (FR-024)
- [ ] T041 [US1] Create CLI command for processing conversation logs in typescript-workspace/apps/cli/src/commands/process.ts
- [ ] T042 [US1] Create file reader utility in typescript-workspace/apps/cli/src/utils/file-reader.ts
- [ ] T043 [US1] Create gRPC client wrapper in typescript-workspace/apps/cli/src/client/grpc-client.ts
- [ ] T044 [US1] Implement CLI entry point in typescript-workspace/apps/cli/src/index.ts
- [ ] T045 [US1] Add handling for malformed logs with auto-fix in python-workspace/apps/server/src/blog_agent/parsers/ (FR-026)
- [ ] T046 [US1] Add handling for empty/non-substantive content with low-quality marking in python-workspace/apps/server/src/blog_agent/workflows/extractor.py (FR-025)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently - users can submit conversation logs and receive basic blog posts

---

## Phase 4: User Story 5 - Structured Output with Metadata (Priority: P1) 🎯 MVP

**Goal**: Generate blog posts with structured metadata (title, tags, summary) compatible with blog publishing platforms

**Independent Test**: Verify that generated blog posts include all required metadata fields (title, tags, summary) in a structured format that can be directly imported into blog platforms

### Implementation for User Story 5

- [ ] T047 [US5] Enhance blog editor workflow step to generate structured metadata in python-workspace/apps/server/src/blog_agent/workflows/editor.py
- [ ] T048 [US5] Implement metadata extraction from conversation logs in python-workspace/apps/server/src/blog_agent/workflows/editor.py (preserve timestamps, participants per FR-015)
- [ ] T049 [US5] Add metadata validation in python-workspace/apps/server/src/blog_agent/storage/models.py (ensure title, summary, tags are present per FR-005)
- [ ] T050 [US5] Update BlogPost model to include all metadata fields in python-workspace/apps/server/src/blog_agent/storage/models.py
- [ ] T051 [US5] Create Markdown formatter with frontmatter support in python-workspace/apps/server/src/blog_agent/utils/markdown_formatter.py
- [ ] T052 [US5] Update CLI output formatter in typescript-workspace/apps/cli/src/utils/formatter.ts to display structured metadata
- [ ] T053 [US5] Add metadata export functionality in typescript-workspace/apps/cli/src/commands/process.ts

**Checkpoint**: At this point, User Stories 1 AND 5 should both work independently - MVP is complete with structured blog post output

---

## Phase 5: User Story 2 - Content Review and Quality Enhancement (Priority: P2)

**Goal**: Automatically review extracted content for errors, logical inconsistencies, and areas needing clarification

**Independent Test**: Provide a conversation with potential errors or unclear points, and verify that the review step identifies issues and suggests improvements

### Implementation for User Story 2

- [ ] T054 [P] [US2] Create review workflow step in python-workspace/apps/server/src/blog_agent/workflows/reviewer.py
- [ ] T055 [US2] Implement logical gap detection in python-workspace/apps/server/src/blog_agent/workflows/reviewer.py
- [ ] T056 [US2] Implement factual inconsistency detection in python-workspace/apps/server/src/blog_agent/workflows/reviewer.py
- [ ] T057 [US2] Implement unclear explanation detection in python-workspace/apps/server/src/blog_agent/workflows/reviewer.py
- [ ] T058 [US2] Create ReviewFindings repository methods in python-workspace/apps/server/src/blog_agent/storage/repository.py
- [ ] T059 [US2] Integrate review step into blog workflow in python-workspace/apps/server/src/blog_agent/workflows/blog_workflow.py (extractor → reviewer → editor)
- [ ] T060 [US2] Implement fact-checking detection and flagging in python-workspace/apps/server/src/blog_agent/workflows/reviewer.py (FR-010)
- [ ] T061 [US2] Update editor step to incorporate review findings in python-workspace/apps/server/src/blog_agent/workflows/editor.py
- [ ] T062 [US2] Add error flagging for issues that cannot be auto-corrected in python-workspace/apps/server/src/blog_agent/workflows/reviewer.py

**Checkpoint**: At this point, User Stories 1, 2, AND 5 should all work independently - content review enhances quality

---

## Phase 6: User Story 3 - Content Extension and Research (Priority: P2)

**Goal**: Automatically extend content that lacks context by researching and incorporating relevant background information

**Independent Test**: Provide a conversation with minimal context, and verify that the system identifies gaps and supplements content with relevant information

### Implementation for User Story 3

- [ ] T063 [P] [US3] Create Tavily service integration in python-workspace/apps/server/src/blog_agent/services/tavily_service.py
- [ ] T064 [US3] Create extension workflow step in python-workspace/apps/server/src/blog_agent/workflows/extender.py
- [ ] T065 [US3] Implement knowledge gap identification in python-workspace/apps/server/src/blog_agent/workflows/extender.py
- [ ] T066 [US3] Implement Tavily search integration for content extension in python-workspace/apps/server/src/blog_agent/workflows/extender.py
- [ ] T067 [US3] Implement content integration logic (merge research into content naturally) in python-workspace/apps/server/src/blog_agent/workflows/extender.py
- [ ] T068 [US3] Add optional knowledge base query support in python-workspace/apps/server/src/blog_agent/services/vector_store.py (FR-018)
- [ ] T069 [US3] Implement knowledge base priority (query KB first, then external sources) in python-workspace/apps/server/src/blog_agent/workflows/extender.py
- [ ] T070 [US3] Integrate extension step into blog workflow in python-workspace/apps/server/src/blog_agent/workflows/blog_workflow.py (extractor → extender → reviewer → editor)
- [ ] T071 [US3] Add error handling for Tavily API failures in python-workspace/apps/server/src/blog_agent/services/tavily_service.py (FR-019)
- [ ] T072 [US3] Implement fact-checking via Tavily in python-workspace/apps/server/src/blog_agent/workflows/reviewer.py (when fact-checking needs detected)

**Checkpoint**: At this point, User Stories 1, 2, 3, AND 5 should all work independently - content extension enhances comprehensiveness

---

## Phase 7: User Story 4 - Prompt Analysis and Optimization Suggestions (Priority: P3)

**Goal**: Analyze user prompts and suggest better ways to phrase them for more effective AI interactions

**Independent Test**: Provide a conversation with user prompts, and verify that the system identifies prompts, analyzes effectiveness, and suggests at least 3 improved alternatives

### Implementation for User Story 4

- [ ] T073 [P] [US4] Create prompt analyzer workflow step in python-workspace/apps/server/src/blog_agent/workflows/prompt_analyzer.py
- [ ] T074 [US4] Implement user prompt extraction from conversation logs in python-workspace/apps/server/src/blog_agent/workflows/prompt_analyzer.py
- [ ] T075 [US4] Implement prompt effectiveness evaluation in python-workspace/apps/server/src/blog_agent/workflows/prompt_analyzer.py
- [ ] T076 [US4] Implement generation of at least 3 alternative prompt candidates in python-workspace/apps/server/src/blog_agent/workflows/prompt_analyzer.py (FR-012)
- [ ] T077 [US4] Implement reasoning generation for why alternatives are better in python-workspace/apps/server/src/blog_agent/workflows/prompt_analyzer.py (FR-013)
- [ ] T078 [US4] Create PromptSuggestion repository methods in python-workspace/apps/server/src/blog_agent/storage/repository.py
- [ ] T079 [US4] Integrate prompt analysis into blog workflow in python-workspace/apps/server/src/blog_agent/workflows/blog_workflow.py (parallel branch)
- [ ] T080 [US4] Update editor step to include prompt suggestions section in blog post in python-workspace/apps/server/src/blog_agent/workflows/editor.py (FR-014)
- [ ] T081 [US4] Format prompt suggestions as side-by-side comparison in python-workspace/apps/server/src/blog_agent/utils/markdown_formatter.py

**Checkpoint**: At this point, all user stories should be independently functional - prompt analysis adds educational value

---

## Phase 8: Additional Features & Retrieval

**Purpose**: Support retrieval and listing of processed content (FR-022)

- [ ] T082 [P] Implement GetConversationLog gRPC handler in python-workspace/apps/server/src/blog_agent/main.py
- [ ] T083 [P] Implement ListConversationLogs gRPC handler in python-workspace/apps/server/src/blog_agent/main.py
- [ ] T084 [P] Implement GetBlogPost gRPC handler in python-workspace/apps/server/src/blog_agent/main.py
- [ ] T085 [P] Implement ListBlogPosts gRPC handler in python-workspace/apps/server/src/blog_agent/main.py
- [ ] T086 [P] Implement GetProcessingHistory gRPC handler in python-workspace/apps/server/src/blog_agent/main.py
- [ ] T087 [P] Create CLI command for listing conversation logs in typescript-workspace/apps/cli/src/commands/list.ts
- [ ] T088 [P] Create CLI command for retrieving blog posts in typescript-workspace/apps/cli/src/commands/retrieve.ts

---

## Phase 9: Advanced Features

**Purpose**: Handle edge cases and advanced scenarios

- [ ] T089 Implement long conversation segmentation (1000+ messages) with hierarchical summarization in python-workspace/apps/server/src/blog_agent/workflows/extractor.py (FR-027)
- [ ] T090 Implement segment summarization logic in python-workspace/apps/server/src/blog_agent/workflows/extractor.py
- [ ] T091 Implement trailing context preservation between segments in python-workspace/apps/server/src/blog_agent/workflows/extractor.py
- [ ] T092 Add support for optional additional file formats beyond Markdown in python-workspace/apps/server/src/blog_agent/utils/formatters.py (FR-020)

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T093 [P] Add comprehensive error logging with stack traces in python-workspace/apps/server/src/blog_agent/utils/logging.py
- [ ] T094 [P] Add structured logging for all workflow steps in python-workspace/apps/server/src/blog_agent/workflows/
- [ ] T095 [P] Add performance monitoring and metrics collection in python-workspace/apps/server/src/blog_agent/utils/metrics.py
- [ ] T096 [P] Optimize database queries with proper indexing (verify indexes from data-model.md)
- [ ] T097 [P] Add input validation for all gRPC endpoints in python-workspace/apps/server/src/blog_agent/main.py
- [ ] T098 [P] Add CLI help text and error messages in typescript-workspace/apps/cli/src/
- [ ] T099 [P] Create README documentation in python-workspace/apps/server/README.md
- [ ] T100 [P] Create README documentation in typescript-workspace/apps/cli/README.md
- [ ] T101 Run quickstart.md validation to ensure all setup steps work
- [ ] T102 [P] Add unit tests for parsers in python-workspace/apps/server/tests/unit/test_parsers.py
- [ ] T103 [P] Add unit tests for workflow steps in python-workspace/apps/server/tests/unit/test_workflows.py
- [ ] T104 [P] Add integration tests for end-to-end workflow in python-workspace/apps/server/tests/integration/test_workflow_integration.py
- [ ] T105 [P] Add CLI tests in typescript-workspace/apps/cli/tests/

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-7)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (US1/US5 → US2/US3 → US4)
- **Additional Features (Phase 8)**: Can proceed in parallel with user stories after Phase 2
- **Advanced Features (Phase 9)**: Depends on US1 completion
- **Polish (Phase 10)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 5 (P1)**: Can start after Foundational (Phase 2) - Depends on US1 for basic blog generation
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 for content extraction
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 for content extraction
- **User Story 4 (P3)**: Can start after Foundational (Phase 2) - Independent but enhances final output

### Within Each User Story

- Parsers before extractor
- Extractor before editor
- Services before workflows
- Workflows before gRPC handlers
- gRPC handlers before CLI commands
- Core implementation before integration

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, user stories can start in parallel (if team capacity allows)
- Parsers (T027-T029) can run in parallel
- Repository methods for different entities can run in parallel
- gRPC handlers (T082-T086) can run in parallel
- CLI commands (T087-T088) can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all parsers for User Story 1 together:
Task: "Create Markdown parser in python-workspace/apps/server/src/blog_agent/parsers/markdown_parser.py"
Task: "Create JSON parser in python-workspace/apps/server/src/blog_agent/parsers/json_parser.py"
Task: "Create CSV parser in python-workspace/apps/server/src/blog_agent/parsers/csv_parser.py"

# Launch all repository methods together:
Task: "Implement ConversationLog repository methods..."
Task: "Implement BlogPost repository methods..."
Task: "Implement ProcessingHistory repository methods..."
```

---

## Implementation Strategy

### MVP First (User Stories 1 & 5 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Basic conversion)
4. Complete Phase 4: User Story 5 (Structured metadata)
5. **STOP and VALIDATE**: Test User Stories 1 & 5 independently
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (Basic MVP!)
3. Add User Story 5 → Test independently → Deploy/Demo (Full MVP with metadata!)
4. Add User Story 2 → Test independently → Deploy/Demo (Quality enhancement)
5. Add User Story 3 → Test independently → Deploy/Demo (Content extension)
6. Add User Story 4 → Test independently → Deploy/Demo (Prompt analysis)
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (parsers, extractor, basic workflow)
   - Developer B: User Story 5 (metadata, formatters) - can start after US1 extractor
   - Developer C: Infrastructure (gRPC handlers, CLI commands)
3. After US1/US5 complete:
   - Developer A: User Story 2 (review workflow)
   - Developer B: User Story 3 (extension workflow)
   - Developer C: User Story 4 (prompt analysis)
4. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- All file paths are absolute or relative to repository root as specified in plan.md

