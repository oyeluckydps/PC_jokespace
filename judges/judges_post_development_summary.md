# Joke Judging System: Post-Code Summary

## 1. Overall Motive and System Design

The primary motive of this repository is to create a sophisticated, LLM-based system for evaluating the quality of jokes. This system aims to minimize common LLM biases (like position bias) and provide a nuanced, multi-faceted evaluation that goes beyond simple "funny" or "not funny" labels. It's designed to be used for assessing collections of jokes, potentially for content curation, analysis, or competitive ranking.

The system employs a **two-judge design**:

1.  **Rating Judge**: This judge performs an in-depth, criteria-based evaluation of individual jokes. Its purpose is to provide a comprehensive, multi-dimensional score for each joke based on various factors and to determine its basic admissibility.
2.  **Duel Judge**: This judge conducts pairwise comparisons between jokes. Its purpose is to make fine-grained distinctions about which joke is funnier when compared directly to another, which is crucial for tournament-style rankings.

These judges are supported by a suite of utility modules for handling API interactions, XML data parsing, and results logging. The entire process can be orchestrated via a command-line interface (CLI).

## 2. Design of the Judges

### 2.1 Rating Judge

**Purpose**:
The Rating Judge is responsible for the initial, detailed assessment of each joke. It determines if a joke is fundamentally sound (admissible) and then scores it based on a predefined set of categories and factors. This provides a rich, structured evaluation for each joke.

**Process**:
The Rating Judge follows a multi-stage pipeline:

1.  **Admissibility Assessment**:
    *   Each joke undergoes five liberal admissibility checks:
        *   `Intent Verification`: Is the text intended to be a joke?
        *   `Completeness Assessment`: Is it a complete joke entity?
        *   `Appropriateness Screening`: Is it free of extremely harmful content?
        *   `Coherence Check`: Does it maintain internal logical consistency?
        *   `Language Accessibility`: Is the humor generally accessible?
    *   A joke must pass all checks to be considered admissible. The evaluation is "liberal," meaning it errs on the side of inclusion.
2.  **Category Classification**:
    *   If admissible, the joke is classified into one or more predefined categories (e.g., "Observational", "Pun", "Wordplay"). These categories are loaded from `criteria_category_of_jokes.xml`.
    *   If a joke doesn't fit any existing categories, it's marked as "Independent."
    *   **Enhanced Prompting**: The category assignment now uses enhanced prompts with detailed analysis frameworks to reduce bias and improve accuracy. Categories are randomized to prevent position bias.
3.  **Factor Identification**:
    *   Based on the assigned categories (or all factors if "Independent"), relevant evaluation factors are selected. Factors are specific criteria like "Originality," "Setup-Punchline Cohesion," etc., loaded from `factors_to_judge_joke.xml`. Each factor has a description and positive/negative examples.
    *   If no relevant factors are found for a category, that category might be dropped for the joke.
4.  **Factor-Based Scoring**:
    *   Each relevant factor is scored on a scale of 0-5.
    *   An `overall_rating` is then calculated for the joke. The current formula is `(max_score * 10 + mean_score + len(scores) / 5) / 12`, which aims to give weight to high-scoring factors and the breadth of factors involved, normalized to roughly a 0-5 scale.

### 2.2 Duel Judge

**Purpose**:
The Duel Judge is used for direct head-to-head comparisons of jokes, typically after an initial rating phase has selected a pool of good candidates. This is essential for tournament-style elimination and ranking where relative funniness is key.

**Process**:
The Duel Judge focuses on bias mitigation and robust comparison:

1.  **Dual Comparison**:
    *   To mitigate position bias, each pair of jokes (Joke A, Joke B) is compared twice:
        *   First: A vs. B
        *   Second: B vs. A
    *   Good and bad joke examples (from `judges/good_vs_bad_joke.xml`) are provided as few-shot context.
2.  **Confidence and Reasoning**:
    *   For each comparison, the LLM determines a winner and a confidence factor (a float >= 1.0).
3.  **Conflict Resolution**:
    *   **Consistent Decision**: If both comparisons (A vs. B and B vs. A) yield the same winner, this winner is chosen. The confidence is averaged.
    *   **Inconsistent Decision (Tie in Confidence)**: If the winners differ but confidences are equal:
        *   The joke with the higher `overall_rating` (from the Rating Judge) wins.
        *   If ratings are also equal, the joke with the lower `original_rank` (initial seed) wins.
    *   **Inconsistent Decision (Different Confidence)**: The winner from the comparison with the higher confidence factor is chosen.
