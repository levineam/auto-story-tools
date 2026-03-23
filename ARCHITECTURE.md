# Auto-Outline & Auto-Screenplay: Architecture Spec

**SUP-198** — Research & Architecture  
**Date:** 2026-03-22  
**Author:** Michael  
**Status:** Draft

---

## 1. Overview

This project builds two complementary AI pipelines that share a common story representation:

- **auto-outline** — generates structured story outlines from seed concepts (novel, screenplay, serial)
- **auto-screenplay** — generates Fountain-format screenplays from outlines

Both consume and produce a **shared story bible** — a format-agnostic intermediate representation that future adapters (auto-novel, auto-serial) can also use.

The architecture is heavily informed by NousResearch/autonovel's production pipeline, adapted for multi-format output and provider flexibility.

---

## 2. Shared Story Bible Schema

The story bible is the project's core data structure. It represents everything about a story except the final prose/dialogue. All adapters (outline, screenplay, novel) read from and write back to this schema.

### 2.1 File Layout (per-project)

```
project-root/
├── story-bible/
│   ├── seed.md                   # Original concept (user-provided or generated)
│   ├── world.md                  # World bible (settings, rules, history)
│   ├── characters.md             # Character registry
│   ├── outline.md                # Plot structure + beat sheet
│   ├── canon.md                  # Hard facts database (consistency anchor)
│   ├── voice.md                  # Voice identity + guardrails
│   ├── mystery.md                # Central mystery / dramatic question (author-only)
│   └── foreshadowing-ledger.md   # Plant/payoff tracking table
├── output/                       # Adapter-specific output
│   ├── screenplay/               # .fountain files, .pdf exports
│   ├── novel/                    # chapter .md files, .tex, .pdf
│   └── serial/                   # episode .md files
├── eval-logs/                    # Evaluation results (JSON)
├── state.json                    # Pipeline state + resumability
└── results.tsv                   # Experiment log (keep/discard decisions)
```

### 2.2 Schema: `seed.md`

Free-form markdown. Must contain at minimum:
- **World differentiator** — what makes this world distinct
- **Central tension** — the core conflict
- **Cost/constraint** — what's at stake, what limits the protagonist
- **Sensory hook** — a concrete image or moment that anchors the concept
- **Target format** — `novel | screenplay | serial` (determines which adapter runs)

### 2.3 Schema: `characters.md`

```markdown
# Characters

## CHARACTER_NAME (POV | non-POV)

### Identity
- **Role:** protagonist / antagonist / supporting / minor
- **Age:** 
- **Occupation/Position:**

### Arc (Wound/Want/Need/Lie)
- **Ghost:** [backstory event that caused the wound]
- **Wound:** [ongoing emotional damage]
- **Lie:** [false belief adopted to cope — one sentence]
- **Truth:** [direct opposite of the Lie — one sentence]
- **Want:** [external goal driven by the Lie]
- **Need:** [internal truth that will actually heal]
- **Arc type:** positive | negative | flat

### Three Sliders (0-10)
- **Proactivity:** [score] — [justification]
- **Likability:** [score] — [justification]
- **Competence:** [score] — [justification]

### Speech Pattern
- **Vocabulary level:** [simple / educated / technical / archaic]
- **Sentence style:** [terse / flowing / fragmented / formal]
- **Contractions:** [always / sometimes / never]
- **Verbal tics:** [specific catchphrases or patterns]
- **Metaphor domain:** [what domain their metaphors draw from]
- **Directness:** [direct / indirect / passive-aggressive]

### Relationships
| Character | Nature (Act 1) | Evolution (Act 2) | Resolution (Act 3) |
|-----------|---------------|-------------------|-------------------|
| Name      | description   | description        | description        |

### Foreshadowing
| Planted (Ch/Scene) | What is planted | Payoff (Ch/Scene) |
|--------------------|-----------------|-------------------|
```

