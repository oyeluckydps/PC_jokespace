# LLM-Based Joke Judge: Design Document

## 1. Project Overview and Literature Foundation

### 1.1 Project Objective

This project aims to develop a bias-minimized LLM-based judge specifically designed for evaluating jokes. The system addresses the critical need for reliable automated humor assessment while incorporating state-of-the-art bias mitigation techniques identified in recent research.

### 1.2 Literature Foundation

Based on comprehensive analysis of current LLM-as-a-Judge research, this project incorporates proven strategies from two key papers:

**From CALM Framework Research ("Justice or Prejudice? Quantifying Biases in LLM-as-a-Judge"):**
- **Position Bias Mitigation**: The framework identified that LLM judges exhibit significant position bias, with robustness rates dropping below 0.5 when evaluating multiple options. Our system addresses this through systematic answer order randomization.
- **Self-Enhancement Bias Avoidance**: Research showed models favor their own outputs with error rates up to 16.1%. We implement separate generation and evaluation models to eliminate this bias.

**From Crowd Score Research ("Crowd Score: A Method for the Evaluation of Jokes using Large Language Model AI Voters as Judges"):**
- **Few-Shot Prompting Superiority**: The study demonstrated that few-shot prompting achieved 100% balanced accuracy compared to 88% for zero-shot prompting in joke evaluation tasks.
- **Opposite Word Selection Impact**: Research showed that choosing appropriate opposite words (e.g., "boring" vs "not funny") can improve classification accuracy by up to 26%. Our system implements careful word selection for binary classifications.

**Additional Research-Backed Features:**
- **Caching Mechanisms**: Reduces computational overhead while maintaining consistency in repeated evaluations.

### 1.3 Unique Contribution

This project combines multiple bias reduction techniques into a domain-specific judge for humor evaluation - an area where subjective judgment and cultural context create additional challenges beyond general text evaluation. 

**Key Innovation - Two-Step Judging Mechanism:**
1. **Broad Classification Phase (Rating Judge)**: Provides comprehensive, criteria-based evaluation that establishes crude or broad positioning of jokes on the funniness scale. This phase handles initial categorization, admissibility checking, and multi-dimensional scoring across relevant factors.

2. **Fine-Tuning Phase (Duel Judge)**: Performs precise comparative analysis between joke pairs to determine relative superiority. This duel-based mechanism handles fine-grained distinctions that are difficult to capture through absolute scoring alone.

**Adaptive Pipeline Architecture**: The system incorporates a sophisticated branching pipeline that accommodates unique, unconventional humor that may not fit established categories or evaluation criteria. This design addresses a critical limitation in traditional humor evaluation systems that often fail to properly assess innovative or boundary-pushing comedic content. By providing pathways for:
- Independent category assignment for uncategorizable jokes
- Dynamic factor generation for novel humor types
- Flexible evaluation criteria adaptation

This ensures that highly creative, avant-garde, or culturally emergent humor forms receive fair evaluation rather than being penalized for not conforming to established patterns. The adaptive pipeline prevents the system from being constrained by preconceived notions about what constitutes evaluable humor, allowing it to evolve and adapt to new comedic forms and styles.

This dual-phase approach ensures both comprehensive individual assessment and precise relative ranking, addressing the inherent challenges in humor evaluation where context and comparison often matter more than absolute metrics.

## 2. System Architecture and Implementation Design

### 2.1 Rating Judge Design

The Rating Judge operates through a sophisticated multi-stage pipeline with dynamic branching to accommodate various humor types and evaluation scenarios. The pipeline includes multiple decision points and convergence mechanisms to ensure comprehensive evaluation regardless of the joke's conventional categorization.

**Advanced Chain-of-Thought Reasoning**: Beyond traditional linear chain-of-thought prompting, the Rating Judge implements a sophisticated reasoning mechanism featuring loops and tree-structured thought processes. This non-linear approach allows the judge to revisit and refine decisions, explore multiple reasoning paths simultaneously, and establish more robust logical foundations for humor evaluation through iterative refinement and branching analysis.

#### 2.1.1 Stage 1: Admissibility Assessment

**Liberal Evaluation Approach**: The admissibility assessment follows a liberal evaluation philosophy, designed to minimize false rejections of potentially valid humor. Jokes should only be rejected if they clearly and significantly fail the assessment criteria. The system errs on the side of inclusion rather than exclusion.

**Binary Classification Criteria:**