4.  **Result**: The final output includes the determined winner, the aggregated confidence, and detailed reasoning, including how any conflicts were resolved.

## 3. File Descriptions

### 3.1 `judges/` Directory

*   **`__init__.py`**:
    *   **Description**: Standard Python package initializer.
    *   **Purpose**: Makes the `judges` directory a Python package.
    *   **Required**: Yes, for proper module import.

*   **`admissibility_checker.py`**:
    *   **Description**: Handles all admissibility checks for jokes using enhanced liberal prompting.
    *   **Purpose**: To determine if a joke meets basic criteria for evaluation with bias towards inclusion.
    *   **Class `AdmissibilityChecker`**:
        *   **`__init__(self, client, max_retries)`**: Initializes with `ClaudeClient` and retry settings. Sets up `dspy.Predict(AdmissibilitySignature)`.
        *   **`check_all_admissibility_async(self, joke_text)`**: Runs all five admissibility checks in parallel using `asyncio.gather()`.
        *   **`_check_intent_async(self, joke_text)` through `_check_accessibility_async(self, joke_text)`**: Individual async methods for each admissibility check with enhanced liberal prompting and clear examples.
        *   **`_retry_on_error(self, func, *args, **kwargs)`**: Generic retry wrapper with exponential backoff.
    *   **Usage**: Used by main `RatingJudge` orchestrator for the admissibility phase.

*   **`category_classifier.py`**:
    *   **Description**: Handles category assignment for jokes with enhanced bias reduction techniques.
    *   **Purpose**: To assign jokes to appropriate categories while minimizing position and popularity bias.
    *   **Class `CategoryClassifier`**:
        *   **`__init__(self, client, category_info_list, max_retries)`**: Initializes with `ClaudeClient`, `CategoryInfo` objects, and retry settings. Sets up `dspy.Predict(CategoryAssignmentSignature)`.
        *   **`classify_categories_async(self, joke_text)`**: Assigns categories using enhanced prompting with randomized category order to reduce position bias. Uses detailed analysis framework.
        *   **`_retry_on_error(self, func, *args, **kwargs)`**: Generic retry wrapper.
    *   **Usage**: Used by main `RatingJudge` orchestrator for the category assignment phase.

*   **`factor_selector.py`**:
    *   **Description**: Handles factor selection for jokes based on assigned categories.
    *   **Purpose**: To identify relevant evaluation factors for each joke based on its categories.
    *   **Class `FactorSelector`**:
        *   **`__init__(self, client, factors, max_retries)`**: Initializes with `ClaudeClient`, factors dictionary, and retry settings. Sets up `dspy.Predict(FactorSelectionSignature)`.
        *   **`select_factors_per_category_async(self, joke_text, categories, is_independent)`**: Main async method to select factors. Handles both regular categories and "Independent" category logic.
        *   **`_select_category_factors_async(self, joke_text, category)`**: Selects factors for a specific category.
        *   **`_select_from_all_factors_async(self, joke_text, all_factors)`**: Selects factors when category is "Independent" (considers all available factors).
        *   **`_retry_on_error(self, func, *args, **kwargs)`**: Generic retry wrapper.
    *   **Usage**: Used by main `RatingJudge` orchestrator for the factor selection phase.

*   **`factor_scorer.py`**:
    *   **Description**: Handles factor scoring for jokes with parallel processing.
    *   **Purpose**: To score jokes on individual factors efficiently using parallel LLM calls.
    *   **Class `FactorScorer`**:
        *   **`__init__(self, client, max_retries)`**: Initializes with `ClaudeClient` and retry settings. Sets up `dspy.Predict(FactorScoringSignature)`.
        *   **`score_factors_async(self, joke_text, factors, factor_objects)`**: Scores each factor in parallel using `asyncio.gather()`. Handles duplicate factor names with suffix notation.
        *   **`_score_single_factor_async(self, joke_text, factor)`**: Scores a joke on a single factor using enhanced prompting with positive/negative examples.
        *   **`_retry_on_error(self, func, *args, **kwargs)`**: Generic retry wrapper.
    *   **Usage**: Used by main `RatingJudge` orchestrator for the factor scoring phase.

