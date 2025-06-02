# AI-Powered Joke Generation and Evaluation System

## Overview

This repository contains a sophisticated AI-powered system for **generating** and **evaluating** jokes using advanced Large Language Model (LLM) techniques. The system combines two powerful components:

1. **🎭 Joke Generator** - A multi-stage pipeline that systematically creates high-quality jokes from topics
2. **⚖️ Joke Judge** - A bias-mitigated evaluation system that rates and ranks jokes through comprehensive analysis

The system transforms simple topics into tournament-winning jokes through structured creativity, comprehensive evaluation, and competitive selection.

## Setup

1. Clone the latest release from https://github.com/oyeluckydps/PC_jokespace/releases/tag/v1.1.2 or whichever release has the latest tag, as new features are continuously added!

2. Create a new virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies from the root directory (PC_jokespace):
   ```bash
   pip install -r requirements.txt
   ```

4. Add your Anthropic API key to your environment. The system uses Haiku 3.0 model by default and may cost up to 20 cents for a complete run (approximately 5 jokes per dollar 😆). While OpenRouter free models are supported as fallback, they are not robust enough for optimal performance.

   **Primary option:**
   ```bash
   export ANTHROPIC_API_KEY=your_api_key_here
   ```

   **Alternative option:**
   Create `secret/LLAMA_API_KEY.txt` and put your OpenRouter API key for "meta-llama/llama-3.1-8b-instruct:free" there.

5. Test the installation:
   ```bash
   python -m cli --topic "ant" --jokespace "small"
   ```
   ( Must launch it from project root i.e. .../PC_jokespace/ )

   This will launch a comprehensive pipeline with a joke generator that creates about 10-15 jokes and a joke judge that selects the best joke. After 1-2 minutes, you'll have a novel, witty, punny joke!

## Quick Start

### Basic Usage

( Must launch these commands from project root i.e. .../PC_jokespace/ )

**Generate jokes with random topic:**
```bash
python -m cli
```

**Generate jokes for specific topic:**
```bash
python -m cli --topic "pizza"
```

**Generate multiple jokes:**
```bash
python -m cli --topic "cat" --count 5
```

### CLI Arguments

The generator CLI supports the following arguments:

- `--topic TOPIC`: Topic for joke generation (default: random selection)
- `--jokespace {small,medium,large}`: Generation scale (default: medium)
  - **small**: 10-15 jokes, ~60-120 seconds, ideal for testing
  - **medium**: 25-50 jokes, ~2-4 minutes, balanced for most use cases
  - **large**: 50+ jokes, ~5-10 minutes, comprehensive generation
- `--count COUNT`: Number of final jokes to select (default: 1)
- `--output-dir DIR`: Output directory for logs and results
- `--retries NUM`: Maximum retry attempts for API calls
- `--bypass-cache`: Force fresh generation without cache

### Sample Workflows

( Must launch these commands from project root i.e. .../PC_jokespace/ )

**Quick Testing:**
```bash
python -m cli --topic "coffee" --jokespace small
```

**A reletavily funny joke:**
```bash
python -m cli --topic "technology" --jokespace medium --count 3
```

**A really FUNNY joke (by searching over a large jokespace):**
```bash
python -m cli --topic "space exploration" --jokespace large --bypass-cache
```

**Custom Output:**
```bash
python -m cli --topic "music" --count 5 --output-dir ./music_jokes
```

## Judge System

For evaluating existing joke collections, use the judge module directly:

( Must launch these commands from project root i.e. .../PC_jokespace/ )

```bash
python -m judges.cli path/to/jokes.xml
```

The judge system provides sophisticated bias-mitigated evaluation through rating and tournament phases. For detailed judge CLI options and usage, see [`./judges/README.md`](./judges/README.md).

## System Architecture

### 🎯 Core Philosophy

Rather than attempting direct joke generation, this system implements a **structured search approach** inspired by PLANSEARCH methodology. It searches over intermediate representations (categories, factors, hook points) to maximize creative diversity and output quality.

### 🔄 Complete Workflow

```
Topic Input → Category-Factor Selection → Hook Point Generation → Cross-Category Synthesis → Joke Generation → Comprehensive Rating → Tournament Selection → Winner
```

## Subsystem Documentation

For comprehensive technical details, please refer to:

- **Generator System**: [`./generator/README.md`](./generator/README.md) - Complete generator architecture, pipeline details, and technical implementation
- **Judge System**: [`./judges/README.md`](./judges/README.md) - Rating and duel judge implementation, bias mitigation techniques, and evaluation methodology

## Output Structure

### Generator Output
```
logs/generator_YYYY_MM_DD_HH_MM_SS/
├── category_factor_selection.xml    # Selected humor categories and factors
├── hook_point_generation.xml        # Generated comedic anchor points
├── cross_category_synthesis.xml     # Hybrid approach combinations
└── joke_generation_results.xml      # Complete generation pipeline

output/generated_jokes.xml           # Final formatted jokes
```

### Judge Output (when integrated)
```
logs/jokes_file_YYYY_MM_DD_HH_MM_SS/
├── rating_results.xml              # Comprehensive rating analysis
├── top_jokes_for_duel.xml          # Tournament participants
├── tournament_results.xml          # Winner and final rankings
└── duel_matches.xml                # All tournament matches
```

## Performance Considerations

The jokespace size affects multiple aspects of generation:

- **LLM API Costs**: Large jokespace requires more API calls
- **Execution Time**: Scales roughly linearly with jokespace size
- **Memory Usage**: Higher-order synthesis increases with larger jokespaces
- **Tournament Competition**: More jokes create more competitive tournaments

Choose your jokespace based on your needs:
- Use **small** for quick testing and concept validation
- Use **medium** for most production use cases
- Use **large** for research and comprehensive analysis

## API Costs

The system uses Claude Haiku 3.0 model for API calls. A complete run typically costs around 20 cents, yielding approximately 5 jokes per dollar. Monitor your API usage when processing large datasets or running extensive evaluations, especially with large jokespace configurations.

## Use Cases

### Content Creation
- **Comedy Writers**: Generate diverse joke concepts and refine through competitive evaluation
- **Content Creators**: Develop humor for social media, presentations, or entertainment
- **Marketing Teams**: Create engaging, appropriate humor for campaigns

### Research and Analysis
- **Humor Research**: Study computational humor generation and evaluation techniques
- **AI Development**: Explore structured creativity and bias mitigation in LLM applications
- **Quality Assessment**: Benchmark joke quality across different generation approaches

### Educational Applications
- **Creative Writing**: Teach humor construction through systematic approaches
- **AI Ethics**: Demonstrate bias mitigation techniques in subjective evaluation
- **Computational Creativity**: Explore structured approaches to creative content generation

## Technical Highlights

### Generator Innovations
- **PLANSEARCH-Inspired Architecture**: Searches over intermediate representations for better creativity
- **Cross-Category Synthesis**: Combines different humor approaches for sophisticated jokes
- **Async Processing**: Efficient parallel generation with graceful error handling
- **Scalable Jokespace**: Dynamic sizing for different use cases and performance requirements

### Judge Sophistication
- **Bias Mitigation**: Position randomization, consistency checking, confidence scoring
- **Multi-Dimensional Rating**: Category-based evaluation with factor-specific scoring
- **Tournament Dynamics**: Lives system, bye handling, and comprehensive match tracking
- **Liberal Evaluation**: Inclusive admissibility assessment preventing false rejections