1. **Intent Verification**: "Is this text intended to be a joke?"
   - **Liberal Prompt Strategy**: "Analyze the following text and determine if it was created with humorous intent. Be generous in your interpretation - consider setup-punchline structure, wordplay, irony, absurdity, or other comedic devices. Some texts may appear serious but contain subtle humor - examine carefully for any indicators of comedic purpose. Only reject if there is absolutely NO indication of humorous intent."
   - **Liberal Threshold**: Only reject if the text shows zero comedic elements or clear serious intent (e.g., news articles, technical documentation, formal business communication)

2. **Completeness Assessment**: "Is this a complete joke entity?"
   - **Liberal Prompt Strategy**: "Evaluate whether this represents a complete humorous entity. Be particularly generous with minimalist humor, anti-jokes, or deliberately incomplete-seeming jokes where the 'incompleteness' IS the humor. Consider: Does this text contain sufficient elements for its intended comedic effect? Note that some jokes are intentionally brief or seemingly incomplete as part of their comedic structure. Only reject if the text is genuinely truncated mid-sentence or clearly missing essential components that would make it incomprehensible."
   - **Liberal Threshold**: Only reject if text appears genuinely incomplete (cut off mid-sentence, missing obvious setup or punchline that makes it incomprehensible)

3. **Appropriateness Screening**: "Is this joke harmful, sexually explicit, or overly racist?"
   - **Liberal Prompt Strategy**: "Assess this content for severely harmful elements including explicit sexual content, overtly racist themes, or clearly harmful stereotypes. Be tolerant of edgy humor that pushes boundaries appropriately - distinguish between humor that challenges conventions and content that is genuinely harmful or dangerous. Only reject content that is clearly offensive, explicitly harmful, or promotes dangerous behavior."
   - **Liberal Threshold**: Only reject if content is explicitly harmful, promotes violence, contains graphic sexual content, or uses overtly racist language

4. **Coherence Check**: "Does this text maintain internal logical consistency within its comedic framework?"
   - **Liberal Prompt Strategy**: "Determine if the text maintains basic coherence within its own comedic logic. Be generous with absurd or surreal humor - even nonsensical content can be coherent within its own framework. Only reject if the text is genuinely incomprehensible, contains contradictory statements that undermine its own premise, or appears to be random words without any discernible structure."
   - **Liberal Threshold**: Only reject if text is completely incoherent, appears to be random text generation, or contains severe logical contradictions that make it impossible to follow

5. **Language Accessibility**: "Is the humor accessible without requiring extensive external context?"
   - **Liberal Prompt Strategy**: "Evaluate whether the humor can be reasonably understood without requiring highly specialized expert knowledge or extremely obscure references. Be generous with cultural references, current events, and moderate specialized knowledge. Only reject if the humor requires such specific, technical, or obscure knowledge that it would be inaccessible to the vast majority of people."
   - **Liberal Threshold**: Only reject if joke requires extremely specialized technical knowledge, references completely obscure events/people, or uses languages/dialects that are incomprehensible to general audiences

**System Prompt Caching Implementation:**
The admissibility assessment instructions and criteria explanations will be cached as system prompts to avoid repetitive metadata transmission. The cache will store:
- Complete admissibility criteria explanations with liberal thresholds
- Assessment methodology instructions emphasizing inclusion over exclusion
- Scoring rubrics that favor admissibility
- Decision trees with bias toward acceptance

**Liberal Assessment Philosophy Implementation:**
```
admissibility_checker.py:
- class AdmissibilityChecker()
  - evaluate_admissibility(joke_text) -> AdmissibilityResult
  - apply_liberal_thresholds() -> bool
  - err_on_side_of_inclusion() -> bool
```

#### 2.1.2 Stage 2: Category Classification Pipeline

**XML Configuration Management:**

The system utilizes `criteria_categories_jokes.xml` containing:
- 7-8 main criteria groups (treated as organizational structure, not hierarchical constraints)
- 10 categories per criteria group
- Total of 50-70 distinct joke categories
- All categories treated as equivalent options for LLM selection

**System Prompt Caching for Categories:**
The complete category list from `criteria_categories_jokes.xml` will be pre-loaded and cached as system prompts including:
- Full category descriptions
- Classification methodology
- Multi-category assignment instructions
- Independent category pathway instructions

This eliminates the need to repeatedly transmit large category lists with every classification request.

**Classification Process Flow:**

**Branch 1: Standard Category Assignment**
1. Load all categories from XML as flat list (ignoring hierarchical organization)
2. Present all categories to LLM for evaluation
3. Allow multi-category assignment across any categories
4. LLM determines category membership independently