*   **`batch_processor.py`**:
    *   **Description**: Handles the processing of jokes in batches, including progress display and retries for individual joke evaluations.
    *   **Purpose**: To efficiently evaluate a large number of jokes by parallelizing calls (conceptually, via `asyncio.gather`) and managing API rate limits or transient errors robustly.
    *   **Class `BatchProcessor`**:
        *   **`__init__(self, rating_judge, batch_size)`**: Initializes with a `RatingJudge` instance and batch size.
        *   **`process_all_jokes(self, jokes)`**: Asynchronously processes a list of `JokeData` objects. It breaks them into batches, calls `_process_batch` for each, displays progress, and handles retries.
        *   **`_process_batch(self, batch, batch_start_idx)`**: Asynchronously processes a single batch of jokes by creating tasks for `_evaluate_joke_with_retry`.
        *   **`_evaluate_joke_with_retry(self, joke, joke_index, max_retries)`**: Attempts to evaluate a single joke using the `rating_judge`, with exponential backoff and retry logic for API errors (like rate limits or timeouts).
        *   **`_display_joke_result(self, result, joke_index)`**: Prints a summary of a single joke's rating result to the console.
        *   **`_create_rating_bar(self, rating, width)`**: Helper to create a simple text-based rating bar.
        *   **`_display_progress(self, total_jokes)`**: Shows overall progress, elapsed time, and ETA.
        *   **`_display_final_summary(self, all_results, total_jokes)`**: Prints a summary of the entire rating phase, including statistics.
    *   **Usage**: Used by `JokeJudgeSystem` in `main_judge.py` to conduct the rating phase.

*   **`cli.py`**:
    *   **Description**: Provides the command-line interface for the joke judging system.
    *   **Purpose**: Allows users to run the evaluation pipeline from the terminal, specifying input files and parameters.
    *   **Function `main()`**: Entry point. Parses arguments and calls either `run_batch_evaluation` (full mode) or `run_rating_only_evaluation`.
    *   **Function `parse_arguments()`**: Uses `argparse` to define and parse CLI arguments (`jokes_file`, `--batch-size`, `--top-count`, `--bypass-cache`, `--rating-only`, `--retries`).
    *   **Function `run_batch_evaluation(...)`**: Orchestrates the full evaluation (rating + tournament). Initializes `JokeJudgeSystem` and calls its `run_complete_evaluation` method.
    *   **Function `run_rating_only_evaluation(...)`**: Orchestrates the rating-only evaluation. Initializes `JokeJudgeSystem` and calls its `run_rating_only_evaluation` method.
    *   **Function `display_rating_only_results(top_jokes)`**: Prints the top-rated jokes to the console in rating-only mode.
    *   **Function `display_progress(current_joke, total_jokes, status)`**: (Currently seems unused directly by `cli.py` but intended for progress, handled by `BatchProcessor`).
    *   **Function `display_final_results(winner_id, winner_text, log_dir)`**: Prints the final tournament winner and log directory.
    *   **Usage**: Executed when running `python -m judges ...`.

*   **`dspy_signatures.py`**:
    *   **Description**: Defines the DSPy signatures for various LLM interactions with enhanced prompting structures.
    *   **Purpose**: Structures the input and output fields for prompts sent to the LLM, ensuring consistency and clarity for the model.
    *   **Class `AdmissibilitySignature(dspy.Signature)`**: Defines fields for admissibility checks (`joke_text`, `check_type`, `instruction_prompt`, `examples` -> `passed`, `reasoning`).
    *   **Class `CategoryAssignmentSignature(dspy.Signature)`**: Enhanced to include `available_categories` (containing `CategoryInfo` objects) and `instruction` field for detailed analysis framework -> `selected_categories`, `is_independent`, `reasoning`.
    *   **Class `FactorSelectionSignature(dspy.Signature)`**: Defines fields for selecting relevant factors (`joke_text`, `category`, `available_factors` -> `relevant_factors`, `reasoning`).
    *   **Class `FactorScoringSignature(dspy.Signature)`**: Defines fields for scoring a joke on a specific factor (`joke_text`, `factor_name`, `factor_description`, `positive_examples`, `negative_examples` -> `score`, `reasoning`).
    *   **Class `DuelComparisonSignature(dspy.Signature)`**: Defines fields for comparing two jokes (`joke_a`, `joke_b`, `good_examples`, `bad_examples` -> `winner`, `confidence_factor`, `reasoning`).
    *   **Usage**: These signatures are used by `dspy.Predict` in the specialized rating components and `DuelJudge` to interact with the LLM.

