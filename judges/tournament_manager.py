import asyncio
from typing import List, Dict, Optional, Tuple
from judges.models import RatingResult, DuelResult, TournamentResult
from judges.duel_judge import DuelJudge

class TournamentManager:
    def __init__(self, duel_judge: DuelJudge):
        """Initialize with duel judge"""
        self.duel_judge = duel_judge
        self.lives_tracker = {}
        self.bye_tracker = {}
    
    def run_tournament(self, top_jokes: List[RatingResult]) -> TournamentResult:
        """Run tournament with lives system and bye handling"""
        if not top_jokes:
            return None
        
        # Initialize lives based on original ranking
        self.lives_tracker = self._initialize_lives(top_jokes)
        self.bye_tracker = {joke.joke_id: [] for joke in top_jokes}
        
        # Track all matches
        all_matches = []
        current_participants = top_jokes.copy()
        round_number = 1
        
        # Run tournament rounds
        while len(current_participants) > 1:
            round_matches, survivors = self._run_tournament_round(
                current_participants, round_number, self.bye_tracker
            )
            all_matches.extend(round_matches)
            current_participants = survivors
            round_number += 1
        
        # Determine winner
        winner = current_participants[0] if current_participants else None
        
        # Calculate final rankings
        final_rankings = self._calculate_final_rankings(top_jokes, all_matches)
        
        # Prepare lives tracking data
        lives_tracking_data = {}
        for joke_id, initial_lives in self.lives_tracker.items():
            lives_used = initial_lives - self._get_current_lives(joke_id, all_matches)
            lives_remaining = self._get_current_lives(joke_id, all_matches)
            lives_tracking_data[joke_id] = [initial_lives, lives_used, lives_remaining]
        
        return TournamentResult(
            winner_joke=winner,
            final_rankings=final_rankings,
            lives_tracking=lives_tracking_data,
            bye_tracking=self.bye_tracker,
            original_top_jokes=top_jokes,
            all_duel_matches=all_matches,
            total_jokes_processed=len(top_jokes),
            tournament_rounds=round_number - 1,
            top_count_used=len(top_jokes)
        )
    
    def _initialize_lives(self, jokes: List[RatingResult]) -> Dict[int, int]:
        """Initialize lives based on original ranking"""
        lives = {}
        for joke in jokes:
            if joke.original_rank == 1:
                lives[joke.joke_id] = 3
            elif joke.original_rank == 2:
                lives[joke.joke_id] = 2
            elif joke.original_rank == 3:
                lives[joke.joke_id] = 1
            else:
                lives[joke.joke_id] = 0
        return lives
    
    def _run_tournament_round(self, participants: List[RatingResult], round_number: int,
                            bye_history: Dict[int, List[int]]) -> Tuple[List[DuelResult], List[RatingResult]]:
        """Run a single tournament round"""
        round_name = self._create_round_name(len(participants))
        matches = []
        survivors = []
        
        # Handle bye if odd number
        bye_recipient = None
        active_participants = participants.copy()
        
        if len(active_participants) % 2 == 1:
            bye_recipient, active_participants = self._select_bye_recipient(
                active_participants, bye_history, round_number
            )
            survivors.append(bye_recipient)
            
            # Create bye match record
            bye_match = DuelResult(
                match_id=f"R{round_number}_BYE",
                round_number=round_number,
                round_name=round_name,
                joke_a_id=bye_recipient.joke_id,
                joke_a_seed=bye_recipient.original_rank,
                joke_a_lives_before=self._get_current_lives(bye_recipient.joke_id, matches),
                joke_b_id=-1,  # Bye indicator
                joke_b_seed=-1,
                joke_b_lives_before=0,
                winner_id=bye_recipient.joke_id,
                loser_advanced_by_life=False,
                confidence_factor=0.0,
                position_consistent=True,
                reasoning="Bye - advanced automatically"
            )
            matches.append(bye_match)
        
        # Create matches using traditional seeding
        sorted_participants = sorted(active_participants, key=lambda x: x.original_rank)
        num_matches = len(sorted_participants) // 2
        
        for i in range(num_matches):
            joke_a = sorted_participants[i]
            joke_b = sorted_participants[-(i+1)]
            
            # Get current lives
            joke_a_lives = self._get_current_lives(joke_a.joke_id, matches)
            joke_b_lives = self._get_current_lives(joke_b.joke_id, matches)
            
            # Run duel
            match_result = self.duel_judge.compare_jokes_for_tournament(
                joke_a, joke_b,
                match_id=f"R{round_number}_M{i+1}",
                round_number=round_number,
                round_name=round_name,
                lives_tracker={joke_a.joke_id: joke_a_lives, joke_b.joke_id: joke_b_lives}
            )
            
            matches.append(match_result)
            
            # Process match result
            advancing_jokes = self._process_match_result(match_result, self.lives_tracker)
            for joke_id in advancing_jokes:
                survivor = next(j for j in [joke_a, joke_b] if j.joke_id == joke_id)
                survivors.append(survivor)
        
        return matches, survivors
    
    def _select_bye_recipient(self, participants: List[RatingResult],
                            bye_history: Dict[int, List[int]], current_round: int) -> Tuple[RatingResult, List[RatingResult]]:
        """Select bye recipient avoiding consecutive byes"""
        # Sort by original rank (best first)
        sorted_participants = sorted(participants, key=lambda x: x.original_rank)
        
        # Find first player who didn't receive bye in previous round
        for participant in sorted_participants:
            joke_id = participant.joke_id
            if current_round - 1 not in bye_history.get(joke_id, []):
                # This player can receive bye
                bye_history[joke_id].append(current_round)
                remaining = [p for p in participants if p.joke_id != joke_id]
                return participant, remaining
        
        # If everyone had bye last round (shouldn't happen), give to top player
        top_player = sorted_participants[0]
        bye_history[top_player.joke_id].append(current_round)
        remaining = [p for p in participants if p.joke_id != top_player.joke_id]
        return top_player, remaining
    
    def _process_match_result(self, match: DuelResult, lives_tracker: Dict[int, int]) -> List[int]:
        """Determine who advances from a match"""
        advancing = [match.winner_id]
        
        # Check if loser has lives
        loser_id = match.joke_b_id if match.winner_id == match.joke_a_id else match.joke_a_id
        
        if loser_id != -1:  # Not a bye
            current_lives = self._get_current_lives(loser_id, [])
            if current_lives > 0:
                # Loser uses a life to advance
                advancing.append(loser_id)
                match.loser_advanced_by_life = True
        
        return advancing
    
    def _create_round_name(self, participants_count: int) -> str:
        """Create appropriate round name"""
        if participants_count == 2:
            return "Final"
        elif participants_count == 4:
            return "Semi-Final"
        elif participants_count == 8:
            return "Quarter-Final"
        else:
            return f"Round of {participants_count}"
    
    def _get_current_lives(self, joke_id: int, completed_matches: List[DuelResult]) -> int:
        """Calculate current lives for a joke"""
        initial_lives = self.lives_tracker.get(joke_id, 0)
        lives_used = 0
        
        for match in completed_matches:
            if match.loser_advanced_by_life:
                # Check if this joke was the loser who used a life
                if match.winner_id != joke_id and (match.joke_a_id == joke_id or match.joke_b_id == joke_id):
                    lives_used += 1
        
        return max(0, initial_lives - lives_used)
    
    def _calculate_final_rankings(self, original_jokes: List[RatingResult], 
                                all_matches: List[DuelResult]) -> List[Tuple[RatingResult, int, int]]:
        """Calculate final tournament rankings"""
        # Track elimination round for each joke
        elimination_round = {}
        max_round = max(m.round_number for m in all_matches) if all_matches else 0
        
        for joke in original_jokes:
            # Find when joke was eliminated
            for match in all_matches:
                if match.joke_b_id == -1:  # Skip bye matches
                    continue
                    
                loser_id = match.joke_b_id if match.winner_id == match.joke_a_id else match.joke_a_id
                if loser_id == joke.joke_id and not match.loser_advanced_by_life:
                    elimination_round[joke.joke_id] = match.round_number
                    break
            
            # If not found, joke made it to the end
            if joke.joke_id not in elimination_round:
                elimination_round[joke.joke_id] = max_round + 1
        
        # Sort by elimination round (later = better) and original rank as tiebreaker
        sorted_jokes = sorted(original_jokes, 
                            key=lambda x: (-elimination_round[x.joke_id], x.original_rank))
        
        # Assign tournament ranks
        rankings = []
        for i, joke in enumerate(sorted_jokes):
            lives_remaining = self._get_current_lives(joke.joke_id, all_matches)
            rankings.append((joke, i + 1, lives_remaining))
        
        return rankings

