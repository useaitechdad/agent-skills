# 🤖 Agent Skills — by Use AI with Tech Dad

A curated collection of **open-source agent skills** for AI coding assistants. Each skill is a self-contained package of instructions, scripts, and resources that teaches an AI agent how to perform a specialized task — reliably and repeatably.

> **📺 YouTube Channel:** [Use AI with Tech Dad](https://youtube.com/@UseAIwithTechDad)
> Follow along as we build, explain, and demo each skill live.

## What Are Agent Skills?

Skills are folders that contain a `SKILL.md` file (with YAML frontmatter) plus any supporting scripts, assets, and resources. When an AI agent loads a skill, it gains the ability to perform that task using the provided instructions — whether that's removing watermarks from images, generating documents, automating workflows, or anything else you can teach it.

```
my-skill/
├── SKILL.md          # Instructions + metadata (required)
├── scripts/          # Helper scripts (optional)
├── resources/        # Documentation, references (optional)
└── examples/         # Usage examples (optional)
```

Skills follow the open [Agent Skills specification](https://agentskills.io/specification).

## Available Skills

| Skill | Description | Status |
| :---- | :---------- | :----: |
| [gemini-watermark-remover](./gemini_watermark_remover_agent_skill/) | Remove Gemini visible watermarks from AI-generated images using Reverse Alpha Blending — lossless, pixel-perfect, Python-based | ✅ Ready |

> More skills coming soon — subscribe to the [YouTube channel](https://youtube.com/@UseAIwithTechDad) to get notified!

## Quick Start

### Using with Any AI Coding Agent

1. Clone or download this repository
2. Point your agent to the skill folder you want to use
3. The agent reads `SKILL.md` and follows the instructions automatically

```bash
git clone https://github.com/useaitechdad/agent-skills.git
cd agent-skills
```

### Example: Gemini Watermark Remover

Tell your agent:
> "Remove the watermark from this Gemini image: `/path/to/my_image.png`"

The agent will read `SKILL.md`, install dependencies if needed, run the Python script, and report the result.

Or run it manually:
```bash
cd gemini_watermark_remover_agent_skill
pip install -r scripts/requirements.txt
python scripts/remove_watermark.py /path/to/image.png --output /path/to/clean.png
```

## Creating Your Own Skills

Use the basic template below as a starting point:

```markdown
---
name: my-skill-name
description: A clear description of what this skill does and when to use it
---

# My Skill Name

[Add your instructions here that the agent will follow when this skill is active]

## Workflow
1. Step one
2. Step two

## Examples
- Example usage 1
- Example usage 2

## Constraints
- Constraint 1
- Constraint 2
```

The frontmatter requires only two fields:
- **`name`** — A unique identifier (lowercase, hyphens for spaces)
- **`description`** — What the skill does and when to use it

## Repository Structure

```text
agent-skills/
├── LICENSE                                    # Apache 2.0
├── README.md                                  # This file
├── .gitignore
└── gemini_watermark_remover_agent_skill/      # First skill
    ├── SKILL.md                               # Agent instructions
    ├── scripts/
    │   ├── remove_watermark.py                # Core processing script
    │   ├── requirements.txt                   # Python dependencies
    │   └── alpha_maps/                        # Pre-calculated watermark maps
    │       ├── alpha_48.npy
    │       └── alpha_96.npy
    ├── resources/
    │   └── algorithm.md                       # How the algorithm works
    └── examples/
        └── usage.md                           # CLI usage examples
```

## Disclaimer

**These skills are provided for educational and personal use.** Always test skills thoroughly in your own environment before relying on them for critical tasks. The implementations and behaviors you receive from your AI agent may vary.

## License

This project is licensed under the [Apache License 2.0](./LICENSE).

Individual skills may include third-party components with their own licenses — check each skill's folder for details.

---

<p align="center">
  Made with 🤖 by <a href="https://youtube.com/@UseAIwithTechDad">Use AI with Tech Dad</a>
</p>
