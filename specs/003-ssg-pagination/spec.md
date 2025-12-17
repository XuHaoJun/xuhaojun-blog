# Feature Specification: SSG Pagination

**Feature Branch**: `003-ssg-pagination`  
**Created**: 2025-12-17  
**Status**: Draft  
**Input**: User description: "支援 full SSG，主要是首頁要支援真正的 pagination 且要能靜態產生，現在是設定極大 pageSize 一次載入全部，想要做成類似 hugo page/1 page/2 這樣，首頁 / 是 page/1 alias"

## Clarifications

### Session 2025-12-17

- Q: Which navigation pattern should be implemented (prev/next only, page numbers, or both)? → A: Use existing shadcn pagination component which provides Previous/Next + Page numbers with ellipsis for many pages.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Browse Paginated Blog Posts (Priority: P1)

As a visitor, I want to browse blog posts across multiple pages so that I don't have to load all posts at once and can navigate through content at my own pace.

**Why this priority**: This is the core functionality of the feature. Without paginated navigation, the feature has no value. Users need to be able to see posts divided into manageable pages and navigate between them.

**Independent Test**: Can be fully tested by visiting `/page/1`, `/page/2`, etc. and verifying that each page shows a subset of posts with working navigation links. Delivers immediate value by improving page load times and user experience.

**Acceptance Scenarios**:

1. **Given** the blog has 25 posts and page size is 10, **When** I visit `/page/1`, **Then** I see the first 10 posts (sorted by date descending) and navigation to page 2 and 3.
2. **Given** the blog has 25 posts and page size is 10, **When** I visit `/page/2`, **Then** I see posts 11-20 and navigation to pages 1 and 3.
3. **Given** the blog has 25 posts and page size is 10, **When** I visit `/page/3`, **Then** I see posts 21-25 and navigation to pages 1 and 2, with no "next" link.
4. **Given** I'm on any paginated page, **When** I view the page source, **Then** all content is pre-rendered (no client-side data fetching required for initial display).

---

### User Story 2 - Homepage as First Page Alias (Priority: P1)

As a visitor, I want the homepage `/` to show the same content as `/page/1` so that I have a clean entry point to the blog without a redirect.

**Why this priority**: Essential for user experience and SEO. The homepage is the primary entry point and must display the first page of posts seamlessly.

**Independent Test**: Can be tested by visiting `/` and verifying it shows identical content to `/page/1` without URL change or redirect.

**Acceptance Scenarios**:

1. **Given** I navigate to `/`, **When** the page loads, **Then** I see the same posts as `/page/1` with the URL remaining as `/`.
2. **Given** I'm on the homepage `/`, **When** I click "next page", **Then** I navigate to `/page/2`.
3. **Given** I'm on `/page/2`, **When** I click "previous page", **Then** I navigate to `/page/1` (not `/`).

---

### User Story 3 - SEO-Friendly Pagination (Priority: P2)

As a site owner, I want each paginated page to have proper SEO metadata so that search engines can properly index all blog content.

**Why this priority**: Important for discoverability but the blog functions without it. Can be added after core pagination works.

**Independent Test**: Can be tested by inspecting each page's meta tags and verifying canonical URLs and pagination links are correct.

**Acceptance Scenarios**:

1. **Given** I'm on any paginated page, **When** search engines crawl the page, **Then** they find proper canonical URL pointing to that specific page.
2. **Given** I'm on `/page/2`, **When** I view the page metadata, **Then** I see rel="prev" linking to `/page/1` and rel="next" linking to `/page/3` (if exists).
3. **Given** I'm on the homepage `/`, **When** I view the page metadata, **Then** the canonical URL is `/` and there's only rel="next" (no rel="prev").

---

### User Story 4 - Handle Invalid Page Numbers (Priority: P2)

As a visitor, I want to see appropriate responses when accessing invalid page numbers so that I understand the blog's boundaries.

**Why this priority**: Improves user experience and prevents confusion, but is not critical for basic functionality.

**Independent Test**: Can be tested by navigating to non-existent page numbers and verifying the response.

**Acceptance Scenarios**:

1. **Given** the blog has 3 pages total, **When** I visit `/page/4`, **Then** I see a 404 page.
2. **Given** the blog has 3 pages total, **When** I visit `/page/0`, **Then** I see a 404 page.
3. **Given** I visit `/page/abc`, **When** the page loads, **Then** I see a 404 page.

---

### Edge Cases

- What happens when the blog has zero posts? → Show empty state message on homepage, no other pages exist.
- What happens when posts are added/removed between static builds? → Pages regenerate at next build; stale page numbers may 404 until rebuild.
- What happens when the last page has exactly `pageSize` posts? → No "next" link on last page; pagination numbers are correct.
- What happens when pageSize configuration changes? → All pages regenerate with new distribution at next build.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST generate static HTML pages for each pagination page at build time.
- **FR-002**: System MUST use URL structure `/page/{number}` where `{number}` starts at 1.
- **FR-003**: Homepage `/` MUST display the same content as `/page/1` without redirect.
- **FR-004**: Each paginated page MUST display a configurable number of posts (default: 10 posts per page).
- **FR-005**: Posts MUST be sorted by creation date in descending order (newest first).
- **FR-006**: Each paginated page MUST include navigation with Previous/Next buttons, page number links, and ellipsis for large page counts (using existing shadcn pagination component).
- **FR-007**: System MUST NOT render a "previous" link on the first page.
- **FR-008**: System MUST NOT render a "next" link on the last page.
- **FR-009**: System MUST return 404 for invalid page numbers (non-existent, zero, negative, non-numeric).
- **FR-010**: System MUST calculate total page count based on total posts and page size at build time.

### Key Entities

- **Page**: Represents a single paginated view containing a subset of posts. Has attributes: page number, posts array, total pages, has previous, has next.
- **Pagination Navigation**: UI component showing available pages and current position. Supports previous/next links and optionally direct page number links.

## Assumptions

- The blog uses static site generation (SSG) where all pages are pre-rendered at build time.
- Post data is available from the backend API at build time.
- Posts have a `createdAt` timestamp for sorting.
- The default page size of 10 posts is reasonable for this blog's content and can be adjusted via configuration.
- The URL structure `/page/{number}` is acceptable and no legacy URLs need to be supported.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Initial page load time is under 1 second on standard broadband connection (compared to current behavior loading all posts).
- **SC-002**: All paginated pages are pre-rendered as static HTML (zero client-side API calls for initial content).
- **SC-003**: Lighthouse performance score for paginated pages is 90+ on desktop.
- **SC-004**: Total HTML payload per page is under 100KB (excluding images).
- **SC-005**: Users can navigate from page 1 to any other page in 2 clicks or fewer (via direct page links or sequential navigation).
