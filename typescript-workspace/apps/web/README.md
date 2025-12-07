# Blog Agent Web UI

Next.js web application for displaying blog posts generated from AI conversations.

## Features

- **Static Site Generation**: Uses Next.js App Router with static generation for optimal performance
- **Blog List Page**: Displays all processed blog posts with metadata
- **Blog Detail Page**: Shows full blog post content with Markdown rendering
- **gRPC Integration**: Connects to Blog Agent service via Connect-Web
- **Responsive Design**: TailwindCSS-based responsive layout
- **Dark Mode Support**: Built-in dark mode support (ready for Phase 11)

## Setup

1. Install dependencies:
   ```bash
   cd typescript-workspace
   pnpm install
   ```

2. Set environment variables (optional):
   ```bash
   export GRPC_SERVER_URL=http://localhost:50051
   ```

3. Run development server:
   ```bash
   cd apps/web
   pnpm dev
   ```

4. Build for production:
   ```bash
   pnpm build
   ```

## Project Structure

```
apps/web/
├── app/                    # Next.js App Router
│   ├── layout.tsx         # Root layout
│   ├── page.tsx           # Blog list page
│   └── blog/
│       └── [id]/
│           └── page.tsx   # Blog detail page
├── components/            # React components
│   ├── markdown-renderer.tsx
│   └── blog-metadata.tsx
├── lib/                   # Utilities
│   ├── grpc-client.ts    # gRPC client configuration
│   └── utils.ts          # Helper functions
└── styles/               # Global styles
    └── globals.css
```

## Static Generation

The application uses Next.js static site generation:

- Blog list page: Revalidates every hour (`revalidate: 3600`)
- Blog detail pages: Pre-generated at build time via `generateStaticParams`
- gRPC client: Configured for server-side use during build

## Next Steps (Phase 11)

Phase 11 will add the Side-by-Side UI/UX features:
- Desktop 70/30 dual-column layout
- Sticky sidebar with prompt clinic cards
- Intersection Observer for scroll tracking
- Mobile accordion mode
- Copy to clipboard functionality

