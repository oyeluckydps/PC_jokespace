# Complete Code Generation Plan for LLM-Based Joke Judge System (Batch Processing with XML Logging) - REVISED

## Project Structure Overview

The system will be organized into two main folders:
- `PC_jokespace/utilities/` - Reusable components for DSPy, caching, and XML parsing
- `PC_jokespace/judges/` - Core joke evaluation system with Rating Judge and Duel Judge

## Dependencies (PC_jokespace/requirements.txt)
```
dspy-ai>=2.4.0
pydantic>=2.0.0
anthropic>=0.25.0
asyncio>=3.4.3
```

## Implementation Specifications from Discussion

### Key Requirements:
1. **API Configuration**: ANTHROPIC_API_KEY already set in environment, use `claude-3-5-sonnet-20241022` with temperature 0.1
2. **DSPy Approach**: Use `dspy.Predict(ZeroShotChatSignature)` with clear instructions and examples in prompts. DSPy handles caching automatically - no custom caching implementation needed
3. **Error Handling**: Retry failed API calls after 5 seconds with maximum 10 retries, print failure reasons in RED
4. **Output Structure**: `logs/{input_filename}_{YYYY_MM_DD_HH_MM_SS}/` containing all XML outputs. Skip output creation if no valid jokes found
5. **Factor Handling**: Allow duplicate factors across categories, evaluate each occurrence separately. Drop categories if no factors are found relevant
6. **Tournament Lives System**: Rank 1 gets 3 lives, Rank 2 gets 2 lives, Rank 3 gets 1 life
7. **Tournament Bye System**: Top-rated player (by original rating score) gets bye if odd number of participants. No player can get two consecutive byes - if top player had bye last round, second-best gets bye
8. **Tie Resolution**: When A>B and B>A with same confidence, advance both jokes
9. **Progress Display**: Show real-time status updates in terminal during batch processing
10. **CLI Arguments**: Accept jokes file, batch size (default 20), and top jokes count (default 20)
11. **File Locations**: 
    - `PC_jokespace/criteria_category_of_jokes.xml`
    - `PC_jokespace/factors_to_judge_joke.xml`
    - `PC_jokespace/judges/good_vs_bad_joke.xml`

## File Structure and Detailed Implementation Plan

### PC_jokespace/utilities/ (Reusable Components)

#### 1. `PC_jokespace/utilities/dspy_client.py`
**Purpose**: Centralized DSPy client for Claude API connections with retry logic

**Implementation Details**:
- Initialize DSPy with Claude 3.5 Sonnet (`claude-3-5-sonnet-20241022`) using environment API key
- Configure DSPy settings for one-shot prediction with temperature 0.1
- Implement retry mechanism with 5-second delay on failures, maximum 10 retries
- Print API failures in RED color to terminal
- DSPy automatically handles caching based on signatures and inputs

**Classes and Functions**:
```python
class ClaudeClient(dspy.LM):
    def __init__(self, model="claude-3-5-sonnet-20241022", api_key=None, cache=True):
        # Get API key from ANTHROPIC_API_KEY environment variable
        # Configure DSPy with Claude 3.5 Sonnet model
        # DSPy handles caching automatically when cache=True
    
    def generate(self, prompt, max_tokens=2000, temperature=0.1):
        # Implement retry logic with 5-second delay, max 10 retries
        # Print failures in RED: print("\033[91mAPI Call Failed: {reason}\033[0m")
        # Return generated response using DSPy's built-in methods
        # Raise exception after 10 failed attempts
    
    def _get_api_key(self):
        # Retrieve from os.environ['ANTHROPIC_API_KEY']
        # Raise clear error if not found
```

#### 2. `PC_jokespace/utilities/xml_parser.py`
**Purpose**: Parse XML configuration files and validate joke input structure

**Implementation Details**:
- Use xml.etree.ElementTree for all XML parsing
- Load from correct paths:
  - `PC_jokespace/criteria_category_of_jokes.xml`
  - `PC_jokespace/factors_to_judge_joke.xml`
  - `PC_jokespace/judges/good_vs_bad_joke.xml`