*   **`duel_judge.py`**:
    *   **Description**: Implements the logic for comparing two jokes head-to-head.
    *   **Purpose**: To determine a winner between two jokes with bias mitigation techniques.
    *   **Class `DuelJudge`**:
        *   **`__init__(self, client, examples, max_retries)`**: Initializes with a `ClaudeClient`, example jokes, and max retries. Sets up `dspy.Predict(DuelComparisonSignature)`.
        *   **`compare_jokes_for_tournament(self, joke_a, joke_b, match_id, round_number, round_name, lives_tracker)`**: Asynchronously compares two `RatingResult` objects for a tournament match. It calls `compare_jokes_async` and then formats the result using `_build_duel_result`. (Note: `asyncio.run` was removed, making this an `async` method).
        *   **`compare_jokes_async(self, joke_a, joke_b)`**: Core async comparison logic. Runs `_compare_ab_async` and `_compare_ba_async` in parallel, then resolves them using `_resolve_comparison`.
        *   **`_retry_on_error(self, func, *args, **kwargs)`**: Generic async retry wrapper for LLM calls.
        *   **`_compare_ab_async(self, joke_a_text, joke_b_text)`**: Performs a single LLM call to compare A vs. B.
        *   **`_compare_ba_async(self, joke_b_text, joke_a_text)`**: Performs a single LLM call to compare B vs. A (inputs swapped).
        *   **`_resolve_comparison(self, ab_result, ba_result, joke_a, joke_b)`**: Resolves results from A->B and B->A comparisons. Handles consistent decisions, ties (broken by rating then seed), and inconsistent decisions (broken by confidence). Returns detailed comparison metrics.
        *   **`_build_duel_result(self, joke_a, joke_b, comparison, match_id, round_number, round_name, lives_tracker)`**: Constructs a `DuelResult` object from the comparison outcome and match metadata.
    *   **Usage**: Used by `TournamentManager` to conduct duels in a tournament.

*   **`main_judge.py`**:
    *   **Description**: Orchestrates the entire joke evaluation pipeline, integrating the Rating Judge, Duel Judge, Batch Processor, and Tournament Manager.
    *   **Purpose**: Acts as the central controller for the joke judging system.
    *   **Class `JokeJudgeSystem`**:
        *   **`__init__(self, output_dir, bypass_cache, max_retries)`**: Initializes all core components: `ClaudeClient`, `XMLConfigParser`, `RatingJudge`. `DuelJudge` is initialized lazily if a full tournament is run.
        *   **`run_complete_evaluation(self, jokes_file_path, batch_size, top_count)`**: Executes the full pipeline: load jokes, rate jokes, select top N, run tournament, log results.
        *   **`run_rating_only_evaluation(self, jokes_file_path, batch_size, top_count)`**: Executes only the rating phase and logs the top N jokes.
        *   **`_load_jokes(self, jokes_file_path)`**: Uses `XMLConfigParser` to load jokes.
        *   **`_run_rating_phase(self, jokes, batch_size)`**: Uses `BatchProcessor` to rate all jokes.
        *   **`_run_tournament_phase(self, top_jokes)`**: Initializes and uses `TournamentManager` to run the tournament.
        *   **`_log_rating_results(self, all_ratings)`**: Logs rating results using `XMLLogger`.
        *   **`_log_top_jokes(self, top_jokes)`**: Logs top jokes using `XMLLogger`.
        *   **`_log_tournament_results(self, tournament_result)`**: Logs tournament results using `XMLLogger`.
        *   **`_log_rating_only_summary(self, top_jokes, total_jokes, admissible_jokes)`**: Creates a text summary file for rating-only mode.
    *   **Usage**: Instantiated and used by `cli.py` to run evaluations.

