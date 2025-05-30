import asyncio
from typing import Tuple, Optional, List
from pathlib import Path

from PC_jokespace.utilities.dspy_client import ClaudeClient
from PC_jokespace.utilities.xml_parser import XMLConfigParser
from PC_jokespace.utilities.xml_logger import XMLLogger
from PC_jokespace.judges.models import RatingResult
from PC_jokespace.judges.rating_judge import RatingJudge
from PC_jokespace.judges.duel_judge import DuelJudge
from PC_jokespace.judges.batch_processor import BatchProcessor
from PC_jokespace.judges.tournament_manager import TournamentManager

class JokeJudgeSystem:
    def __init__(self, output_dir: str):
        """Initialize all components"""
        self.output_dir = output_dir
        self.logger = None  # Initialize later if needed
        
        # Initialize DSPy client
        self.client = ClaudeClient()
        
        # Load XML configurations
        self.parser = XMLConfigParser()
        self.categories = self.parser.parse_categories()
        self.factors = self.parser.parse_factors()
        self.examples = self.parser.parse_examples()
        
        # Initialize judges
        self.rating_judge = RatingJudge(self.client, self.categories, self.factors, self.examples)
        self.duel_judge = DuelJudge(self.client, self.examples)
    
    async def run_complete_evaluation(self, jokes_file_path: str, batch_size: int = 20, 
                                    top_count: int = 20) -> Tuple[Optional[Tuple[int, str]], Optional[str]]:
        """Main pipeline with configurable parameters"""
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
        return manager.run_tournament(top_jokes)
    
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

