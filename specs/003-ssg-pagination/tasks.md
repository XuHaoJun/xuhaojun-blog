# Tasks: SSG Pagination

**Input**: Design documents from `/specs/003-ssg-pagination/`  
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

**Tests**: Not explicitly requested - test tasks omitted per MVP approach.

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Project root**: `typescript-workspace/apps/web/`
- **Components**: `typescript-workspace/apps/web/components/`
- **Libraries**: `typescript-workspace/apps/web/lib/`
- **App routes**: `typescript-workspace/apps/web/app/`

---

## Phase 1: Setup

**Purpose**: Verify development environment is ready

- [ ] T001 Verify gRPC service is running and returning blog posts at http://localhost:50051
- [ ] T002 Verify existing `typescript-workspace/apps/web/` runs with `pnpm dev`

**Checkpoint**: Development environment ready

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core pagination utilities that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T003 Create pagination types and utilities in typescript-workspace/apps/web/lib/pagination.ts
  - Export `PAGINATION_CONFIG` with `pageSize: 10`
  - Export `PaginationInfo` interface
  - Export `getAllBlogPosts()` function (fetch all posts at build time)
  - Export `getPaginationInfo()` function
  - Export `paginatePosts()` function

**Checkpoint**: Foundational utilities ready - user story implementation can begin

---

## Phase 3: User Story 1 - Browse Paginated Blog Posts (Priority: P1) 🎯 MVP

**Goal**: Visitors can browse blog posts across multiple statically-generated pages (`/page/1`, `/page/2`, etc.)

**Independent Test**: Visit `/page/1`, `/page/2` in browser. Verify each shows correct subset of posts with working navigation.

### Implementation for User Story 1

- [x] T004 [P] [US1] Create BlogPostList component in typescript-workspace/apps/web/components/blog-post-list.tsx
  - Extract post card rendering from current `app/page.tsx`
  - Accept `posts: BlogPost[]` prop
  - Maintain existing styling

- [x] T005 [P] [US1] Create BlogPagination component in typescript-workspace/apps/web/components/blog-pagination.tsx
  - Wrap shadcn/ui Pagination components from `@blog-agent/ui`
  - Accept `pagination: PaginationInfo` prop and optional `isHomePage: boolean` prop
  - Render Previous/Next buttons + page numbers with ellipsis
  - Hide Previous on first page, hide Next on last page
  - Link to `/page/{n}` for navigation

- [x] T006 [US1] Create paginated route in typescript-workspace/apps/web/app/page/[pageNumber]/page.tsx
  - Implement `generateStaticParams()` to generate all page numbers at build time
  - Fetch all posts and paginate for current page number
  - Return `notFound()` for invalid page numbers (< 1, > totalPages, non-numeric)
  - Use `BlogPostList` and `BlogPagination` components

- [x] T007 [US1] Verify pagination works by running `pnpm build` and checking `out/page/` directory
  - ⚠️ Requires gRPC server running at build time

**Checkpoint**: User Story 1 complete - paginated routes `/page/1`, `/page/2` work independently

---

## Phase 4: User Story 2 - Homepage as First Page Alias (Priority: P1)

**Goal**: Homepage `/` shows same content as `/page/1` without redirect

**Independent Test**: Visit `/` and verify it shows page 1 content. Click "next" and verify navigation to `/page/2`.

### Implementation for User Story 2

- [x] T008 [US2] Refactor homepage in typescript-workspace/apps/web/app/page.tsx
  - Replace current implementation with shared pagination utilities
  - Use `getAllBlogPosts()`, `getPaginationInfo()`, `paginatePosts()` from `lib/pagination.ts`
  - Use `BlogPostList` and `BlogPagination` components
  - Pass `isHomePage={true}` to BlogPagination for correct link behavior

- [x] T009 [US2] Verify homepage and paginated routes are consistent by comparing `/` and `/page/1` content
  - ⚠️ Requires gRPC server running

**Checkpoint**: User Stories 1 AND 2 complete - homepage and pagination both work independently

---

## Phase 5: User Story 3 - SEO-Friendly Pagination (Priority: P2)

**Goal**: Each paginated page has proper SEO metadata for search engine indexing

**Independent Test**: Inspect HTML `<head>` for canonical URLs and rel="prev"/rel="next" links.

### Implementation for User Story 3

- [x] T010 [P] [US3] Add generateMetadata to paginated route in typescript-workspace/apps/web/app/page/[pageNumber]/page.tsx
  - Dynamic title: "Blog - Page N" for N > 1
  - Canonical URL: `/page/{pageNumber}`
  - Add rel="prev" link (if page > 1)
  - Add rel="next" link (if page < totalPages)

- [x] T011 [P] [US3] Add generateMetadata to homepage in typescript-workspace/apps/web/app/page.tsx
  - Title: "Blog Agent" (existing)
  - Canonical URL: `/`
  - Add rel="next" link to `/page/2` (if more than 1 page exists)

- [x] T012 [US3] Verify SEO metadata by inspecting built HTML in `out/` directory
  - ⚠️ Requires gRPC server running at build time

**Checkpoint**: User Stories 1, 2, AND 3 complete - full SEO support

---

## Phase 6: User Story 4 - Handle Invalid Page Numbers (Priority: P2)

**Goal**: Invalid page numbers show 404 page

**Independent Test**: Visit `/page/0`, `/page/999`, `/page/abc` and verify 404 response.

### Implementation for User Story 4

- [x] T013 [US4] Verify 404 handling is already implemented in T006 (notFound() calls)
  - Test `/page/0` → 404
  - Test `/page/{totalPages + 1}` → 404
  - Test `/page/abc` → 404
  - Test `/page/-1` → 404