*   **`models.py`**:
    *   **Description**: Defines Pydantic models for structuring data throughout the system.
    *   **Purpose**: Ensures data consistency and provides type validation for various results and inputs.
    *   **Class `CategoryInfo(BaseModel)`**: New model for category information including `name`, `description`, `example1`, and `example2` fields.
    *   **Class `AdmissibilityCheck(BaseModel)`**: Stores result of a single admissibility check (`passed`, `reasoning`).
    *   **Class `AdmissibilityResults(BaseModel)`**: Aggregates all five admissibility checks and an overall `is_admissible` flag.
    *   **Class `RatingResult(BaseModel)`**: Comprehensive result for a single joke after rating (ID, text, admissibility, categories, factors, scores, overall rating, original rank).
    *   **Class `DuelResult(BaseModel)`**: Result of a single duel (match metadata, joke IDs, seeds, lives, winner, confidence, consistency, reasoning, and detailed A/B comparison stats).
    *   **Class `TournamentResult(BaseModel)`**: Overall result of a tournament (winner, rankings, lives/bye tracking, all matches, etc.).
    *   **Usage**: Used extensively across all modules to pass structured data.

*   **`rating_judge.py`**:
    *   **Description**: Main orchestrator class that coordinates all specialized rating components.
    *   **Purpose**: To manage the complete rating pipeline while delegating specific tasks to specialized components.
    *   **Class `RatingJudge`**:
        *   **`__init__(self, client, categories, factors, examples, category_info_list, max_retries)`**: Initializes with `ClaudeClient`, pre-parsed categories/factors/examples, `CategoryInfo` objects, and retry settings. Initializes specialized components: `AdmissibilityChecker`, `CategoryClassifier`, `FactorSelector`, and `FactorScorer`.
        *   **`evaluate_joke(self, joke)`**: Synchronous wrapper for `evaluate_joke_async`.
        *   **`evaluate_joke_async(self, joke)`**: Main async pipeline orchestrator that coordinates the specialized components: admissibility check, category classification, factor selection, factor scoring, and final rating calculation with detailed timing logs.
    *   **Usage**: Used by `BatchProcessor` to rate jokes through the coordinated pipeline.

*   **`tournament_manager.py`**:
    *   **Description**: Manages the execution of a tournament between a list of top-rated jokes.
    *   **Purpose**: To determine an ultimate winner through a series of duels, incorporating a lives and bye system.
    *   **Class `TournamentManager`**:
        *   **`__init__(self, duel_judge)`**: Initializes with a `DuelJudge` instance.
        *   **`run_tournament(self, top_jokes)`**: Asynchronously runs the entire tournament. Initializes lives, then iteratively calls `_run_tournament_round` until one winner remains.
        *   **`_initialize_lives(self, jokes)`**: Sets initial lives for jokes based on their `original_rank` (Rank 1: 3 lives, Rank 2: 2, Rank 3: 1, Others: 0).
        *   **`_get_initial_lives_count(self, jokes)`**: Helper to get the initial lives map.
        *   **`_run_tournament_round(self, participants, round_number, all_previous_matches)`**: Asynchronously runs a single round: handles byes, pairs participants for duels (using `duel_judge`), processes results, and determines survivors.
        *   **`_display_match_result(self, match, joke_a, joke_b)`**: Prints detailed results of a single duel to the console.
        *   **`_select_bye_recipient(self, participants, bye_history, current_round)`**: Selects a participant to receive a bye, prioritizing higher-ranked jokes that didn't have a bye in the previous round.
        *   **`_process_match_result(self, match)`**: Determines which joke(s) advance from a match. If a loser has lives, they use one and advance. Updates `lives_remaining` and `total_lives_used`.
        *   **`_display_round_summary(self, round_number, round_matches, survivors)`**: Prints a summary of a completed round to the console.
        *   **`_create_round_name(self, participants_count)`**: Generates a name for the round (e.g., "Final", "Semi-Final").
        *   **`_calculate_final_rankings(self, original_jokes, all_matches)`**: Determines the final tournament rank for all participants based on when they were eliminated.
    *   **Usage**: Used by `JokeJudgeSystem` to run the tournament phase.

### 3.2 `utilities/` Directory

*   **`__init__.py`**:
    *   **Description**: Standard Python package initializer, may also expose key classes for easier import.
    *   **Purpose**: Makes the `utilities` directory a Python package.
    *   **Required**: Yes, for proper module import.