- Implement validation for joke XML structure (must have id and text)
- Skip invalid jokes with console warning
- Load all configuration XMLs into structured Pydantic models

**Classes and Functions**:
```python
class XMLConfigParser:
    def __init__(self, base_path="PC_jokespace"):
        # Set base path for finding XML configuration files
        # Account for good_vs_bad_joke.xml being in judges/ subdirectory
    
    def parse_categories(self):
        # Parse criteria_category_of_jokes.xml from PC_jokespace/
        # Return flat list of all categories (ignore hierarchical grouping)
        # Each category should have name only (no description at category level)
    
    def parse_factors(self):
        # Parse factors_to_judge_joke.xml from PC_jokespace/
        # Organize factors by category
        # Include description, positive and negative examples for each factor
        # Factors contain all context needed for evaluation
    
    def parse_examples(self):
        # Parse good_vs_bad_joke.xml from PC_jokespace/judges/
        # Extract 5 good jokes and 5 bad jokes for few-shot prompting
    
    def parse_jokes(self, jokes_file_path):
        # Parse input jokes XML file
        # Validate each joke has id and text
        # Skip invalid jokes with warning: print(f"Warning: Skipping invalid joke at position {i}")
        # Return list of valid JokeData objects
        # If no valid jokes found, return empty list
    
    def _load_xml_file(self, filename):
        # Generic XML file loader with error handling
        # Exit with error message if config files missing/malformed

class Category(BaseModel):
    name: str
    # No description field - categories are just names
    factors: List[Factor]  # All factors for this category

class Factor(BaseModel):
    name: str
    category: str
    description: str  # Full context for evaluation
    positive_examples: List[str]
    negative_examples: List[str]

class ExampleData(BaseModel):
    good_jokes: List[str]
    bad_jokes: List[str]

class JokeData(BaseModel):
    id: int
    text: str
```

#### 3. `PC_jokespace/utilities/xml_logger.py`
**Purpose**: Generate all XML output files with proper formatting and structure

**Implementation Details**:
- Create output directory structure: `logs/{filename}_{timestamp}/`
- Use 4-space indentation for XML hierarchy
- Include all required metadata (timestamps, counts, ranks, lives tracking, bye tracking)
- Generate 4 main output files with comprehensive data
- Track which players received byes in each round

**Classes and Functions**:
```python
class XMLLogger:
    def __init__(self, output_dir):
        # Initialize with dynamic output directory
        # Create directory if it doesn't exist
    
    def log_rating_results(self, results: List[RatingResult], filename="rating_results.xml"):
        # Log all jokes with detailed admissibility breakdown
        # Include categories (drop those with no relevant factors)
        # Include factors and individual scores (including duplicates)
        # Show max_score, mean_score, and overall_rating
    
    def log_top_jokes(self, top_jokes: List[RatingResult], filename="top_jokes_for_duel.xml"):
        # Log top N jokes selected for tournament (N from CLI argument)
        # Include original rating and rank for each joke
        # Sort by overall_rating descending
    
    def log_tournament_results(self, tournament_result: TournamentResult, filename="tournament_results.xml"):
        # Log final tournament winner with complete details
        # Include final rankings comparing tournament position vs original rating rank
        # Show which jokes used lives during tournament
        # Track bye history for each participant
    
    def log_duel_matches(self, all_matches: List[DuelResult], filename="duel_matches.xml"):
        # Log all tournament matches organized by rounds
        # Start with lowest round (Round of N) and progress to Final
        # Include confidence factors, position consistency, and reasoning
        # Track lives used per match
        # Indicate bye recipients for each round
    
    def _create_output_dir(self):
        # Ensure output directory exists
    
    def _format_timestamp(self):
        # Generate YYYY-MM-DD HH:MM:SS format
    
    def _create_xml_element(self, tag, text=None, attributes=None):
        # Helper for creating XML elements with proper indentation
```

**XML Output Structure Updates**:

Add lives tracking and bye tracking to tournament XML outputs:
```xml
<tournament_results>
  <joke id="45" tournament_rank="1" original_rank="2">
    <lives_remaining>2</lives_remaining>
    <lives_used>1</lives_used>
    <bye_rounds>3,5</bye_rounds> <!-- Rounds where this joke received bye -->
  </joke>
</tournament_results>

<duel_matches>
  <round number="1" name="Round of 32">
    <bye_recipient joke_id="12" reason="top_rated_no_consecutive_bye"/>
    <match>
      <joke_a id="1" seed="1" lives_before="3"/>
      <joke_b id="20" seed="20" lives_before="0"/>
      <winner id="20"/>
      <joke_a_lives_after>2</joke_a_lives_after>
      <advanced_by_life>true</advanced_by_life>
    </match>
  </round>
</duel_matches>
```

### PC_jokespace/judges/ (Core Evaluation System)

#### 4. `PC_jokespace/judges/__init__.py`
**Purpose**: Module initialization
**Content**: Empty file or basic imports only

#### 5. `PC_jokespace/judges/cli.py`
**Purpose**: Command line interface and main entry point with three arguments

**Implementation Details**:
- Parse command line arguments: jokes file (required), batch size (optional), top count (optional)
- Extract filename for output directory naming
- Orchestrate complete pipeline with progress updates
- Return winner joke id and text, plus log location
- Handle case of no valid jokes gracefully

**Functions**:
```python
def main():
    # Entry point for: python -m judges <jokes_file.xml> [--batch-size N] [--top-count N]
    # Parse arguments
    # Create output directory with timestamp (only if valid jokes exist)
    # Run evaluation pipeline
    # Print final winner and log location
    
def parse_arguments():
    # Required positional argument:
    #   jokes_file: Path to XML file containing jokes
    # Optional arguments:
    #   --batch-size: Number of jokes to process in parallel (default: 20)
    #   --top-count: Number of top jokes to advance to tournament (default: 20)
    # Return: args object with jokes_file, batch_size, and top_count
    
def run_batch_evaluation(jokes_file_path, batch_size=20, top_count=20):
    # Extract filename from path for output directory
    # Load and validate jokes first
    # If no valid jokes:
    #   Print in RED: "Error: No valid jokes found in input file"
    #   Return (None, None)
    # Create logs/{filename}_{timestamp}/ directory
    # Initialize JokeJudgeSystem with output directory
    # Run complete evaluation with specified parameters
    # Return winner (id, text) and log directory path
    
def display_progress(current_joke, total_jokes, status):
    # Print progress updates to terminal
    # Format: [Joke {id}] {status}... ✓/✗
    
def display_final_results(winner_id, winner_text, log_dir):
    # Display the tournament winner and log location
    # Format: 
    # ========== TOURNAMENT WINNER ==========
    # Joke ID: {winner_id}
    # Joke Text: {winner_text}
    # 
    # Full results saved to: {log_dir}
    # =====================================
```

**Command Line Usage Examples**:
```bash
# Basic usage with defaults
python -m judges jokes.xml

# Custom batch size
python -m judges jokes.xml --batch-size 30

# Custom top count for tournament
python -m judges jokes.xml --top-count 16

# Both custom parameters
python -m judges jokes.xml --batch-size 50 --top-count 32
```

#### 6. `PC_jokespace/judges/models.py`
**Purpose**: Pydantic models for structured data with lives and bye tracking

**Implementation Details**:
- Add lives tracking to tournament-related models
- Add bye tracking to monitor consecutive byes
- Ensure all models properly validate DSPy outputs
- Include fields for tracking duplicate factors
- Track which categories were dropped due to no relevant factors

