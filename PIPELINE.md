# PIPELINE

This repo is split into two layers:

1. **Foundation layer (`auto_outline`)**
   - Input: a seed concept
   - Output: a complete story bible
   - Goal: produce something a writer or downstream adapter can actually draft from

2. **Adapter layer (`auto_screenplay`, future `auto_novel`, etc.)**
   - Input: the story bible
   - Output: a format-specific artifact (Fountain screenplay, novel chapters, serial episodes)
   - Goal: turn planning documents into production-ready drafts

## Foundation pipeline

### Step 0 — Init
`auto-outline init --dir my-story`

Creates:
- `seed.txt`
- `.env`
- `state.json`
- `eval_logs/`

### Step 1 — Seed validation
Checks for four required ingredients:
- world differentiator
- central tension
- cost/constraint
- sensory hook

### Step 2 — Initial generation
Dependency order:
1. `world.md`
2. `characters.md`
3. `voice.md`
4. `MYSTERY.md`
5. `outline.md`
6. `canon.md`
7. `foreshadowing.md`

### Step 3 — Evaluation
Four lenses:
- **foundation judge** — overall quality + dimension scores
- **mechanical slop detector** — regex-based AI-writing detection
- **consistency checker** — contradictions across files
- **reader panel** — 4-perspective qualitative review

### Step 4 — Weakest-dimension targeting
The lowest-scoring dimension is regenerated.
Examples:
- weak `world_depth` → regenerate `world.md`
- weak `character_depth` → regenerate `characters.md`
- weak `outline_completeness` → regenerate `outline.md`

### Step 5 — Keep / discard
After regeneration, the tool runs a quick re-evaluation.
- if score improved or held: keep the new version
- if score dropped: restore the old version

### Step 6 — Stop conditions
The loop stops when:
- `foundation_score >= 7.5`
- `lore_score >= 7.0`

Or when:
- max iterations reached
- score plateaus across iterations

## Adapter pipeline (planned)

### `auto_screenplay`
Target flow:
1. Read story bible
2. Map outline scenes to screenplay scenes
3. Generate structured scene content
4. Emit Fountain
5. Evaluate pacing, dialogue distinctiveness, visuality, and page count
6. Export to PDF / FDX

## Design principles

- Different model for generation vs evaluation
- State lives with the project (`state.json`)
- Output files are human-readable markdown
- Evaluation evidence is preserved (`eval_logs/`, `results.tsv`)
- No OpenClaw dependency in core runtime