*   **`dspy_client.py`**:
    *   **Description**: Provides a client for interacting with the Claude LLM via the DSPy library.
    *   **Purpose**: Encapsulates API key management, model configuration, retry logic, and caching for LLM calls.
    *   **Class `ClaudeClient`**:
        *   **`__init__(self, model, api_key, cache)`**: Initializes the DSPy LM with the specified Claude model (defaults to Haiku), API key (from env var), and caching preference. It includes a small random temperature adjustment if caching is disabled to help bypass DSPy's aggressive caching if needed.
        *   **`generate(self, prompt, max_tokens, temperature)`**: Sends a prompt to the LLM and returns the response. Implements retry logic with delays for API failures.
        *   **`_get_api_key(self)`**: Retrieves the `ANTHROPIC_API_KEY` from environment variables.
    *   **Usage**: Instantiated and used by `JokeJudgeSystem`, specialized rating components, and `DuelJudge` for all LLM interactions.

*   **`xml_parser.py`**:
    *   **Description**: Handles parsing of all XML configuration files and the input joke XML file with enhanced category information support.
    *   **Purpose**: To load criteria, categories, factors, example jokes, and input jokes from their respective XML files into Pydantic models.
    *   **Pydantic Models (`CategoryInfo`, `Factor`, `Category`, `ExampleData`, `JokeData`)**: Define the structure for the data parsed from XML. `CategoryInfo` is a new model that encapsulates category name, description, and examples.
    *   **Class `XMLConfigParser`**:
        *   **`__init__(self, base_path)`**: Initializes with the base path for XML files.
        *   **`parse_categories(self)`**: Parses `criteria_category_of_jokes.xml` into a flat list of category names.
        *   **`parse_category_info(self)`**: **NEW METHOD** - Parses `criteria_category_of_jokes.xml` into a list of `CategoryInfo` objects containing name, description, and up to 2 examples per category.
        *   **`parse_categories_with_descriptions(self)`**: Parses categories with descriptions as tuples (maintained for backward compatibility).
        *   **`parse_category_examples(self)`**: Parses category examples as dictionary (maintained for backward compatibility).
        *   **`parse_factors(self)`**: Parses `factors_to_judge_joke.xml` into a dictionary mapping category names to lists of `Factor` objects.
        *   **`parse_examples(self)`**: Parses `judges/good_vs_bad_joke.xml` into an `ExampleData` object (5 good, 5 bad jokes).
        *   **`parse_jokes(self, jokes_file_path)`**: Parses the input jokes XML, validating IDs and text, and returns a list of `JokeData` objects.
        *   **`_load_xml_file(self, filename)`**: Helper to load and parse an XML file using `xml.etree.ElementTree`.
    *   **Usage**: Used by `JokeJudgeSystem` to load all necessary configurations and input data.

*   **`xml_logger.py`**:
    *   **Description**: Responsible for generating all XML output log files.
    *   **Purpose**: To create detailed, well-formatted XML logs of the rating process, top jokes, tournament matches, and final tournament results.
    *   **Class `XMLLogger`**:
        *   **`__init__(self, output_dir)`**: Initializes with the output directory path and creates it if it doesn't exist.
        *   **`log_rating_results(self, results, filename)`**: Creates `rating_results.xml` with detailed admissibility, categories, factors, and scores for every processed joke.
        *   **`log_top_jokes(self, top_jokes, filename)`**: Creates `top_jokes_for_duel.xml` (or `top_jokes_rating_only.xml`) listing the top N jokes with their ratings and key details.
        *   **`log_tournament_results(self, tournament_result, filename)`**: Creates `tournament_results.xml` with the tournament winner, final rankings, and lives/bye tracking for all participants.
        *   **`log_duel_matches(self, all_matches, filename)`**: Creates `duel_matches.xml`, logging every duel played, organized by round, including A/B results, confidence, and reasoning.
        *   **`_create_output_dir(self)`**: Ensures the output directory exists.
        *   **`_format_timestamp(self)`**: Generates a standard timestamp string.
        *   **`_write_xml(self, root, filename)`**: Helper function to pretty-print an `ET.Element` root to an XML file using `minidom` for formatting.
    *   **Usage**: Used by `JokeJudgeSystem` to log all stages of the evaluation.