**Updated Classes**:
```python
class RatingResult(BaseModel):
    joke_id: int
    joke_text: str
    admissibility_results: AdmissibilityResults
    assigned_categories: List[str]  # All initially assigned categories
    dropped_categories: List[str]  # Categories dropped due to no relevant factors
    relevant_factors: List[str]  # May contain duplicates
    factor_scores: Dict[str, int]  # Factor name -> score (0-5)
    max_score: int
    mean_score: float
    overall_rating: float  # (max_score + mean_score) / 2
    original_rank: Optional[int] = None  # Set after ranking

class DuelResult(BaseModel):
    match_id: str
    round_number: int
    round_name: str
    joke_a_id: int
    joke_a_seed: int
    joke_a_lives_before: int  # Lives before this match
    joke_b_id: int
    joke_b_seed: int
    joke_b_lives_before: int  # Lives before this match
    winner_id: int
    loser_advanced_by_life: bool  # True if loser used a life to advance
    confidence_factor: float
    position_consistent: bool
    reasoning: str

class TournamentResult(BaseModel):
    winner_joke: RatingResult
    final_rankings: List[Tuple[RatingResult, int, int]]  # (joke, tournament_rank, lives_remaining)
    lives_tracking: Dict[int, List[int]]  # joke_id -> [initial_lives, lives_used, lives_remaining]
    bye_tracking: Dict[int, List[int]]  # joke_id -> [round_numbers_with_bye]
    original_top_jokes: List[RatingResult]  # Top N jokes from rating phase
    all_duel_matches: List[DuelResult]
    total_jokes_processed: int
    tournament_rounds: int
    top_count_used: int  # Number of jokes that entered tournament
```

#### 7. `PC_jokespace/judges/batch_processor.py`
**Purpose**: Handle parallel batch processing with progress updates

**Implementation Details**:
- Process jokes in parallel batches of specified size
- Update terminal with progress for each joke
- Track admissible vs inadmissible jokes
- Assign original ranks after rating
- Handle empty results gracefully

**Classes and Functions**:
```python
class BatchProcessor:
    def __init__(self, rating_judge, batch_size=20):
        # Store rating judge reference
        # Store batch size for parallel processing
    
    async def process_all_jokes(self, jokes: List[JokeData]):
        # If empty list, return empty results
        # Calculate total batches needed
        # Split jokes into batches of batch_size
        # Process each batch in parallel
        # Print batch progress
        # Return all results with ranks assigned
    
    async def _process_batch(self, joke_batch: List[JokeData], batch_num: int, total_batches: int):
        # Print: Processing batch {batch_num}/{total_batches} (jokes {start}-{end})...
        # Use asyncio.gather to run all evaluations in parallel
        # Update progress for each joke completion
        # Return batch results
    
    def _print_joke_progress(self, joke_id: int, stage: str, result: Any):
        # Format and print progress update
        # Include admissibility, categories, factors, ratings
        # Use color coding: GREEN for pass, RED for fail
        # Show dropped categories if any
    
    def get_top_jokes(self, results: List[RatingResult], count: int):
        # Filter admissible jokes only
        # Sort by overall_rating descending
        # Assign original_rank to each joke (1-based)
        # Return top 'count' jokes
        # If fewer than 'count' admissible jokes, return all admissible
```

#### 8. `PC_jokespace/judges/tournament_manager.py`
**Purpose**: Manage knockout tournament with lives system and revised bye handling

**Implementation Details**:
- Implement lives system: Rank 1 (3 lives), Rank 2 (2 lives), Rank 3 (1 life)
- Handle byes: Top-rated player (by original rating) gets bye unless they had bye in previous round
- Track bye history to prevent consecutive byes
- Track lives usage throughout tournament
- Advance both jokes when tie with same confidence
- Support variable number of tournament participants

