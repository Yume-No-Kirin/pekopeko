# Pekopeko Knowledge Management System - UX Specification

## Overview
Pekopeko is a knowledge management system that ingests content from multiple sources (Markdown files, YouTube Shorts, Instagram posts, TikTok videos), extracts atomic canonical notes via LLM processing, and routes them through mandatory human validation before adding them to a structured knowledge base.

## Core Workflow
1. **Ingestion**: Content sources are processed by LLM to extract atomic propositions
2. **Validation**: Human reviewer validates, edits folder paths, and accepts/rejects each note
3. **Storage**: Accepted notes are saved to canonical knowledge folders organized by domain

## Modules

### Dashboard (`pekopeko-dashboard.html`)
- Overview stats: active ingestions, pending proposals, canonical knowledge count, acceptance rate
- Module cards: Validation (active), Ingestion Logs (active), upcoming modules (Analytics, Config, Export, Search)
- Quick navigation to active modules

### Validation (`pekopeko-workflow.html`)
- **Unified view**: All proposed notes visible at once, grouped by source
- **Source header row**: Shows source file/video, metadata (domain, status, note count), bulk actions (accept/reject all)
- **Note rows**: Each canonical note displays:
  - Content (read-only text)
  - Epistemic status badge (Direct vs Inferred)
  - Interactive folder path builder with clickable segments + dropdown menus
  - Individual actions (accept/reject/details)
- **Source types**: Markdown files (📄), YouTube Shorts (🎥), Instagram posts (📱), TikTok videos (🎵)
- **Navigation**: Previous/Next buttons to move between proposals

### Ingestion Logs (`pekopeko-ingestion.html`)
- List of ingestion tasks with filters (status, domain, date range)
- Status tracking: pending, running, completed, failed, skipped_duplicate
- Detailed logs for errors and rejections

### Proposal Detail (`pekopeko-proposal-detail.html`)
- **Note selector**: Dropdown to switch between different canonical notes from different source types
- **Content section**: Editable note content, metadata (domain, type, epistemic status)
- **Interactive folder builder**: Same segment-based UI as validation page
- **Source section**: Dynamic display based on source type:
  - Markdown: file preview, hash
  - YouTube: title, creator, URL, duration, timestamped transcription
  - Instagram: account, post type, caption + audio transcription (for Reels)
  - TikTok: creator, URL, duration, hashtags, Whisper transcription
- **Provenance**: LLM provider, model, temperature, extraction timestamp
- **Validation actions**: Reject (with reason) or Accept (creates canonical file)

## Key UX Patterns

### Interactive Folder Path Builder
- Visual: `[segment ▼] / [segment ▼] / [segment ▼] [+ Ajouter]`
- Click segment → dropdown shows existing folders at that level + "Create new" option
- Click "+ Ajouter" → add new sub-folder to end of path
- Updates `data-path` attribute on change

### Source Types
Each source type displays platform-specific metadata:
- **Markdown**: filename, hash, preview
- **YouTube Short**: title, duration (0:58), URL, timestamped transcription
- **Instagram**: carousel/reel type, caption text, audio transcription (separate sections)
- **TikTok**: duration (2:43), hashtags, Whisper transcription

### Epistemic Status
- **Direct**: Information explicitly stated in source (badge: darker background)
- **Inferred**: Information derived/interpreted from source (badge: lighter background)

### Domain Organization
Knowledge organized into domains: FICTION, LEARNING, RESEARCH, PERSONAL, PUBLISHING

## Navigation Pattern
- Sidebar: Fixed left navigation with sections (Principal, Active Modules, Upcoming Modules)
- Breadcrumbs: Dashboard / Module / Detail
- Icon: Pink pixel-art pig (pekopeko-icon.svg)

## Data Flow
```
Source (MD/YT/IG/TT) 
  → LLM Extraction 
  → Proposed Notes (status: PROPOSED)
  → Human Validation 
  → Canonical Knowledge (status: ACCEPTED/REJECTED)
```

## File Structure
- `pekopeko-dashboard.html` - Landing page
- `pekopeko-workflow.html` - Validation interface
- `pekopeko-ingestion.html` - Ingestion logs
- `pekopeko-proposal-detail.html` - Note detail view
- `pekopeko-icon.svg` - App icon (pink pig)

## Technical Notes
- Examples files in single-page HTML files, self-contained
- JavaScript handles folder path interactions, note switching, validation actions
- No real-time updates (manual refresh workflow)
- Responsive layout with sidebar pattern
- These mockups are static, framework-agnostic maquettes (vanilla HTML/CSS/JS), not a production implementation. The final Pekopeko interface will be implemented in **React** (see `specs/decisions/ADI-009-frontend-framework.md`); the screens and interaction patterns described here (folder path builder, source-type rendering, etc.) carry over as the UX reference, but the HTML/CSS/JS itself does not.