## 4. Complete Pipeline and Code Flow

1.  **CLI Invocation (`judges/cli.py`)**:
    *   The user runs `python -m judges <jokes_file.xml> [options]`.
    *   `parse_arguments()` processes CLI inputs.
    *   `main()` determines mode (full or rating-only) and calls the appropriate `run_*_evaluation` function.

2.  **System Initialization (`judges/main_judge.py -> JokeJudgeSystem.__init__`)**:
    *   An output directory (e.g., `logs/jokes_file_2023_10_27_12_00_00/`) is determined.
    *   `ClaudeClient` is initialized (API key, model, caching, retries).
    *   `XMLConfigParser` is initialized. It loads:
        *   Categories from `criteria_category_of_jokes.xml`.
        *   **Enhanced**: Category information (including descriptions and examples) using `parse_category_info()` into `CategoryInfo` objects.
        *   Factors from `factors_to_judge_joke.xml`.
        *   Example jokes from `judges/good_vs_bad_joke.xml`.
    *   `RatingJudge` is initialized with the client and parsed configurations, which internally initializes specialized components: `AdmissibilityChecker`, `CategoryClassifier`, `FactorSelector`, and `FactorScorer`.
    *   `DuelJudge` is initialized (if not in rating-only mode) with the client and examples.
    *   `XMLLogger` is initialized with the output directory once jokes are confirmed to be loaded.

3.  **Joke Loading (`JokeJudgeSystem._load_jokes` -> `utilities/xml_parser.parse_jokes`)**:
    *   The input XML file is parsed into a list of `JokeData` objects. Invalid jokes are skipped.
    *   If no valid jokes, the process may terminate early.

4.  **Rating Phase (`JokeJudgeSystem._run_rating_phase` -> `judges/batch_processor.py`)**:
    *   `BatchProcessor` is instantiated with the `RatingJudge`.
    *   `BatchProcessor.process_all_jokes()` iterates through jokes in batches:
        *   For each joke, `_evaluate_joke_with_retry()` calls `RatingJudge.evaluate_joke_async()`.
        *   `RatingJudge.evaluate_joke_async()` **orchestrates specialized components**:
            *   **Admissibility Phase**: `AdmissibilityChecker.check_all_admissibility_async()` performs 5 enhanced liberal admissibility checks in parallel using detailed prompting with clear examples.
            *   **Category Phase**: If admissible, `CategoryClassifier.classify_categories_async()` assigns categories using enhanced prompting with randomized category order and detailed analysis framework to reduce bias.
            *   **Factor Selection Phase**: `FactorSelector.select_factors_per_category_async()` identifies relevant factors based on assigned categories or all factors for "Independent" category.
            *   **Factor Scoring Phase**: `FactorScorer.score_factors_async()` scores each factor in parallel with enhanced prompting using positive/negative examples.
            *   **Final Calculation**: Calculates `max_score`, `mean_score`, and `overall_rating` with detailed timing logs.
            *   Returns a comprehensive `RatingResult` object.
        *   Batch processor collects `RatingResult` objects and displays progress.
    *   `XMLLogger.log_rating_results()` saves `rating_results.xml`.

5.  **Top Jokes Selection (`JokeJudgeSystem.run_complete_evaluation` or `run_rating_only_evaluation`)**:
    *   Admissible jokes are filtered from `all_ratings`.
    *   They are sorted by `overall_rating` in descending order.
    *   The top `N` (from `--top-count`) are selected.
    *   `XMLLogger.log_top_jokes()` saves `top_jokes_for_duel.xml` or `top_jokes_rating_only.xml`.
    *   If in rating-only mode, `_log_rating_only_summary()` creates a text summary, and the process ends.