**Classes and Functions**:
```python
class TournamentManager:
    def __init__(self, duel_judge):
        # Initialize with duel judge
        # Create lives tracking dictionary
        # Create bye tracking dictionary
    
    def run_tournament(self, top_jokes: List[RatingResult]):
        # Initialize lives based on original ranking
        # Initialize bye tracking
        # Run tournament rounds until winner
        # Track all matches and lives usage
        # Handle variable number of participants (not just 20)
        # Return comprehensive tournament result
    
    def _initialize_lives(self, jokes: List[RatingResult]):
        # For any number of participants:
        # Rank 1: 3 lives, Rank 2: 2 lives, Rank 3: 1 life
        # Others: 0 lives (single elimination)
        # Return dict: {joke_id: lives_count}
    
    def _run_tournament_round(self, participants: List[RatingResult], round_number: int, 
                            bye_history: Dict[int, List[int]]):
        # If odd number of participants, handle bye:
        #   - Find top-rated player (by original_rank) who didn't have bye last round
        #   - If top player had bye last round, give to second-best, etc.
        # Create matches based on seeding
        # Run all duels in parallel
        # Process results with lives system
        # Handle ties (both advance)
        # Update bye history
        # Return survivors for next round
    
    def _select_bye_recipient(self, participants: List[RatingResult], 
                            bye_history: Dict[int, List[int]], current_round: int):
        # Sort participants by original_rank
        # Find first player who didn't receive bye in (current_round - 1)
        # Update bye_history
        # Return selected player and remaining participants
    
    def _process_match_result(self, match: DuelResult, lives_tracker: Dict[int, int]):
        # Determine who advances
        # Update lives for loser if applicable
        # Handle tie case (both advance)
        # Track if loser advanced by life
        # Return list of advancing joke IDs
    
    def _create_round_name(self, participants_count: int):
        # Handle any number of participants:
        # 2: "Final"
        # 4: "Semi-Final" 
        # 8: "Quarter-Final"
        # Other: "Round of {count}"
```

#### 9. `PC_jokespace/judges/dspy_signatures.py`
**Purpose**: Define DSPy signatures for structured outputs

**Implementation Details**:
- Create ZeroShotChatSignature variants for each evaluation step
- Include clear instructions and output format requirements
- Add example formatting where applicable
- DSPy will handle caching automatically based on these signatures

**Signatures to Define**:
```python
# Each signature should specify exact output format expected

class AdmissibilitySignature(dspy.Signature):
    """Check if text is admissible as a joke"""
    joke_text = dspy.InputField()
    check_type = dspy.InputField()  # intent/completeness/appropriateness/coherence/accessibility
    instructions = dspy.InputField()  # Liberal evaluation instructions
    passed = dspy.OutputField(desc="true or false")
    reasoning = dspy.OutputField(desc="Brief explanation")

class CategoryAssignmentSignature(dspy.Signature):
    """Assign joke to relevant categories"""
    joke_text = dspy.InputField()
    all_categories = dspy.InputField()  # Full list with names only
    categories = dspy.OutputField(desc="List of category names")
    is_independent = dspy.OutputField(desc="true if no categories fit")
    reasoning = dspy.OutputField()

class FactorSelectionSignature(dspy.Signature):
    """Select relevant factors for a category"""
    joke_text = dspy.InputField()
    category = dspy.InputField()
    available_factors = dspy.InputField()  # Factors for this category with full context
    relevant_factors = dspy.OutputField(desc="List of factor names")
    reasoning = dspy.OutputField()

class FactorScoringSignature(dspy.Signature):
    """Score joke on specific factor"""
    joke_text = dspy.InputField()
    factor_name = dspy.InputField()
    factor_description = dspy.InputField()
    positive_examples = dspy.InputField()
    negative_examples = dspy.InputField()
    score = dspy.OutputField(desc="Integer 0-5")
    reasoning = dspy.OutputField()

class DuelComparisonSignature(dspy.Signature):
    """Compare two jokes with examples"""
    joke_a = dspy.InputField()
    joke_b = dspy.InputField()
    good_examples = dspy.InputField()  # 5 good jokes
    bad_examples = dspy.InputField()   # 5 bad jokes
    winner = dspy.OutputField(desc="joke_a or joke_b")
    confidence_factor = dspy.OutputField(desc="Float >= 1.0")
    reasoning = dspy.OutputField()
```

#### 10. `PC_jokespace/judges/rating_judge.py`
**Purpose**: Orchestrate complete joke rating with parallel processing

