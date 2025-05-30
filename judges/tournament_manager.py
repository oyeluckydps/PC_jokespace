import asyncio
from typing import List, Dict, Optional, Tuple
from judges.models import RatingResult, DuelResult, TournamentResult
from judges.duel_judge import DuelJudge

class TournamentManager:
    def __init__(self, duel_judge: DuelJudge):
        """Initialize with duel judge"""
        self.duel_judge = duel_judge
        self.lives_remaining = {}  # Simplified lives tracking
        self.bye_tracker = {}
        self.total_lives_used = 0
    
    async def run_tournament(self, top_jokes: List[RatingResult]) -> TournamentResult:
        """Run tournament with lives system and bye handling"""
        if not top_jokes:
            return None
        
        # Initialize lives based on original ranking
        self._initialize_lives(top_jokes)
        self.bye_tracker = {joke.joke_id: [] for joke in top_jokes}
        
        # Display tournament start
        print(f"\n{'='*70}")
        print(f"TOURNAMENT STARTING")
        print(f"{'='*70}")
        print(f"Total participants: {len(top_jokes)}")
        print(f"Lives distribution: Rank 1: 3 lives, Rank 2: 2 lives, Rank 3: 1 life")
        print(f"{'='*70}\n")
        
        # Track all matches
        all_matches = []
        current_participants = top_jokes.copy()
        round_number = 1
        
        # Run tournament rounds
        while len(current_participants) > 1:
            round_matches, survivors = await self._run_tournament_round(
                current_participants, round_number, all_matches
            )
            all_matches.extend(round_matches)
            current_participants = survivors
            round_number += 1
            
            # Display round summary
            self._display_round_summary(round_number - 1, round_matches, survivors)
        
        # Determine winner
        winner = current_participants[0] if current_participants else None
        
        # Display tournament end
        print(f"\n{'='*70}")
        print(f"🏆 TOURNAMENT COMPLETE 🏆")
        print(f"{'='*70}")
        print(f"Winner: Joke {winner.joke_id} (Original Seed: {winner.original_rank})")
        print(f"Total rounds played: {round_number - 1}")
        print(f"Total lives used: {self.total_lives_used}")
        print(f"{'='*70}\n")
        
        # Calculate final rankings
        final_rankings = self._calculate_final_rankings(top_jokes, all_matches)
        
        # Prepare lives tracking data
        lives_tracking_data = {}
        initial_lives = self._get_initial_lives_count(top_jokes)
        for joke_id in initial_lives:
            lives_used = initial_lives[joke_id] - self.lives_remaining.get(joke_id, 0)
            lives_tracking_data[joke_id] = [
                initial_lives[joke_id], 
                lives_used, 
                self.lives_remaining.get(joke_id, 0)
            ]
        
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
    
    def _initialize_lives(self, jokes: List[RatingResult]):
        """Initialize lives based on original ranking"""
        self.lives_remaining = {}
        for joke in jokes:
            if joke.original_rank == 1:
                self.lives_remaining[joke.joke_id] = 3
            elif joke.original_rank == 2:
                self.lives_remaining[joke.joke_id] = 2
            elif joke.original_rank == 3:
                self.lives_remaining[joke.joke_id] = 1
            else:
                self.lives_remaining[joke.joke_id] = 0
    
    def _get_initial_lives_count(self, jokes: List[RatingResult]) -> Dict[int, int]:
        """Get initial lives for tracking purposes"""
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
    
    async def _run_tournament_round(self, participants: List[RatingResult], round_number: int,
                                  all_previous_matches: List[DuelResult]) -> Tuple[List[DuelResult], List[RatingResult]]:
        """Run a single tournament round"""
        round_name = self._create_round_name(len(participants))
        matches = []
        survivors = []
        
        # Display round header
        print(f"\n{'='*70}")
        print(f"ROUND {round_number}: {round_name}")
        print(f"{'='*70}")
        print(f"Participants: {len(participants)}")
        
        # Handle bye if odd number
        bye_recipient = None
        active_participants = participants.copy()
        
        if len(active_participants) % 2 == 1:
            bye_recipient, active_participants = self._select_bye_recipient(
                active_participants, self.bye_tracker, round_number
            )
            survivors.append(bye_recipient)
            
            # Display bye
            print(f"\n🎫 BYE: Joke {bye_recipient.joke_id} (Seed {bye_recipient.original_rank}) "
                  f"- advances automatically")
            print(f"   Reason: Highest seed without recent bye")
            print(f"   Current lives: {self.lives_remaining.get(bye_recipient.joke_id, 0)}")
            
            # Create bye match record
            bye_match = DuelResult(
                match_id=f"R{round_number}_BYE",
                round_number=round_number,
                round_name=round_name,
                joke_a_id=bye_recipient.joke_id,
                joke_a_seed=bye_recipient.original_rank,
                joke_a_lives_before=self.lives_remaining.get(bye_recipient.joke_id, 0),
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
            
            # Display match header
            print(f"\n{'─'*60}")
            print(f"Match {i+1}: Joke {joke_a.joke_id} (Seed {joke_a.original_rank}, "
                  f"Lives: {self.lives_remaining.get(joke_a.joke_id, 0)}) vs "
                  f"Joke {joke_b.joke_id} (Seed {joke_b.original_rank}, "
                  f"Lives: {self.lives_remaining.get(joke_b.joke_id, 0)})")
            
            # Run duel
            match_result = await self.duel_judge.compare_jokes_for_tournament(
                joke_a, joke_b,
                match_id=f"R{round_number}_M{i+1}",
                round_number=round_number,
                round_name=round_name,
                lives_tracker=self.lives_remaining
            )
            
            # Display match details
            self._display_match_result(match_result, joke_a, joke_b)
            
            matches.append(match_result)
            
            # Process match result and update lives
            advancing_jokes = self._process_match_result(match_result)
            for joke_id in advancing_jokes:
                survivor = next(j for j in [joke_a, joke_b] if j.joke_id == joke_id)
                survivors.append(survivor)
        
        return matches, survivors
    
    def _display_match_result(self, match: DuelResult, joke_a: RatingResult, joke_b: RatingResult):
        """Display detailed match result"""
        # Show evaluation details with joke IDs
        print(f"  > Evaluating A→B... confidence: {match.ab_confidence:.2f} "
            f"(winner: Joke {match.ab_winner_id})")
        print(f"  > Evaluating B→A... confidence: {match.ba_confidence:.2f} "
            f"(winner: Joke {match.ba_winner_id})")
        
        # Show decision type
        if match.decision_type == "consistent":
            print(f"  ✓ CONSISTENT: Both directions agree on Joke {match.winner_id}")
        elif match.decision_type == "by_confidence":
            print(f"  ⚠️  INCONSISTENT: Using higher confidence result")
        elif match.decision_type == "by_rating":
            joke_a_rating = joke_a.overall_rating
            joke_b_rating = joke_b.overall_rating
            print(f"  ⚖️  TIE: Using original ratings (A: {joke_a_rating:.2f}, B: {joke_b_rating:.2f})")
        
        # Show winner
        winner_joke = joke_a if match.winner_id == joke_a.joke_id else joke_b
        loser_joke = joke_b if match.winner_id == joke_a.joke_id else joke_a
        
        print(f"  🏆 Winner: Joke {winner_joke.joke_id} (confidence: {match.confidence_factor:.2f})")
        
        # Show loser status
        if match.loser_advanced_by_life:
            remaining_lives = self.lives_remaining.get(loser_joke.joke_id, 0)
            print(f"  💚 Loser: Joke {loser_joke.joke_id} advances using 1 life "
                f"({remaining_lives} {'lives' if remaining_lives != 1 else 'life'} remaining)")
        else:
            print(f"  💔 Loser: Joke {loser_joke.joke_id} eliminated (no lives remaining)")
    
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
    
    def _process_match_result(self, match: DuelResult) -> List[int]:
        """Determine who advances from a match and update lives"""
        advancing = [match.winner_id]
        
        # Determine loser
        loser_id = match.joke_b_id if match.winner_id == match.joke_a_id else match.joke_a_id
        
        if loser_id != -1:  # Not a bye
            # Check if loser has lives
            if self.lives_remaining.get(loser_id, 0) > 0:
                # Decrease life and advance
                self.lives_remaining[loser_id] -= 1
                self.total_lives_used += 1
                advancing.append(loser_id)
                # Update the match record to reflect life usage
                match.loser_advanced_by_life = True
        
        return advancing
    
    def _display_round_summary(self, round_number: int, round_matches: List[DuelResult], 
                             survivors: List[RatingResult]):
        """Display summary after round completion"""
        print(f"\n{'─'*70}")
        print(f"Round {round_number} Summary:")
        print(f"  - Matches played: {len([m for m in round_matches if m.joke_b_id != -1])}")
        print(f"  - Byes given: {len([m for m in round_matches if m.joke_b_id == -1])}")
        
        lives_used_this_round = sum(1 for m in round_matches if m.loser_advanced_by_life)
        print(f"  - Lives used this round: {lives_used_this_round}")
        print(f"  - Jokes advancing: {len(survivors)}")
        
        # Show remaining lives distribution
        lives_dist = {}
        for survivor in survivors:
            lives = self.lives_remaining.get(survivor.joke_id, 0)
            lives_dist[lives] = lives_dist.get(lives, 0) + 1
        
        print(f"  - Lives distribution: ", end="")
        for lives in sorted(lives_dist.keys(), reverse=True):
            print(f"{lives} {'lives' if lives != 1 else 'life'}: {lives_dist[lives]} jokes, ", end="")
        print()  # New line
        print(f"{'─'*70}")
    
    def _create_round_name(self, participants_count: int) -> str:
        """Create appropriate round name"""
        if participants_count == 2:
            return "Final"
        elif participants_count == 3:
            return "Semi-Final (with bye)"
        elif participants_count == 4:
            return "Semi-Final"
        elif participants_count <= 8:
            return "Quarter-Final"
        else:
            return f"Round of {participants_count}"
    
    def _calculate_final_rankings(self, original_jokes: List[RatingResult], 
                                all_matches: List[DuelResult]) -> List[Tuple[RatingResult, int, int]]:
        """Calculate final tournament rankings"""
        # Track elimination round for each joke
        elimination_round = {}
        max_round = max(m.round_number for m in all_matches) if all_matches else 0
        
        for joke in original_jokes:
            # Find when joke was eliminated
            eliminated = False
            for match in all_matches:
                if match.joke_b_id == -1:  # Skip bye matches
                    continue
                
                # Check if this joke lost and didn't advance
                if match.winner_id != joke.joke_id and (match.joke_a_id == joke.joke_id or match.joke_b_id == joke.joke_id):
                    if not match.loser_advanced_by_life:
                        elimination_round[joke.joke_id] = match.round_number
                        eliminated = True
                        break
            
            # If not eliminated, joke made it to the end
            if not eliminated:
                elimination_round[joke.joke_id] = max_round + 1
        
        # Sort by elimination round (later = better) and original rank as tiebreaker
        sorted_jokes = sorted(original_jokes, 
                            key=lambda x: (-elimination_round.get(x.joke_id, 0), x.original_rank))
        
        # Assign tournament ranks
        rankings = []
        for i, joke in enumerate(sorted_jokes):
            lives_remaining = self.lives_remaining.get(joke.joke_id, 0)
            rankings.append((joke, i + 1, lives_remaining))
        
        return rankings