### 2.4 Schema: `outline.md`

```markdown
# Outline

## Meta
- **Total chapters/scenes:** 
- **Target word count / page count:**
- **Act structure:** [3-act | 5-act | custom]

## Themes
- Theme 1: [description]
- Theme 2: [description]

## Beat Sheet (Save the Cat)

| Beat | % Mark | Chapter/Scene | What Happens |
|------|--------|---------------|--------------|
| Opening Image | 0-1% | | |
| Theme Stated | ~5% | | |
| Setup | 1-10% | | |
| Catalyst | ~11% | | |
| Debate | 11-23% | | |
| Break Into Two | ~23% | | |
| B Story | ~27% | | |
| Fun and Games | 26-50% | | |
| Midpoint | ~50% | | |
| Bad Guys Close In | 50-68% | | |
| All Is Lost | ~68% | | |
| Dark Night of the Soul | 68-77% | | |
| Break Into Three | ~77% | | |
| Finale | 77-97% | | |
| Final Image | ~99% | | |

## MICE Threads

| Thread | Type | Opens (Ch/Scene) | Closes (Ch/Scene) | Status |
|--------|------|-------------------|--------------------|--------|
| | milieu/inquiry/character/event | | | open/closed |

Note: MICE threads close in REVERSE order of opening.

## Chapters / Scenes

### Act 1: [Title]

#### Ch/Scene N: "Title" (POV, target length)
- **BEATS:**
  1. ...
- **Try-fail cycle:** [yes-but | no-and | no-but | yes-and]
- **PLANTS:** (foreshadowing seeded here)
  - description → payoff Ch/Scene M
- **HARVESTS:** (foreshadowing paid off here)
  - description ← planted Ch/Scene N
- **EMOTIONAL ARC:** start → end
- **STATUS:** unwritten | drafted (vN, score X.X) | revised

### Act 2: [Title]
...

### Act 3: [Title]
...

## Foreshadowing Ledger

| ID | Planted | Payoff | Thread | Status |
|----|---------|--------|--------|--------|
```

### 2.5 Schema: `world.md`

```markdown
# World Bible

## Cosmology & History
[Origin, major historical events, calendar system, timeline]

## Magic System / Speculative Element
### Hard Rules (NEVER violate)
[Costs, limits, absolute constraints]

### Soft Rules (can bend)
[Conventions, norms, known exceptions]

## Geography
[Major locations, travel times/distances, key landmarks]

## Factions & Politics
[Power structures, conflicts, alliances, economies]

## Cultural Details
[Languages, customs, religions, food, clothing, taboos]

## Internal Consistency Rules
[Explicit constraints the evaluator checks against]
```

### 2.6 Schema: `canon.md`

A flat append-only database of hard facts. Every fact established anywhere (world, characters, drafts) gets an entry here. The evaluator checks new content against canon for contradictions.

```markdown
# Canon Database

| ID | Fact | Source | Category |
|----|------|--------|----------|
| C001 | The river Kael flows north-to-south | world.md | geography |
| C002 | Elena lost her left hand at age 14 | characters.md | character |
| C003 | Magic costs the user's body heat | world.md | magic |
```

### 2.7 Schema: `voice.md`

```markdown
# Voice

## Part 1: Guardrails (permanent across all projects)
- Reference: ANTI-SLOP.md and ANTI-PATTERNS.md rules apply
- Banned word tiers: see evaluation framework
- Structural slop patterns: see evaluation framework

## Part 2: Project Voice (discovered during foundation)
- **Register:** [mythic / spare / warm / cold / whimsical / noir / etc.]
- **Sentence rhythm:** [description]
- **POV style:** [close third / first / omniscient / etc.]

### Exemplar Passages
[2-3 paragraphs that exemplify the target voice]

### Anti-Exemplar Passages
[2-3 paragraphs that show what NOT to sound like]
```

### 2.8 Schema: `state.json`

