import asyncio
from typing import Tuple, Optional, List
from pathlib import Path

from utilities.dspy_client import ClaudeClient
from utilities.xml_parser import XMLConfigParser
from utilities.xml_logger import XMLLogger
from judges.models import RatingResult
from judges.rating_judge import RatingJudge
from judges.duel_judge import DuelJudge
from judges.batch_processor import BatchProcessor
from judges.tournament_manager import TournamentManager

class JokeJudgeSystem:
    def __init__(self, output_dir: str, bypass_cache: bool = False, max_retries: int = 5):
        """Initialize all components"""
        self.output_dir = output_dir
        self.bypass_cache = bypass_cache
        self.max_retries = max_retries
        self.logger = None  # Initialize later if needed
        
        # Initialize DSPy client with bypass_cache parameter
        self.client = ClaudeClient(cache = not bypass_cache)
        
        # Load XML configurations
        self.parser = XMLConfigParser()
        self.categories = self.parser.parse_categories()
        self.factors = self.parser.parse_factors()
        self.examples = self.parser.parse_examples()
        self.category_info_list = self.parser.parse_category_info()  # New: using CategoryInfo objects
        
        # Initialize judges with max_retries parameter and new category data
        self.rating_judge = RatingJudge(
            client=self.client,
            categories=self.categories,
            factors=self.factors,
            examples=self.examples,
            category_info_list=self.category_info_list,  # New: pass CategoryInfo objects
            max_retries=max_retries
        )
        # Duel judge will be initialized only if needed (not in rating-only mode)
        self.duel_judge = None
    
    async def run_complete_evaluation(self, jokes_file_path: str, batch_size: int = 20, 
                                    top_count: int = 20) -> Tuple[Optional[Tuple[int, str]], Optional[str]]:
        """Main pipeline with configurable parameters"""
        # Initialize duel judge for full evaluation
        if self.duel_judge is None:
            self.duel_judge = DuelJudge(self.client, self.examples, max_retries=self.max_retries)
        
        # Step 1: Load and validate jokes
        jokes = self._load_jokes(jokes_file_path)
        
        if not jokes:
            return (None, None)
        
        # Now create logger since we have valid jokes
        self.logger = XMLLogger(self.output_dir)
        
        print(f"\nLoaded {len(jokes)} valid jokes from {jokes_file_path}")
        print(f"Output directory: {self.output_dir}")
        
        # Step 2: Run rating phase
        print(f"\n{'='*50}")
        print("PHASE 1: Rating Jokes")
        print(f"{'='*50}")
        
        all_ratings = await self._run_rating_phase(jokes, batch_size)
        
        # Log rating results
        await self._log_rating_results(all_ratings)
        
        # Step 3: Select top jokes
        admissible_jokes = [r for r in all_ratings if r.admissibility_results.is_admissible]
        print(f"\nTotal admissible jokes: {len(admissible_jokes)}")
        
        if not admissible_jokes:
            print("\033[91mNo admissible jokes found!\033[0m")
            return (None, self.output_dir)
        
        # Get top N jokes
        top_jokes = sorted(admissible_jokes, key=lambda x: x.overall_rating, reverse=True)[:top_count]
        print(f"Selected top {len(top_jokes)} jokes for tournament")
        
        # Log top jokes
        await self._log_top_jokes(top_jokes)
        
        # Step 4: Run tournament
        print(f"\n{'='*50}")
        print("PHASE 2: Tournament")
        print(f"{'='*50}")
        
        tournament_result = await self._run_tournament_phase(top_jokes)
        
        # Step 5: Log tournament results
        await self._log_tournament_results(tournament_result)
        
        # Return winner
        winner = tournament_result.winner_joke
        return ((winner.joke_id, winner.joke_text), self.output_dir)
    
    async def run_rating_only_evaluation(self, jokes_file_path: str, batch_size: int = 20, 
                                       top_count: int = 20) -> Optional[List[RatingResult]]:
        """Run only the rating phase and return top jokes"""
        # Step 1: Load and validate jokes
        jokes = self._load_jokes(jokes_file_path)
        
        if not jokes:
            return None
        
        # Create logger
        self.logger = XMLLogger(self.output_dir)
        
        print(f"\nLoaded {len(jokes)} valid jokes from {jokes_file_path}")
        print(f"Output directory: {self.output_dir}")
        print(f"Mode: Rating-only (skipping tournament)")
        
        # Step 2: Run rating phase
        print(f"\n{'='*50}")
        print("Rating Jokes (Rating-Only Mode)")
        print(f"{'='*50}")
        
        all_ratings = await self._run_rating_phase(jokes, batch_size)
        
        # Log rating results
        await self._log_rating_results(all_ratings)
        
        # Step 3: Select and return top jokes
        admissible_jokes = [r for r in all_ratings if r.admissibility_results.is_admissible]
        print(f"\nTotal admissible jokes: {len(admissible_jokes)}")
        
        if not admissible_jokes:
            print("\033[91mNo admissible jokes found!\033[0m")
            return None
        
        # Get top N jokes
        top_jokes = sorted(admissible_jokes, key=lambda x: x.overall_rating, reverse=True)[:top_count]
        print(f"\nSelected top {len(top_jokes)} jokes")
        
        # Log top jokes as final results for rating-only mode
        if self.logger:
            self.logger.log_top_jokes(top_jokes)
            print(f"\nTop jokes saved to: {self.output_dir}/top_jokes_rating_only.xml")
        
        # Create a summary file for rating-only mode
        await self._log_rating_only_summary(top_jokes, len(jokes), len(admissible_jokes))
        
        return top_jokes
    
    def _load_jokes(self, jokes_file_path: str) -> List:
        """Load and validate jokes from XML file"""
        return self.parser.parse_jokes(jokes_file_path)
    
    async def _run_rating_phase(self, jokes: List, batch_size: int) -> List[RatingResult]:
        """Run batch rating evaluation"""
        processor = BatchProcessor(self.rating_judge, batch_size)
        return await processor.process_all_jokes(jokes)
    
    async def _run_tournament_phase(self, top_jokes: List[RatingResult]):
        """Run tournament with lives and bye system"""
        manager = TournamentManager(self.duel_judge)
        return await manager.run_tournament(top_jokes)
    
    async def _log_rating_results(self, all_ratings: List[RatingResult]):
        """Log rating results progressively"""
        if self.logger:
            self.logger.log_rating_results(all_ratings)
            print(f"\nRating results saved to: {self.output_dir}/rating_results.xml")
    
    async def _log_top_jokes(self, top_jokes: List[RatingResult]):
        """Log top jokes selected for tournament"""
        if self.logger:
            self.logger.log_top_jokes(top_jokes)
            print(f"Top jokes saved to: {self.output_dir}/top_jokes_for_duel.xml")
    
    async def _log_tournament_results(self, tournament_result):
        """Log tournament results"""
        if self.logger:
            self.logger.log_tournament_results(tournament_result)
            self.logger.log_duel_matches(tournament_result.all_duel_matches)
            print(f"\nTournament results saved to: {self.output_dir}/tournament_results.xml")
            print(f"Duel matches saved to: {self.output_dir}/duel_matches.xml")
    
    async def _log_rating_only_summary(self, top_jokes: List[RatingResult], 
                                     total_jokes: int, admissible_jokes: int):
        """Create a summary file for rating-only mode"""
        if self.logger:
            summary_path = Path(self.output_dir) / "rating_only_summary.txt"
            
            with open(summary_path, 'w') as f:
                f.write("=" * 60 + "\n")
                f.write("RATING-ONLY EVALUATION SUMMARY\n")
                f.write("=" * 60 + "\n\n")
                
                f.write(f"Total jokes processed: {total_jokes}\n")
                f.write(f"Admissible jokes: {admissible_jokes}\n")
                f.write(f"Top jokes selected: {len(top_jokes)}\n\n")
                
                f.write("TOP RATED JOKES:\n")
                f.write("-" * 60 + "\n\n")
                
                for i, joke in enumerate(top_jokes, 1):
                    f.write(f"{i}. Joke ID: {joke.joke_id}\n")
                    f.write(f"   Rating: {joke.overall_rating:.2f} ")
                    f.write(f"(Max: {joke.max_score}, Mean: {joke.mean_score:.2f})\n")
                    f.write(f"   Categories: {', '.join(joke.assigned_categories)}\n")
                    f.write(f"   Text: {joke.joke_text}\n")
                    
                    if joke.factor_scores:
                        top_factors = sorted(joke.factor_scores.items(), 
                                           key=lambda x: x[1], reverse=True)[:3]
                        f.write(f"   Top factors: ")
                        f.write(", ".join(f"{factor}({score})" for factor, score in top_factors))
                        f.write("\n")
                    
                    f.write("\n")
            
            print(f"Summary saved to: {self.output_dir}/rating_only_summary.txt")