**Implementation Details**:
- Run all 5 admissibility checks in parallel
- Process categories, then factors per category
- Drop categories with no relevant factors
- Score all factors in parallel (including duplicates separately)
- Calculate max and mean scores
- Include clear instructions in each DSPy call
- For "Independent" category, use factors from all categories with their original context

**Classes and Functions**:
```python
class RatingJudge:
    def __init__(self, client, categories, factors, examples):
        # Store parsed XML data
        # Initialize DSPy predictors for each step
        # Categories are just names, factors have full context
    
    def evaluate_joke(self, joke: JokeData):
        # Synchronous wrapper for async evaluation
    
    async def evaluate_joke_async(self, joke: JokeData):
        # Full evaluation pipeline:
        # 1. Check admissibility (5 parallel checks)
        # 2. If admissible, assign categories
        # 3. Select factors per category (drop categories with no factors)
        # 4. Score all factors in parallel (duplicates scored separately)
        # 5. Calculate final ratings
    
    async def _check_all_admissibility_async(self, joke_text):
        # Run 5 checks in parallel using asyncio.gather
        # Each check uses liberal evaluation instructions
        # Compile results into AdmissibilityResults
    
    async def _check_intent_async(self, joke_text):
        # Use DSPy with liberal intent instructions
        # "Only reject if absolutely NO comedic intent"
    
    # Similar for other 4 admissibility checks...
    
    async def _classify_categories_async(self, joke_text):
        # Present all categories to LLM
        # Allow multi-category assignment
        # Check for independent category need
    
    async def _select_factors_per_category_async(self, joke_text, categories):
        # For each category, select relevant factors
        # Run category factor selections in parallel
        # Drop categories with no relevant factors
        # Track dropped categories
        # For "Independent" category, consider all factors from all categories
        # Combine all factors (duplicates allowed)
    
    async def _score_factors_async(self, joke_text, factors):
        # Score each factor in parallel
        # Include factor description and examples in prompt
        # Duplicates scored separately (each occurrence)
        # Return dictionary of factor_name -> score
    
    def _calculate_final_rating(self, factor_scores):
        # max_score = max(scores) or 0
        # mean_score = sum(scores) / len(scores) or 0
        # overall_rating = (max_score + mean_score) / 2
```

#### 11. `PC_jokespace/judges/duel_judge.py`
**Purpose**: Compare jokes with position bias mitigation

**Implementation Details**:
- Include good/bad examples in every comparison prompt
- Run both A vs B and B vs A comparisons
- Handle inconsistent results and ties
- Track match details for tournament
- Check for exact confidence match for tie determination

**Classes and Functions**:
```python
class DuelJudge:
    def __init__(self, client, examples):
        # Store good/bad joke examples
        # Initialize DSPy predictor
    
    def compare_jokes_for_tournament(self, joke_a: RatingResult, joke_b: RatingResult, 
                                   match_id: str, round_number: int, round_name: str,
                                   lives_tracker: Dict[int, int]):
        # Full tournament comparison with lives tracking
        # Return detailed DuelResult
    
    async def compare_jokes_async(self, joke_a: RatingResult, joke_b: RatingResult):
        # Run both comparisons in parallel
        # Resolve conflicts using confidence factors
    
    async def _compare_ab_async(self, joke_a_text, joke_b_text):
        # Compare A vs B with examples
        # Return comparison result
    
    async def _compare_ba_async(self, joke_b_text, joke_a_text):
        # Compare B vs A with examples
        # Return comparison result
    
    def _resolve_tournament_result(self, ab_result, ba_result, joke_a, joke_b, 
                                 match_info, lives_tracker):
        # Check consistency
        # Handle ties (both advance if same confidence exactly)
        # Update lives if loser has lives remaining
        # Create comprehensive DuelResult
```

#### 12. `PC_jokespace/judges/main_judge.py`
**Purpose**: Orchestrate complete pipeline with XML logging

**Implementation Details**:
- Accept batch_size and top_count parameters
- Create timestamped output directory only if valid jokes exist
- Run rating phase with specified batch size
- Select specified number of top jokes
- Run tournament with variable participants
- Log all results to XML files
- Return winner id, text, and log directory path
- Handle no valid jokes case gracefully

