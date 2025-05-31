# AI-Powered Joke Generation and Evaluation System

## Overview

This repository contains a sophisticated AI-powered system for **generating** and **evaluating** jokes using advanced Large Language Model (LLM) techniques. The system combines two powerful components:

1. **🎭 Joke Generator** - A multi-stage pipeline that systematically creates high-quality jokes from topics
2. **⚖️ Joke Judge** - A bias-mitigated evaluation system that rates and ranks jokes through comprehensive analysis

The system transforms simple topics into tournament-winning jokes through structured creativity, comprehensive evaluation, and competitive selection.

## System Architecture

### 🎯 Core Philosophy

Rather than attempting direct joke generation, this system implements a **structured search approach** inspired by PLANSEARCH methodology. It searches over intermediate representations (hook-template pairs, categories, factors) to maximize creative diversity and output quality.

### 🔄 Complete Workflow

```
Topic Input → Hook-Template Generation → Higher-Order Grouping → Joke Generation → Comprehensive Rating → Tournament Selection → Winner Identification
```

## 🎭 Joke Generator Module

### Purpose
The generator transforms topics into diverse, high-quality jokes through a systematic 5-stage pipeline that prioritizes creativity while maintaining structure.

### Key Features
- **Hook-Template System**: Creates comedic anchors paired with compatible joke structures
- **Cross-Category Synthesis**: Combines different humor approaches for sophisticated jokes
- **Async Parallel Processing**: Generates jokes efficiently using configurable batch processing
- **Comprehensive Context Creation**: Builds rich explanatory frameworks for joke generation

### Generation Pipeline Stages
1. **Topic Processing**: Handles user input or random topic selection
2. **Hook-Template Generation**: Creates 15-20 diverse comedic foundations
3. **Higher-Order Grouping**: Forms synergistic combinations of hook-template pairs
4. **Joke Generation**: Produces ~40-100 jokes using parallel processing
5. **Output Formatting**: Creates XML compatible with the judge system

## ⚖️ Joke Judge Module

### Purpose
The judge provides bias-mitigated, comprehensive evaluation of jokes through a sophisticated two-phase system designed for objectivity and precision.

### Key Features
- **Dual-Judge Architecture**: Combines broad classification with fine-tuned comparison
- **Bias Mitigation**: Position randomization, confidence scoring, and consistency checking
- **Tournament System**: Lives-based elimination with bye handling for fair competition
- **Comprehensive Logging**: Detailed XML outputs for analysis and transparency

### Evaluation Pipeline
1. **Rating Judge**: Multi-dimensional scoring based on categories and factors
2. **Duel Judge**: Pairwise comparisons with bias mitigation techniques
3. **Tournament Manager**: Competitive elimination with lives system
4. **Result Analysis**: Winner identification with comprehensive ranking

## 🚀 Getting Started

### Prerequisites
```bash
pip install -r requirements.txt
```

**Required Environment Variables:**
```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

### Quick Start Commands

#### Generate Jokes Only
```bash
# Generate jokes about a random topic
python cli.py

# Generate jokes about specific topics
python cli.py --topic "artificial intelligence, robots, future"

# Quick generation (skip higher-order grouping)
python cli.py --topic "coffee" --first-order-only --generation-only
```

#### Full Pipeline (Generation + Evaluation)
```bash
# Complete pipeline with default settings
python cli.py --topic "technology"

# Custom configuration for optimal results
python cli.py --topic "cooking, restaurants" --batch-size 6 --retries 4
```

#### Evaluate Existing Jokes
```bash
# Evaluate jokes from XML file
python -m judges temp/sample_jokes.xml

# Custom evaluation parameters
python -m judges jokes.xml --batch-size 30 --top-count 16

# Rating-only mode (skip tournament)
python -m judges jokes.xml --rating-only --top-count 10
```

## 📖 Detailed Documentation

For comprehensive technical details, please refer to:

- **Generator System**: [`post_development_summary.md`](post_development_summary.md) - Complete generator architecture, file descriptions, and pipeline details
- **Judge System**: [`judges_post_development_summary.md`](judges_post_development_summary.md) - Rating and duel judge implementation, bias mitigation techniques

## 🎯 Use Cases

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

## 🔧 Advanced Usage

### Performance Optimization
```bash
# High-performance generation
python cli.py --topic "space exploration" --batch-size 10 --bypass-cache