**Branch 2: Independent Category Pathway**
When LLM determines joke doesn't fit any existing categories:
1. Assign "Independent" category
2. Create concatenated list of all factors from all categories
3. LLM evaluates which factors are relevant for this unique joke
4. Selected factors used for evaluation (rejoins main pipeline at Stage 4)

**Implementation Structure:**
```
category_classifier.py:
- class CategoryClassifier()
  - classify_joke(joke_text) -> CategoryClassificationResult
  - handle_independent_category(joke_text) -> IndependentCategoryResult
```

#### 2.1.3 Stage 3: Factor Identification Pipeline

**Standard Pathway (For Categorized Jokes):**

The system uses `factors_to_judge_jokes.xml` containing:
- Factor definitions for each category
- Detailed explanations of each factor
- Positive examples (good implementation of factor)
- Negative examples (poor implementation of factor)

**System Prompt Caching for Factors:**
All factor definitions, explanations, and examples from `factors_to_judge_jokes.xml` will be pre-loaded and cached as system prompts including:
- Complete factor definitions database
- Factor explanation methodology
- Good and bad example libraries
- Factor relevance assessment instructions

This prevents repeated transmission of extensive factor documentation with each evaluation request.

**No Relevant Factors Pathway (Branch 3):**
When no existing factors apply to the joke:
1. Invoke dynamic factor generation prompt
2. LLM creates one or more new factors specific to this joke type
3. Generate explanations, good examples, and bad examples for new factors
4. Use newly created factors for evaluation

**Implementation Structure:**
```
factor_analyzer.py:
- class FactorAnalyzer()
  - determine_relevant_factors(joke_text, categories) -> FactorResult
  - create_dynamic_factors(joke_text) -> List[DynamicFactor]
```

#### 2.1.4 Stage 4: Factor-Based Scoring (Convergence Point)

**System Prompt Caching for Scoring:**
Scoring methodology, rubrics, and general instructions will be cached as system prompts:
- Scoring scale definitions (0-5)
- Evaluation methodology
- Score interpretation guidelines
- Aggregation strategy instructions

**Scoring Methodology:**
- Scale: 0-5 (integers only: 0, 1, 2, 3, 4, 5)
- 5 = Excellent adherence to factor
- 0 = No adherence or negative adherence to factor

**Aggregation Strategy:**
After scoring all relevant factors:
1. Calculate maximum score achieved across all factors
2. Calculate mean score across all factors
3. Store individual factor scores for detailed analysis
4. Record pathway taken (standard/independent/dynamic factors)

**Implementation Structure:**
```
factor_scorer.py:
- class FactorScorer()
  - score_factors(joke_text, factors) -> Dict[Factor, int]
  - calculate_aggregated_scores(factor_scores) -> AggregatedResult
```

#### 2.1.5 Complete Rating Judge Implementation

**Files to Create:**
- `rating_judge.py`: Main orchestrator class
- `admissibility_checker.py`: Binary classification stage with liberal thresholds
- `category_classifier.py`: Multi-category assignment with independent pathway
- `factor_analyzer.py`: Factor relevance determination and dynamic creation
- `factor_scorer.py`: Factor-based scoring engine
- `xml_parser.py`: XML configuration management

### 2.2 Duel Judge Design

#### 2.2.1 Core Functionality
Performs pairwise comparison of jokes with comprehensive bias mitigation:

**Bias Mitigation Features:**
- Position randomization (A vs B, then B vs A)
- Few-shot prompting with curated examples
- Separate generation/evaluation models
- Confidence factor scoring

#### 2.2.2 Few-Shot Example Database

**System Prompt Caching for Examples:**
The system utilizes `good_vs_bad_jokes.xml` to load curated examples that will be cached as system prompts:
- 5 high-quality funny joke examples
- 5 low-quality/boring joke examples
- Comparative evaluation methodology
- Duel assessment instructions

This eliminates the need to repeatedly transmit example libraries with each comparison request.

#### 2.2.3 Comparative Evaluation Process

**System Prompt Caching for Duel Methodology:**
Duel evaluation instructions, bias mitigation protocols, and confidence scoring methodologies will be cached as system prompts:
- Position randomization protocols
- Consistency checking procedures
- Confidence factor calculation methods
- Final decision aggregation rules

**Duel Evaluation Protocol:**
1. First comparison: Joke A vs Joke B
2. Second comparison: Joke B vs Joke A (position swapped)
3. Consistency check between results
4. Final decision with confidence factor

**Confidence Factor Scale:**
- 1.0 - 1.1: Nearly identical quality
- 1.1 - 2.0: Slight preference
- 2.0 - 5.0: Clear preference
- 5.0 - 10.0: Strong preference
- 10.0+: Overwhelming preference