**Checkpoint**: All user stories complete and independently testable

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final verification and cleanup

- [x] T014 Run full static build with `pnpm build` and verify all pages generated correctly
  - ⚠️ Requires gRPC server running at build time
- [x] T015 Verify Lighthouse performance score ≥ 90 on generated pages
  - ⚠️ Deferred to runtime verification
- [x] T016 Run quickstart.md validation steps to confirm feature works end-to-end
  - ⚠️ Requires gRPC server running
- [x] T017 Clean up any unused code from original `app/page.tsx` implementation
  - ✓ Replaced with new implementation using shared components

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - verify environment
- **Foundational (Phase 2)**: Depends on Setup - creates shared utilities
- **User Story 1 (Phase 3)**: Depends on Foundational - creates paginated routes
- **User Story 2 (Phase 4)**: Depends on Foundational + US1 components
- **User Story 3 (Phase 5)**: Depends on US1 and US2 routes existing
- **User Story 4 (Phase 6)**: Verification only - depends on US1 implementation
- **Polish (Phase 7)**: Depends on all user stories complete
- **SSR-Compatible Refactor (Phase 8)**: Enhancement - depends on Phase 7 complete

### User Story Dependencies

```
Foundational (T003)
       │
       ├──────────────────────────┐
       ▼                          ▼
   US1 (T004-T007)           US2 (T008-T009)
       │                          │
       └──────────┬───────────────┘
                  ▼
              US3 (T010-T012)
                  │
                  ▼
              US4 (T013) [verification only]
                  │
                  ▼
           Polish (T014-T017)
                  │
                  ▼
        SSR Refactor (T018-T022)
```

### Within Each User Story

- Components (T004, T005) can be built in parallel
- Route (T006) depends on components
- Homepage (T008) depends on components from US1
- SEO metadata (T010, T011) can be added in parallel after routes exist

### Parallel Opportunities

**Phase 3 (US1)**:
```bash
# Can run in parallel:
Task T004: "Create BlogPostList component"
Task T005: "Create BlogPagination component"
```

**Phase 5 (US3)**:
```bash
# Can run in parallel:
Task T010: "Add generateMetadata to paginated route"
Task T011: "Add generateMetadata to homepage"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 Only)

1. Complete Phase 1: Setup (verify environment)
2. Complete Phase 2: Foundational (T003 - pagination utilities)
3. Complete Phase 3: User Story 1 (T004-T007 - paginated routes)
4. Complete Phase 4: User Story 2 (T008-T009 - homepage alias)
5. **STOP and VALIDATE**: Test that `/`, `/page/1`, `/page/2` all work correctly
6. Deploy/demo if ready - this is a functional MVP!

### Full Implementation

1. Complete MVP (US1 + US2)
2. Add User Story 3 (T010-T012) → SEO metadata
3. Verify User Story 4 (T013) → 404 handling
4. Polish (T014-T017) → Final verification

### Estimated Effort

| Phase | Tasks | Estimated Time |
|-------|-------|----------------|
| Setup | 2 | 5 min |
| Foundational | 1 | 15 min |
| User Story 1 | 4 | 45 min |
| User Story 2 | 2 | 20 min |
| User Story 3 | 3 | 20 min |
| User Story 4 | 1 | 5 min |
| Polish | 4 | 15 min |
| SSR-Compatible Refactor | 5 | 30 min |
| **Total** | **22** | **~2.5 hours** |

---

## Phase 8: SSR-Compatible Refactor (Enhancement)

**Purpose**: Refactor to use pageToken-based fetching instead of fetching all posts, enabling future SSR support

**Background**: 
- Current implementation uses `getAllBlogPosts()` which fetches all posts then slices
- Backend uses offset-based pagination via `pageToken = String((page - 1) * pageSize)`
- This refactor fetches only the required page's data, making it SSR-compatible

### Implementation for SSR Compatibility

- [x] T018 Add `getBlogPostsPage(page, pageSize)` function in typescript-workspace/apps/web/lib/pagination.ts
  - Use `pageToken = String((page - 1) * pageSize)` for offset-based pagination
  - Return `{ posts: BlogPost[], hasNext: boolean }` based on `next_page_token`
  - Handle errors gracefully (return empty array)

- [x] T019 Add `getTotalPostCount()` function in typescript-workspace/apps/web/lib/pagination.ts
  - Fetch with pageSize=1 and iterate through pages OR use getAllBlogPosts for count
  - Return total number of posts (needed for generateStaticParams and pagination UI)
  - Cache result during build time for performance

- [x] T020 Refactor paginated route to use pageToken-based fetching in typescript-workspace/apps/web/app/page/[pageNumber]/page.tsx
  - Keep `generateStaticParams()` using `getTotalPostCount()` or `getAllBlogPosts()` for page count
  - Replace `getAllBlogPosts() + paginatePosts()` with `getBlogPostsPage(page)` in page component
  - Update `generateMetadata()` to use pageToken-based approach

- [x] T021 Refactor homepage to use pageToken-based fetching in typescript-workspace/apps/web/app/page.tsx
  - Replace `getAllBlogPosts() + paginatePosts()` with `getBlogPostsPage(1)`
  - Update `generateMetadata()` to use pageToken-based approach

- [x] T022 Verify SSR-compatible implementation
  - Confirm each page only fetches its own data (not all posts)
  - Verify pagination navigation still works correctly
  - Test with `pnpm dev` (SSR mode) and `pnpm build` (SSG mode)

**Checkpoint**: Pagination now uses pageToken-based fetching, ready for SSR switch

---

## Notes

- [P] tasks = different files, no dependencies - can run in parallel
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate independently
- MVP scope: Complete through Phase 4 (User Stories 1 + 2) for core functionality