**Classes and Functions**:
```python
class JokeJudgeSystem:
    def __init__(self, output_dir):
        # Initialize all components
        # Load XML configurations with correct paths
        # Set up output directory
    
    async def run_complete_evaluation(self, jokes_file_path, batch_size=20, top_count=20):
        # Main pipeline with configurable parameters:
        # 1. Load and validate jokes
        # 2. If no valid jokes, return (None, None) immediately
        # 3. Run batch rating evaluation with specified batch_size
        # 4. Select top_count jokes for tournament
        # 5. Run tournament with lives and bye system
        # 6. Log all results
        # 7. Return winner (id, text) and log directory
    
    def _load_jokes(self, jokes_file_path):
        # Use XMLConfigParser to load jokes
        # Skip invalid jokes with warnings
        # Return list of valid jokes (may be empty)
    
    async def _run_rating_phase(self, jokes, batch_size):
        # Use BatchProcessor with specified batch_size
        # Show progress updates
        # Return all results with ranks
    
    async def _run_tournament_phase(self, top_jokes):
        # Use TournamentManager with lives and bye system
        # Support any number of participants
        # Return comprehensive tournament result
    
    async def _log_all_results(self, all_ratings, top_jokes, tournament_result):
        # Log rating results with admissibility details
        # Log top N jokes with ranks (N = top_count used)
        # Log tournament results with lives and bye tracking
        # Log all duel matches with round organization
    
    def _generate_timestamped_filenames(self):
        # Create unique filenames with timestamp
        # Prevent overwriting previous runs
    
    def _extract_filename_from_path(self, file_path):
        # Extract base filename without extension
        # Use for output directory naming
```

## Key Implementation Notes:

1. **CLI Arguments**: Accept three arguments - jokes file (required), batch size (optional, default 20), top count (optional, default 20)
2. **Model Configuration**: Use `claude-3-5-sonnet-20241022` with temperature 0.1
3. **DSPy Caching**: DSPy handles caching automatically - no custom implementation needed
4. **Error Handling**: Maximum 10 retries for API calls, print error and return None if no valid jokes
5. **Flexible Tournament Size**: Support any number of tournament participants, not fixed at 20
6. **Lives System**: Carefully track lives throughout tournament, maintaining original seeding
7. **Bye System**: Top-rated player gets bye unless they had one in previous round - no consecutive byes
8. **Category/Factor Handling**: Drop categories with no relevant factors, score duplicate factors separately
9. **Independent Category**: Uses factors from all categories with their original context (description, examples)
10. **Progress Updates**: Print real-time status to terminal during batch processing
11. **XML Structure**: Use 4-space indentation, include all metadata and tracking information
12. **Output Directory**: Name based on input filename and timestamp, skip creation if no valid jokes
13. **Return Value**: Return winner joke id, text, and log directory path (or None, None if no valid jokes)

## File Path Summary:
- Configuration XMLs:
  - `PC_jokespace/criteria_category_of_jokes.xml`
  - `PC_jokespace/factors_to_judge_joke.xml`
  - `PC_jokespace/judges/good_vs_bad_joke.xml`
- Output: `logs/{input_filename}_{YYYY_MM_DD_HH_MM_SS}/`

## Usage Examples:

```bash
# Process 300 jokes with default settings
python -m judges jokes_dataset.xml

# Process with larger batches for faster evaluation
python -m judges jokes_dataset.xml --batch-size 50

# Run tournament with only top 16 jokes
python -m judges jokes_dataset.xml --top-count 16

# Custom configuration for both parameters
python -m judges jokes_dataset.xml --batch-size 30 --top-count 24

# Error case - no valid jokes in file
python -m judges empty_or_invalid.xml
# Output: Error: No valid jokes found in input file (in RED)
```

This complete revised plan incorporates all clarifications and discussions, including the revised bye mechanism, error handling for no valid jokes, proper file paths, category/factor handling, and all other implementation details discussed.