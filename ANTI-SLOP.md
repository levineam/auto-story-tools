# ANTI-SLOP REFERENCE

A field guide to AI-generated writing patterns. Use this to catch and kill slop in any text.

Adapted from [NousResearch/autonovel](https://github.com/NousResearch/autonovel)'s ANTI-SLOP.md,
which drew from [slop-forensics](https://github.com/sam-paech/slop-forensics) and
[EQ-Bench Slop Score](https://eqbench.com/slop-score.html).

---

## BANNED WORDS AND PHRASES

### Tier 1: Kill on sight

These almost never appear in casual human writing. If you see one, rewrite the sentence.

| Slop word | What a human would write |
|---|---|
| delve | dig into, look at, examine |
| utilize | use |
| leverage (verb) | use, take advantage of |
| facilitate | help, enable, make possible |
| elucidate | explain, clarify |
| embark | start, begin |
| endeavor | effort, try |
| encompass | include, cover |
| multifaceted | complex, varied |
| tapestry | (just don't. describe the actual thing.) |
| testament (as in "a testament to") | shows, proves |
| paradigm | model, approach, framework |
| synergy / synergize | (delete the sentence and start over) |
| holistic | whole, complete, full-picture |
| catalyze / catalyst | trigger, cause, spark |
| juxtapose | compare, contrast, set against |
| nuanced (as filler) | (cut it. if the thing is nuanced, show how.) |
| realm | area, field, domain |
| landscape (metaphorical) | field, space, situation |
| myriad | many, lots of |
| plethora | many, a lot |

### Tier 2: Suspicious in clusters

Fine in isolation. Three in one paragraph = rewrite.

robust, comprehensive, seamless, cutting-edge, innovative, streamline,
empower, foster, enhance, elevate, optimize, scalable, pivotal, intricate,
profound, resonate, underscore, harness, navigate (metaphorical), cultivate,
bolster, galvanize, cornerstone, game-changer

### Tier 3: Filler phrases (zero information)

Delete all of these:

- "It's worth noting that..." → Just state the thing.
- "It's important to note that..." → Just state the thing.
- "Importantly, ..." / "Notably, ..." / "Interestingly, ..." → Just state the thing.
- "Let's dive into..." / "Let's explore..." → Start with the content.
- "Furthermore, ..." / "Moreover, ..." / "Additionally, ..." → and, also
- "In today's [fast-paced/digital/modern] world..." → Delete the clause.
- "Not just X, but Y" → Restructure. This is the #1 LLM rhetorical crutch.

---

## STRUCTURAL SLOP PATTERNS

### The "topic sentence" machine
LLMs default to: topic sentence → elaboration → example → wrap-up. Every paragraph.
Human writing varies rhythm.

### List abuse
Watch for: lists where every item starts identically, lists substituting for explanation,
lists of exactly 3 or 5 items.

### Symmetry addiction
Three pros, three cons. Five steps. Equal-length sections. Real writing is lumpy.

### The hedge parade
"may potentially help improve performance in some cases" → "This is faster."

### Transition word addiction
If every paragraph opens with However/Furthermore/Additionally/Moreover — rewrite.

---

## FICTION-SPECIFIC AI TELLS

Kill on sight in prose:
- "A sense of [emotion]"
- "Couldn't help but feel"
- "The weight of [abstract noun]"
- "The air was thick with [emotion/tension]"
- "Eyes widened" (as default surprise)
- "A wave of [emotion] washed over"
- "Heart pounded in [his/her] chest"
- "[Raven/dark/golden] hair [spilled/cascaded/tumbled]"
- "Piercing [blue/green] eyes"
- "A knowing smile"
- "Let out a breath [he/she] didn't know [he/she] was holding"
- "Something [dark/ancient/primal] stirred"

---

*Adapted from NousResearch/autonovel. See original for full reference.*
