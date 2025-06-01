from typing import List, Dict, Optional, Tuple
from pydantic import BaseModel

class CategoryInfo(BaseModel):
    """Pydantic model for category information including name, description, and examples"""
    name: str
    description: str
    example1: Optional[str] = ""
    example2: Optional[str] = ""

class AdmissibilityCheck(BaseModel):
    passed: bool
    reasoning: str

class AdmissibilityResults(BaseModel):
    intent_check: AdmissibilityCheck
    completeness_check: AdmissibilityCheck
    appropriateness_check: AdmissibilityCheck
    coherence_check: AdmissibilityCheck
    accessibility_check: AdmissibilityCheck
    is_admissible: bool

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
    # New fields for enhanced display
    ab_confidence: Optional[float] = None
    ba_confidence: Optional[float] = None
    ab_winner_id: Optional[int] = None
    ba_winner_id: Optional[int] = None
    decision_type: Optional[str] = None  # "consistent", "by_confidence", "by_tie", "by_rating"

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