```json
{
  "version": 1,
  "projectId": "uuid",
  "format": "screenplay",
  "phase": "foundation",
  "currentFocus": null,
  "iteration": 0,
  "scores": {
    "foundation": 0.0,
    "lore": 0.0,
    "overall": 0.0
  },
  "progress": {
    "scenesTotal": 0,
    "scenesDrafted": 0,
    "scenesRevised": 0
  },
  "debts": [],
  "lastUpdated": "ISO-8601"
}
```

**Debts** are logged when drafting reveals upstream issues:
```json
{
  "trigger": "scene_12: character motivation contradicts established backstory",
  "affected": ["characters.md", "scene_08"],
  "status": "pending"
}
```

---

## 3. Tooling Survey & Decisions

### 3.1 Fountain Format (Screenplay Output)

**Decision: Use `screenplay-tools` (JS) as primary Fountain parser/writer.**

| Library | Language | Fountain→Parse | Parse→Fountain | FDX | PDF | Maintained |
|---------|----------|---------------|---------------|-----|-----|------------|
| **screenplay-tools** | JS/Python/C++ | ✅ | ✅ | ✅ | ❌ | ✅ (Jan 2026) |
| screenplain | Python | ✅ | ❌ | ✅ | ✅ | ✅ (active) |
| wrap | Rust CLI | ✅ | ❌ | ❌ | ✅ | ✅ (active) |

**Rationale:**
- `screenplay-tools` has native JS support (fits our Node.js stack), handles both read and write, supports FDX for Final Draft interop
- For PDF export: shell out to `screenplain` (Python) or `wrap` (Rust) as a post-processing step — both take Fountain input and produce professional PDFs
- The pipeline generates Fountain as the canonical output format; PDF/FDX are secondary exports

**Integration path:**
1. AI generates scene content as structured JSON (scene heading, action, dialogue blocks)
2. Our adapter converts structured JSON → Fountain text using `screenplay-tools` Writer
3. For PDF: pipe Fountain through `screenplain screenplay.fountain screenplay.pdf`
4. For FDX (Final Draft): use `screenplay-tools` FDX.Writer

### 3.2 LaTeX (Novel Output)

**Decision: Port autonovel's LaTeX template for novel adapter (future).**

Autonovel uses EB Garamond + trade paperback dimensions. This stays in the novel adapter package and is not needed for screenplay work.

### 3.3 Mechanical Evaluation (Anti-Slop Scoring)

**Decision: Port autonovel's `evaluate.py` regex engine to TypeScript.**

The mechanical scorer is pure regex — no LLM needed. It detects:
- **Tier 1 banned words** (25 words: delve, utilize, leverage, etc.)
- **Tier 2 suspicious clusters** (24 words: robust, comprehensive, seamless, etc. — 3+ in one paragraph = flag)
- **Tier 3 filler phrases** (17 patterns: "it's worth noting", "let's dive into", etc.)
- **Fiction AI tells** (15 patterns: "a wave of X washed over", "eyes widened", "heart pounded in chest", etc.)
- **Structural AI tics** (6 patterns: "not just X, but Y", "I'm not saying X. I'm saying Y", etc.)
- **Telling patterns** (emotion-telling vs showing)
- **Em-dash density** (per 1000 words)
- **Sentence length coefficient of variation** (higher = more human)
- **Transition opener ratio** (fraction of paragraphs starting with However/Furthermore/etc.)

Output: a `slop_penalty` score (0-10, where 0 = clean, 10 = pure slop) plus detailed hit lists.

The LLM-judge evaluation (separate from mechanical) uses a different, more expensive model than the writer to avoid self-congratulation. In our case: writer uses Sonnet-class, judge uses Opus-class (or GPT for diversity).

### 3.4 Provider Abstraction

**Decision: Three auth paths, abstracted behind a `StoryProvider` interface.**

