import os
import xml.etree.ElementTree as ET
from xml.dom import minidom
from typing import List, Dict, Optional, Tuple, Union
from datetime import datetime
from pathlib import Path

from generator.models import FirstOrderTriplet, HigherOrderGroup
from judges.models import (
    RatingResult, TournamentResult, DuelResult, 
    AdmissibilityResults
)
from utilities.generator_utils import ensure_directory_exists

class XMLLogger:
    def __init__(self, output_dir: str):
        """Initialize with dynamic output directory"""
        self.output_dir = Path(output_dir)
        self._create_output_dir()
    
    def log_rating_results(self, results: List[RatingResult], filename: str = "rating_results.xml"):
        """Log all jokes with detailed admissibility breakdown"""
        root = ET.Element("rating_results")
        root.set("timestamp", self._format_timestamp())
        root.set("total_jokes", str(len(results)))
        
        for result in results:
            joke_elem = ET.SubElement(root, "joke")
            joke_elem.set("id", str(result.joke_id))
            
            # Joke text
            text_elem = ET.SubElement(joke_elem, "text")
            text_elem.text = result.joke_text
            
            # Admissibility results
            admiss_elem = ET.SubElement(joke_elem, "admissibility")
            admiss_elem.set("overall", str(result.admissibility_results.is_admissible))
            
            # Individual checks
            for check_name, check_result in [
                ("intent", result.admissibility_results.intent_check),
                ("completeness", result.admissibility_results.completeness_check),
                ("appropriateness", result.admissibility_results.appropriateness_check),
                ("coherence", result.admissibility_results.coherence_check),
                ("accessibility", result.admissibility_results.accessibility_check)
            ]:
                check_elem = ET.SubElement(admiss_elem, check_name)
                check_elem.set("passed", str(check_result))
            
            # Categories
            categories_elem = ET.SubElement(joke_elem, "categories")
            for category in result.assigned_categories:
                cat_elem = ET.SubElement(categories_elem, "category")
                cat_elem.text = category
            
            # Dropped categories
            if result.dropped_categories:
                dropped_elem = ET.SubElement(joke_elem, "dropped_categories")
                for category in result.dropped_categories:
                    cat_elem = ET.SubElement(dropped_elem, "category")
                    cat_elem.text = category
            
            # Factors
            factors_elem = ET.SubElement(joke_elem, "factors")
            for factor in result.relevant_factors:
                factor_elem = ET.SubElement(factors_elem, "factor")
                factor_elem.set("name", factor)
                factor_elem.set("score", str(result.factor_scores.get(factor, 0)))
            
            # Scores
            scores_elem = ET.SubElement(joke_elem, "scores")
            scores_elem.set("max_score", str(result.max_score))
            scores_elem.set("mean_score", f"{result.mean_score:.2f}")
            scores_elem.set("overall_rating", f"{result.overall_rating:.2f}")
            
            if result.original_rank:
                joke_elem.set("rank", str(result.original_rank))
        
        self._write_xml(root, filename)
    
    def log_top_jokes(self, top_jokes: List[RatingResult], filename: str = "top_jokes_for_duel.xml"):
        """Log top N jokes selected for tournament"""
        root = ET.Element("top_jokes")
        root.set("timestamp", self._format_timestamp())
        root.set("count", str(len(top_jokes)))
        
        for joke in top_jokes:
            joke_elem = ET.SubElement(root, "joke")
            joke_elem.set("id", str(joke.joke_id))
            joke_elem.set("rank", str(joke.original_rank))
            joke_elem.set("overall_rating", f"{joke.overall_rating:.2f}")
            
            text_elem = ET.SubElement(joke_elem, "text")
            text_elem.text = joke.joke_text
            
            # Include categories and top factors
            categories_elem = ET.SubElement(joke_elem, "categories")
            for category in joke.assigned_categories:
                cat_elem = ET.SubElement(categories_elem, "category")
                cat_elem.text = category
        
        self._write_xml(root, filename)
    
    def log_tournament_results(self, tournament_result: TournamentResult, 
                             filename: str = "tournament_results.xml"):
        """Log final tournament winner with complete details"""
        root = ET.Element("tournament_results")
        root.set("timestamp", self._format_timestamp())
        root.set("total_participants", str(tournament_result.top_count_used))
        root.set("tournament_rounds", str(tournament_result.tournament_rounds))
        
        # Winner
        winner_elem = ET.SubElement(root, "winner")
        winner_elem.set("id", str(tournament_result.winner_joke.joke_id))
        winner_elem.set("original_rank", str(tournament_result.winner_joke.original_rank))
        
        text_elem = ET.SubElement(winner_elem, "text")
        text_elem.text = tournament_result.winner_joke.joke_text
        
        # Lives tracking for winner
        winner_id = tournament_result.winner_joke.joke_id
        if winner_id in tournament_result.lives_tracking:
            lives_info = tournament_result.lives_tracking[winner_id]
            lives_elem = ET.SubElement(winner_elem, "lives")
            lives_elem.set("initial", str(lives_info[0]))
            lives_elem.set("used", str(lives_info[1]))
            lives_elem.set("remaining", str(lives_info[2]))
        
        # Bye rounds for winner
        if winner_id in tournament_result.bye_tracking:
            bye_rounds = tournament_result.bye_tracking[winner_id]
            if bye_rounds:
                bye_elem = ET.SubElement(winner_elem, "bye_rounds")
                bye_elem.text = ",".join(map(str, bye_rounds))
        
        # Final rankings
        rankings_elem = ET.SubElement(root, "final_rankings")
        for joke, tournament_rank, lives_remaining in tournament_result.final_rankings:
            rank_elem = ET.SubElement(rankings_elem, "joke")
            rank_elem.set("id", str(joke.joke_id))
            rank_elem.set("tournament_rank", str(tournament_rank))
            rank_elem.set("original_rank", str(joke.original_rank))
            rank_elem.set("lives_remaining", str(lives_remaining))
            
            # Lives info
            if joke.joke_id in tournament_result.lives_tracking:
                lives_info = tournament_result.lives_tracking[joke.joke_id]
                rank_elem.set("lives_used", str(lives_info[1]))
            
            # Bye info
            if joke.joke_id in tournament_result.bye_tracking:
                bye_rounds = tournament_result.bye_tracking[joke.joke_id]
                if bye_rounds:
                    rank_elem.set("bye_rounds", ",".join(map(str, bye_rounds)))
        
        self._write_xml(root, filename)
    
    def log_duel_matches(self, all_matches: List[DuelResult], filename: str = "duel_matches.xml"):
        """Log all tournament matches organized by rounds"""
        root = ET.Element("duel_matches")
        root.set("timestamp", self._format_timestamp())
        root.set("total_matches", str(len(all_matches)))
        
        # Group matches by round
        matches_by_round = {}
        for match in all_matches:
            if match.round_number not in matches_by_round:
                matches_by_round[match.round_number] = []
            matches_by_round[match.round_number].append(match)
        
        # Sort rounds (lowest first)
        for round_num in sorted(matches_by_round.keys()):
            round_elem = ET.SubElement(root, "round")
            round_elem.set("number", str(round_num))
            round_elem.set("name", matches_by_round[round_num][0].round_name)
            
            for match in matches_by_round[round_num]:
                # Check if this was a bye match
                if match.joke_b_id == -1:  # Bye indicator
                    bye_elem = ET.SubElement(round_elem, "bye_recipient")
                    bye_elem.set("joke_id", str(match.joke_a_id))
                    bye_elem.set("reason", "top_rated_no_consecutive_bye")
                else:
                    match_elem = ET.SubElement(round_elem, "match")
                    match_elem.set("id", match.match_id)
                    
                    # Joke A
                    joke_a_elem = ET.SubElement(match_elem, "joke_a")
                    joke_a_elem.set("id", str(match.joke_a_id))
                    joke_a_elem.set("seed", str(match.joke_a_seed))
                    joke_a_elem.set("lives_before", str(match.joke_a_lives_before))
                    
                    # Joke B
                    joke_b_elem = ET.SubElement(match_elem, "joke_b")
                    joke_b_elem.set("id", str(match.joke_b_id))
                    joke_b_elem.set("seed", str(match.joke_b_seed))
                    joke_b_elem.set("lives_before", str(match.joke_b_lives_before))
                    
                    # Result
                    winner_elem = ET.SubElement(match_elem, "winner")
                    winner_elem.set("id", str(match.winner_id))
                    
                    # Lives after
                    if match.loser_advanced_by_life:
                        loser_id = match.joke_b_id if match.winner_id == match.joke_a_id else match.joke_a_id
                        lives_elem = ET.SubElement(match_elem, "loser_advanced")
                        lives_elem.set("id", str(loser_id))
                        lives_elem.set("used_life", "true")
                    
                    # Confidence and reasoning
                    conf_elem = ET.SubElement(match_elem, "confidence_factor")
                    conf_elem.text = f"{match.confidence_factor:.2f}"
                    
                    pos_elem = ET.SubElement(match_elem, "position_consistent")
                    pos_elem.text = str(match.position_consistent)
                    
                    reason_elem = ET.SubElement(match_elem, "reasoning")
                    reason_elem.text = match.reasoning
        
        self._write_xml(root, filename)
    
    def log_first_order_contexts(self, contexts: List[FirstOrderTriplet], output_dir: str = None) -> None:
        """Log hook-template-context combinations"""
        root = ET.Element("first_order_contexts")
        root.set("timestamp", self._format_timestamp())
        root.set("total_contexts", str(len(contexts)))
        
        for i, ctx in enumerate(contexts):
            context_elem = ET.SubElement(root, "context")
            context_elem.set("id", str(i + 1))
            
            hook_elem = ET.SubElement(context_elem, "hook")
            hook_elem.text = ctx.hook
            
            template_elem = ET.SubElement(context_elem, "template")
            template_elem.text = ctx.template
            
            explanation_elem = ET.SubElement(context_elem, "explanation")
            explanation_elem.text = ctx.explanation
        
        self._write_xml(root, "first_order_contexts.xml")
        print(f"First-order contexts logged to: {self.output_dir}/first_order_contexts.xml")

    def log_higher_order_groups(self, groups: List[HigherOrderGroup], output_dir: str = None) -> None:
        """Log higher-order groups"""
        root = ET.Element("higher_order_groups")
        root.set("timestamp", self._format_timestamp())
        root.set("total_groups", str(len(groups)))
        
        for i, group in enumerate(groups):
            group_elem = ET.SubElement(root, "group")
            group_elem.set("id", str(i + 1))
            group_elem.set("member_count", str(len(group.hook_template_pairs)))
            
            # List member contexts
            members_elem = ET.SubElement(group_elem, "members")
            for j, pair in enumerate(group.hook_template_pairs):
                member_elem = ET.SubElement(members_elem, "member")
                member_elem.set("index", str(j + 1))
                
                hook_elem = ET.SubElement(member_elem, "hook")
                hook_elem.text = pair.hook
                
                template_elem = ET.SubElement(member_elem, "template")
                template_elem.text = pair.template
            
            # Group explanation
            explanation_elem = ET.SubElement(group_elem, "group_explanation")
            explanation_elem.text = group.context_explanation
        
        self._write_xml(root, "higher_order_groups.xml")
        print(f"Higher-order groups logged to: {self.output_dir}/higher_order_groups.xml")

    def _create_output_dir(self):
        """Ensure output directory exists"""
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def _format_timestamp(self) -> str:
        """Generate YYYY-MM-DD HH:MM:SS format"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def _write_xml(self, root: ET.Element, filename: str):
        """Write XML with proper formatting"""
        # Convert to string with minidom for pretty printing
        rough_string = ET.tostring(root, encoding='unicode')
        reparsed = minidom.parseString(rough_string)
        
        # Pretty print with 4-space indentation
        pretty_xml = reparsed.toprettyxml(indent="    ")
        
        # Remove extra blank lines
        lines = pretty_xml.split('\n')
        lines = [line for line in lines if line.strip()]
        pretty_xml = '\n'.join(lines[1:])  # Skip XML declaration from minidom
        
        # Add our own XML declaration
        final_xml = '<?xml version="1.0" encoding="UTF-8"?>\n' + pretty_xml
        
        # Write to file
        filepath = self.output_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(final_xml)
    