6.  **Tournament Phase (if not rating-only) (`JokeJudgeSystem._run_tournament_phase` -> `judges/tournament_manager.py`)**:
    *   `TournamentManager` is instantiated with the `DuelJudge`.
    *   `TournamentManager.run_tournament()`:
        *   Initializes lives for participants based on their original rank (from rating phase).
        *   Enters a loop, running rounds (`_run_tournament_round`) until only one participant remains.
        *   `_run_tournament_round()`:
            *   Determines bye recipient if an odd number of participants (`_select_bye_recipient`).
            *   Pairs remaining participants (top seed vs. bottom seed, etc.).
            *   For each pair, calls `DuelJudge.compare_jokes_for_tournament()`:
                *   `DuelJudge.compare_jokes_async()` runs A vs. B and B vs. A comparisons in parallel (`_compare_ab_async`, `_compare_ba_async` using `DuelComparisonSignature`).
                *   `_resolve_comparison()` determines the true winner and confidence, handling ties and inconsistencies.
                *   Returns a `DuelResult`.
            *   `_process_match_result()` updates lives. Losers with lives remaining use one and advance.
            *   Collects survivors for the next round.
        *   After the loop, the single remaining participant is the winner.
    *   `XMLLogger.log_tournament_results()` saves `tournament_results.xml`.
    *   `XMLLogger.log_duel_matches()` saves `duel_matches.xml`.

7.  **Final Output (`judges/cli.py`)**:
    *   The winner's ID and text (if full tournament) or the list of top jokes (if rating-only) are displayed.
    *   The path to the log directory is printed.

## 5. Enhanced Features and Improvements

### 5.1 Modular Architecture
The rating system has been refactored into a modular architecture with specialized components:

*   **`AdmissibilityChecker`**: Dedicated to admissibility checks with enhanced liberal prompting
*   **`CategoryClassifier`**: Specialized for category assignment with bias reduction techniques
*   **`FactorSelector`**: Focused on factor selection based on categories
*   **`FactorScorer`**: Optimized for parallel factor scoring
*   **`RatingJudge`**: Main orchestrator that coordinates all specialized components

This modular design provides:
- **Separation of Concerns**: Each component has a single responsibility
- **Better Maintainability**: Easier to modify individual components
- **Improved Testing**: Can unit test each component separately
- **Cleaner Code**: Each component is focused and manageable in size

### 5.2 Enhanced Prompting and Bias Reduction

**Category Assignment Enhancements**:
- **Randomized Category Order**: Categories are shuffled before each classification to prevent position bias
- **Enhanced Analysis Framework**: Detailed instructions guide the LLM through systematic category analysis
- **Structured Category Information**: Uses `CategoryInfo` objects that bundle name, description, and examples together
- **Bias Awareness**: Explicit instructions to avoid common biases (length bias, popularity bias, position bias)

**Admissibility Check Enhancements**:
- **Liberal Evaluation Guidelines**: Each check includes explicit "liberal evaluation" instructions that err on the side of inclusion
- **Clear Examples**: Each check provides clear pass/fail/borderline examples with detailed explanations
- **Focused Instructions**: Each check focuses only on its specific criterion to avoid cross-contamination

**Factor Scoring Enhancements**:
- **Positive/Negative Examples**: Each factor includes concrete examples of high and low performance
- **Parallel Processing**: All factor scoring happens in parallel for efficiency
- **Enhanced Error Handling**: Robust retry logic with graceful degradation

### 5.3 Data Structure Improvements

**CategoryInfo Model**:
- Encapsulates category name, description, and up to 2 examples in a single object
- Ensures consistent data flow when categories are randomized
- Provides better type safety through Pydantic validation

**Enhanced XML Parsing**:
- New `parse_category_info()` method returns structured `CategoryInfo` objects
- Maintains backward compatibility with existing parsing methods
- Avoids circular import issues through local model definitions

## 6. Sample Commands to Run the Module

*   **Run a full evaluation (rating + tournament) on `temp/100_jokes_dataset.xml`, process 15 jokes per batch, and advance top 10 to tournament:**
    ```bash
    python -m judges.cli temp/100_jokes_dataset.xml --batch-size 15 --top-count 10
    ```

*   **Run a rating-only evaluation on `temp/sample_jokes.xml`, process 5 jokes per batch, and show top 3 rated jokes:**
    ```bash
    python -m judges.cli temp/sample_jokes.xml --batch-size 5 --top-count 3 --rating-only
    ```

*   **Run a full evaluation with default batch size (20) and top count (20), but bypass the DSPy cache and set LLM call retries to 3:**
    ```bash
    python -m judges.cli temp/another_jokes_file.xml --bypass-cache --retries 3
    ```

*   **Run with minimal arguments (will use defaults for batch size and top count for tournament):**
    ```bash
    python -m judges.cli temp/short_jokes_list.xml
    ```