#### 2.2.4 Implementation Structure for Duel Judge

**Files to Create:**
- `duel_judge.py`: Main comparative evaluation class
- `bias_mitigation.py`: Position randomization and consistency checking
- `confidence_scorer.py`: Calculates confidence factors

**Key Functions:**
```
duel_judge.py:
- class DuelJudge()
  - compare_jokes(joke_a, joke_b) -> ComparisonResult
```

### 2.3 Integration and Workflow

#### 2.3.1 Simplified Cache Management

```
cache_manager.py:
- class CacheManager()
  - load_xml_configurations() -> None
  - get_cached_system_prompt(prompt_type) -> str
  - cache_system_prompts() -> None

xml_parser.py:
- parse_categories_xml() -> List[Category]
- parse_factors_xml() -> List[Factor] 
- parse_examples_xml() -> ExampleDatabase
```

#### 2.3.2 Main Application Structure

```
main_judge.py:
- class JokeJudge()
  - __init__(config_path)
  - rate_joke(joke_text) -> RatingResult
  - compare_jokes(joke_a, joke_b) -> ComparisonResult

config.py:
- load_config(config_path) -> Config

models.py:
- class RatingResult()
- class ComparisonResult()
- class AdmissibilityResult()
```

## 3. Future Enhancements

### 3.1 Planned System Improvements

**Confidence Scoring Integration**: Future versions will incorporate confidence scores for category assignments and factor relevance determinations to enable weighted mean calculations and more nuanced evaluation. This enhancement will allow the system to express uncertainty in its judgments and potentially request additional evaluation rounds for borderline cases.

**Adaptive Factor Learning**: The system could learn from dynamically generated factors to expand the base factor database for future evaluations. This would create a continuously improving knowledge base that adapts to emerging humor trends and styles without manual intervention.

**Cultural Context Awareness**: Enhanced pipeline branches for culturally specific humor evaluation. This would involve developing specialized pathways that can understand and evaluate humor that is deeply embedded in specific cultural contexts, regional references, or linguistic nuances.

### 3.2 Personality-Based Evaluation

**Personality Induction for Specialized Contexts**: While the current implementation deliberately avoids personality-based prompting to maintain consistency and reduce bias, future versions may explore controlled personality induction for specific evaluation contexts. This could include:

- **Target Audience Analysis**: Evaluating jokes for specific demographic groups or contexts (e.g., workplace humor, family-friendly content, academic settings)
- **Cultural Adaptation**: Incorporating different cultural perspectives for humor that may be received differently across various cultural contexts
- **Controlled Personality Sets**: Using validated personality profiles that have been tested for bias and consistency to provide multiple perspectives on humor evaluation

This enhancement would be implemented with careful bias monitoring and validation mechanisms to ensure that personality induction improves rather than compromises evaluation quality.

### 3.3 Verbosity Bias Mitigation

**Statistical Analysis for Length Bias Correction**: The current implementation does not address verbosity bias - the tendency for LLMs to favor longer responses regardless of quality. Future work will explore statistical analysis tools to identify and correct for this bias:

- **Length Normalization Algorithms**: Developing statistical methods to normalize joke evaluations across different lengths while preserving legitimate quality differences
- **Content Density Analysis**: Implementing metrics that measure humor content density rather than total length to better assess joke efficiency and effectiveness
- **Bias Detection and Correction**: Creating automated systems that can detect when length is inappropriately influencing evaluation scores and apply corrective adjustments
- **Comparative Length Studies**: Conducting systematic studies to understand how joke length affects perceived humor and developing compensation mechanisms

This enhancement would involve sophisticated statistical modeling to ensure that genuinely longer jokes that require more setup are not penalized while preventing simple verbosity from artificially inflating scores.

### 3.4 Advanced Pipeline Extensions

**Multi-Modal Humor Evaluation**: Extending the system to handle visual jokes, memes, and multimedia humor content that combines text with images or other media formats.

**Temporal Humor Analysis**: Developing capabilities to understand and evaluate time-sensitive humor, including references to current events, trending topics, and evolving cultural phenomena.

**Interactive Evaluation Sessions**: Creating mechanisms for iterative joke refinement where the system can provide specific feedback for joke improvement rather than just evaluation scores.

This comprehensive design provides a detailed blueprint for implementing a sophisticated, adaptive joke evaluation system that can handle conventional humor through established pathways while providing robust mechanisms for evaluating unique, unconventional, or emergent humor forms through dynamic adaptation and factor generation.