```typescript
interface StoryProvider {
  generate(params: GenerateParams): Promise<GenerateResult>
  evaluate(params: EvaluateParams): Promise<EvaluateResult>
}

interface GenerateParams {
  systemPrompt: string
  userPrompt: string
  model?: string          // override default
  temperature?: number
  maxTokens?: number
  responseFormat?: 'text' | 'json'
}
```

**Auth paths:**

| Path | How it works | When to use |
|------|-------------|------------|
| **Anthropic API key** | `ANTHROPIC_API_KEY` env var, direct SDK call | Standalone CLI, highest quality |
| **OpenAI API key** | `OPENAI_API_KEY` env var, direct SDK call | Standalone CLI, GPT preference |
| **OpenClaw OAuth** | OpenClaw routes the request through its model proxy | Running as OpenClaw skill |

The provider is selected at runtime based on available env vars, with a priority order: explicit `--provider` flag > env vars > OpenClaw detection.

For evaluation, the provider deliberately uses a different model family than the writer (autonovel's insight: judge should be harsher and independent).

---

## 4. Repo Structure

**Decision: Monorepo with shared packages.**

```
auto-story/
├── packages/
│   ├── shared/                    # Shared story bible schema + utilities
│   │   ├── src/
│   │   │   ├── schema/            # TypeScript types for all bible docs
│   │   │   ├── evaluate/          # Mechanical slop scorer (ported from autonovel)
│   │   │   ├── providers/         # StoryProvider abstraction + implementations
│   │   │   ├── state/             # state.json management + resumability
│   │   │   └── canon/             # Canon database operations
│   │   ├── templates/             # Blank story bible templates
│   │   │   ├── seed.md
│   │   │   ├── world.md
│   │   │   ├── characters.md
│   │   │   ├── outline.md
│   │   │   ├── canon.md
│   │   │   ├── voice.md
│   │   │   └── mystery.md
│   │   └── craft/                 # Craft reference docs (ported from autonovel)
│   │       ├── CRAFT.md           # Plot, character, worldbuilding frameworks
│   │       ├── ANTI-SLOP.md       # Word-level AI tell detection
│   │       └── ANTI-PATTERNS.md   # Structural AI pattern detection
│   │
│   ├── auto-outline/              # Outline generation pipeline
│   │   ├── src/
│   │   │   ├── foundation/        # Phase 1: seed → world, characters, outline
│   │   │   ├── refine/            # Iterative outline improvement loop
│   │   │   └── cli.ts             # CLI entry point
│   │   └── package.json
│   │
│   └── auto-screenplay/           # Screenplay generation pipeline
│       ├── src/
│       │   ├── adapter/           # outline → Fountain scene generation
│       │   ├── export/            # Fountain → PDF/FDX export
│       │   └── cli.ts             # CLI entry point
│       └── package.json
│
├── package.json                   # Workspace root (pnpm workspaces)
├── tsconfig.json                  # Shared TS config
└── README.md
```

**Rationale for monorepo:**
- `shared` changes often during early development — separate repos would mean constant version bumps
- The schema is the contract between packages; co-location makes it easy to evolve atomically
- pnpm workspaces handle dependency linking cleanly
- Future adapters (auto-novel, auto-serial) just add a new `packages/` entry

**Language: TypeScript (Node.js)**
- Matches the OpenClaw skill ecosystem
- `screenplay-tools` has native JS support
- Autonovel's Python tools are straightforward to port (httpx → fetch, regex → regex, Anthropic SDK → provider abstraction)

---

## 5. Pipeline Phases (Shared)

Both auto-outline and auto-screenplay follow autonovel's phase model, adapted for their scope:

### Phase 0: Setup
- User provides `seed.md` (or generates via seed prompts)
- Initialize `state.json`, create project directory from templates
- Select target format (novel/screenplay/serial)

### Phase 1: Foundation (auto-outline's main job)
- **Loop** until `foundation_score > 7.5 AND lore_score > 7.0`:
  1. Generate/refine world.md
  2. Generate/refine characters.md (Wound/Want/Need/Lie, sliders, speech)
  3. Generate/refine outline.md (Save the Cat beats, MICE threads)
  4. Voice discovery (trial passages → select → exemplars)
  5. Build canon.md (cross-reference all hard facts)
  6. Evaluate (mechanical + LLM judge)
  7. Keep/discard based on score delta (git commit if improved)
  8. Identify weakest dimension → target next iteration

### Phase 2: Drafting (auto-screenplay's main job)
- For each scene in outline order:
  1. Load context: voice + world + characters + this scene's outline + adjacent scenes
  2. Generate scene (structured JSON → Fountain)
  3. Evaluate (mechanical slop + LLM judge)
  4. Keep/discard based on score threshold (>6.0)
  5. Extract new canon entries
  6. Log to results.tsv

### Phase 3: Revision (shared, future)
- Adversarial editing, reader panel evaluation, targeted improvements
- Same pattern as autonovel but adapted per format

---

## 6. Screenplay-Specific Considerations

### Scene Structure (Fountain elements the AI must produce)
- **Scene heading:** INT./EXT. + LOCATION - TIME
- **Action lines:** Scene description (show, don't tell)
- **Character cue:** CHARACTER NAME (uppercase)
- **Parenthetical:** (acting direction) — use sparingly
- **Dialogue:** The spoken words
- **Transitions:** CUT TO:, FADE OUT., etc. — use sparingly (modern style avoids most)

### Page Count Target
- Industry standard: 1 page ≈ 1 minute of screen time
- Feature film: 90-120 pages
- TV pilot (1 hour): 55-65 pages
- TV pilot (30 min): 25-35 pages

### Anti-Patterns Specific to AI Screenplays
- **Over-directing:** too many parentheticals, camera directions, actor notes
- **Novel-brain:** action lines reading like novel prose instead of visual directions
- **On-the-nose dialogue:** characters saying exactly what they mean/feel
- **Talking heads:** scenes that are just dialogue with no visual action
- **Scene slugline abuse:** too many micro-locations when fewer would work

---

## 7. Key Design Decisions Summary

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Repo structure | Monorepo (pnpm workspaces) | Schema co-evolution, single version of truth |
| Language | TypeScript/Node.js | OpenClaw ecosystem, screenplay-tools JS support |
| Screenplay format | Fountain (.fountain) | Industry standard plaintext, multiple export paths |
| Fountain library | screenplay-tools (JS) | Multi-format, read+write, actively maintained |
| PDF export | screenplain (Python CLI) | Proven, professional output, easy to shell out to |
| Story bible format | Markdown files per concern | Human-readable, git-diffable, LLM-friendly |
| State management | state.json per project | Autonovel-proven, simple, resumable |
| Evaluation | Mechanical regex + LLM judge | Two-layer: cheap pass first, expensive pass second |
| Provider abstraction | StoryProvider interface | Supports Anthropic, OpenAI, and OpenClaw OAuth |
| Anti-slop framework | Ported from autonovel evaluate.py | Battle-tested on a 75k-word production novel |

---

## 8. Example: Story Bible in JSON/YAML

For programmatic consumers, the markdown story bible can be parsed into a structured representation. Here's the canonical TypeScript schema:

```typescript
interface StoryBible {
  seed: {
    concept: string
    worldDifferentiator: string
    centralTension: string
    costConstraint: string
    sensoryHook: string
    targetFormat: 'novel' | 'screenplay' | 'serial'
  }

  world: {
    cosmology: string
    magicSystem: {
      hardRules: string[]
      softRules: string[]
    }
    geography: string
    factions: string
    culture: string
    consistencyRules: string[]
  }

  characters: Character[]

  outline: {
    meta: {
      totalScenes: number
      targetLength: string      // "110 pages" or "80000 words"
      actStructure: string
    }
    themes: string[]
    beatSheet: BeatSheetEntry[]
    miceThreads: MiceThread[]
    scenes: Scene[]
    foreshadowingLedger: ForeshadowingEntry[]
  }

  canon: CanonEntry[]

  voice: {
    register: string
    sentenceRhythm: string
    povStyle: string
    exemplars: string[]
    antiExemplars: string[]
  }

  mystery: {
    centralQuestion: string
    layers: string[]
    resolution: string
  }
}

interface Character {
  name: string
  role: 'protagonist' | 'antagonist' | 'supporting' | 'minor'
  pov: boolean
  identity: {
    age: string
    occupation: string
  }
  arc: {
    ghost: string
    wound: string
    lie: string
    truth: string
    want: string
    need: string
    arcType: 'positive' | 'negative' | 'flat'
  }
  sliders: {
    proactivity: number    // 0-10
    likability: number     // 0-10
    competence: number     // 0-10
  }
  speechPattern: {
    vocabularyLevel: string
    sentenceStyle: string
    contractions: 'always' | 'sometimes' | 'never'
    verbalTics: string[]
    metaphorDomain: string
    directness: string
  }
  relationships: Relationship[]
  foreshadowing: ForeshadowingEntry[]
}

interface Scene {
  id: string
  act: number
  title: string
  pov: string
  targetLength: string
  beats: string[]
  tryFailCycle: 'yes-but' | 'no-and' | 'no-but' | 'yes-and'
  plants: ForeshadowingEntry[]
  harvests: ForeshadowingEntry[]
  emotionalArc: { start: string; end: string }
  status: 'unwritten' | 'drafted' | 'revised'
  score?: number
  version?: number
}

interface BeatSheetEntry {
  beat: string
  percentMark: string
  sceneId: string
  description: string
}

interface MiceThread {
  name: string
  type: 'milieu' | 'inquiry' | 'character' | 'event'
  opens: string        // scene ID
  closes: string       // scene ID
  status: 'open' | 'closed'
}

interface ForeshadowingEntry {
  id: string
  plantedIn: string    // scene/chapter ID
  payoffIn: string     // scene/chapter ID
  description: string
  status: 'planted' | 'paid-off' | 'abandoned'
}

interface CanonEntry {
  id: string
  fact: string
  source: string
  category: string
}

interface Relationship {
  character: string
  act1: string
  act2: string
  act3: string
}
```

---

## 9. Open Questions (for Andrew)

1. **Naming** — Is `auto-story` the repo name, or do you prefer something else?
2. **Initial scope** — Start with auto-outline only (SUP-199), or scaffold both packages from the start?
3. **Voice discovery** — Should auto-screenplay reuse the outline's voice, or run its own discovery pass for screenplay-specific register?
4. **OpenClaw skill packaging** — One skill per adapter (auto-outline skill, auto-screenplay skill) or one combined skill?
5. **Evaluation models** — Confirm: writer = Sonnet-class, judge = Opus-class? Or let the user configure?

---

## 10. References

- [NousResearch/autonovel](https://github.com/NousResearch/autonovel) — PIPELINE.md, CRAFT.md, ANTI-SLOP.md, program.md, evaluate.py
- [Fountain syntax spec](https://fountain.io/syntax/)
- [screenplay-tools](https://github.com/wildwinter/screenplay-tools) — JS/Python/C++ Fountain parser + writer + FDX support
- [screenplain](https://github.com/vilcans/screenplain) — Python Fountain→PDF/HTML/FDX
- [wrap](https://github.com/eprovst/wrap) — Rust Fountain→PDF/HTML CLI
- Save the Cat (Blake Snyder) — beat sheet structure
- Sanderson's Laws of Magic — worldbuilding framework
- K.M. Weiland's character arc framework — Wound/Want/Need/Lie
- Orson Scott Card / Sanderson — MICE quotient