# Conservative processing for stable networks
python cli.py --topic "music" --batch-size 2 --retries 5

# Minimal pipeline for testing
python cli.py --topic "test" --first-order-only --generation-only --batch-size 1
```

### Comprehensive Evaluation
```bash
# Large-scale evaluation with detailed logging
python -m judges dataset.xml --batch-size 50 --top-count 32

# Fresh evaluation bypassing cache
python -m judges jokes.xml --bypass-cache --retries 10

# Quick rating assessment
python -m judges small_set.xml --rating-only --batch-size 10
```

## 📊 Output Structure

### Generator Output
```
logs/generator_YYYY_MM_DD_HH_MM_SS/
├── first_order_contexts.xml      # Hook-template pairs with explanations
├── higher_order_groups.xml       # Synergistic combinations
└── pipeline_log.xml             # Generation summary

output/generated_jokes.xml        # Final formatted jokes
```

### Judge Output
```
logs/jokes_file_YYYY_MM_DD_HH_MM_SS/
├── rating_results.xml           # Comprehensive rating analysis
├── top_jokes_for_duel.xml       # Tournament participants
├── tournament_results.xml       # Winner and final rankings
└── duel_matches.xml            # All tournament matches
```

## 🎪 Sample Workflow

### Complete End-to-End Process
```bash
# 1. Generate jokes about technology
python cli.py --topic "smartphones, apps, digital life" --batch-size 8

# 2. The system automatically runs the judge evaluation
# 3. Review results in the timestamped output directories
# 4. Winner joke is displayed with confidence metrics
```

### Research and Development Workflow
```bash
# 1. Generate jokes with detailed logging
python cli.py --topic "research_topic" --bypass-cache --batch-size 5

# 2. Analyze intermediate results in logs/generator_*/
# 3. Run separate evaluation with custom parameters
python -m judges output/generated_jokes.xml --batch-size 20 --top-count 15

# 4. Compare results across different approaches
```

## 🧠 Technical Highlights

### Generator Innovations
- **PLANSEARCH-Inspired Architecture**: Searches over intermediate representations for better creativity
- **Context Flattening**: Unified processing of first-order and higher-order contexts
- **Async Processing**: Efficient parallel generation with graceful error handling
- **Creative Freedom**: LLM treats provided elements as inspiration, not rigid requirements

### Judge Sophistication
- **Bias Mitigation**: Position randomization, consistency checking, confidence scoring
- **Multi-Dimensional Rating**: Category-based evaluation with factor-specific scoring
- **Tournament Dynamics**: Lives system, bye handling, and comprehensive match tracking
- **Liberal Evaluation**: Inclusive admissibility assessment preventing false rejections

## 🔮 Future Enhancements

### Planned Improvements
- **Evolutionary Algorithm**: Learn from successful patterns to optimize future generation
- **Cultural Context Awareness**: Enhanced evaluation for culturally-specific humor
- **Multi-Modal Support**: Integration of visual and audio humor elements
- **Real-Time Adaptation**: Dynamic factor generation for emerging humor trends

### Research Directions
- **Verbosity Bias Correction**: Statistical analysis for length-based evaluation bias
- **Personality-Based Evaluation**: Controlled personality induction for specific contexts
- **Interactive Refinement**: Iterative joke improvement through system feedback

## 🤝 Contributing

This system represents a significant advancement in computational humor generation and evaluation. For technical implementation details, architectural decisions, and comprehensive function descriptions, please refer to the detailed post-development summaries linked above.

## 📜 License

This project demonstrates sophisticated AI techniques for creative content generation and bias-mitigated evaluation, suitable for research, education, and practical applications in content creation.

---

**Note**: This system requires an Anthropic API key and generates costs through Claude API usage. Monitor your API usage when processing large datasets or running extensive evaluations.