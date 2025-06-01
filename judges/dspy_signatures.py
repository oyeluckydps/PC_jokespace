import dspy
from typing import List
from judges.models import CategoryFactor, FactorData

class AdmissibilitySignature(dspy.Signature):
    """Check if text is admissible as a joke"""
    joke_text = dspy.InputField(desc="The joke text to evaluate")
    check_type = dspy.InputField(desc="Type of admissibility check: intent/completeness/appropriateness/coherence/accessibility")
    instruction_prompt = dspy.InputField(desc="Liberal evaluation instructions for this check")
    
    reasoning = dspy.OutputField(desc="Brief explanation for the decision")
    passed = dspy.OutputField(desc="true or false")

class CategoryAssignmentSignature(dspy.Signature):
    """Assign joke to relevant categories based on analysis of joke content against available category definitions"""
    joke_text = dspy.InputField(desc="The joke text to categorize")
    available_categories = dspy.InputField(desc="List of CategoryInfo objects containing name, description, and examples for all available categories")
    instruction = dspy.InputField(desc="Detailed instructions for categorization analysis and bias avoidance")
    
    reasoning = dspy.OutputField(desc="Analysis of which categories the joke should fit into and why")
    selected_categories = dspy.OutputField(desc="List of applicable category names only (do not include descriptions or examples)")
    is_independent = dspy.OutputField(desc="true if no existing categories fit well, false otherwise")

class FactorSelectionSignature(dspy.Signature):
    """Select relevant factors from randomized categories for joke evaluation with enhanced bias mitigation"""
    joke_text = dspy.InputField(desc="The joke text to evaluate")
    relevant_categories = dspy.InputField(desc="List[CategoryFactor] - Randomized categories with their associated factor descriptions (name and description only) to prevent position bias")
    instruction = dspy.InputField(desc="Comprehensive instructions for factor selection with explicit bias mitigation guidelines and validation questions")
    
    reasoning = dspy.OutputField(desc="Detailed explanation for factor selection including validation against bias mitigation criteria")
    relevant_factors = dspy.OutputField(desc="List of relevant factor names chosen from the factors that would be application to rate a the joke. Please select one or more options.")

class FactorScoringSignature(dspy.Signature):
    """Score joke on specific factor"""
    joke_text = dspy.InputField(desc="The joke text to score")
    factor_data = dspy.InputField(desc="FactorData object containing factor name, description, positive examples, and negative examples")
    instruction = dspy.InputField(desc="Detailed instructions for objective factor-based scoring with bias mitigation guidelines")
    
    reasoning = dspy.OutputField(desc="Explanation for the score")
    score = dspy.OutputField(desc="Integer score from 0 to 5")

class DuelComparisonSignature(dspy.Signature):
    """Compare two jokes to determine which is funnier with bias mitigation"""
    joke_a = dspy.InputField(desc="First joke text")
    joke_b = dspy.InputField(desc="Second joke text")
    good_examples = dspy.InputField(desc="Examples of good jokes for reference")
    bad_examples = dspy.InputField(desc="Examples of bad jokes for reference")
    instruction = dspy.InputField(desc="Comprehensive instructions for bias-free humor evaluation and comparison")
    
    winner = dspy.OutputField(desc="Either 'joke_a' or 'joke_b'")
    confidence_level = dspy.OutputField(desc="Float between 1.0 and 5.0 representing confidence in the decision. Use descriptive ranges: 1.0-2.0=Tie/Equal, 2.0-3.0=Slightly funnier, 3.0-4.0=Moderately funnier, 4.0-5.0=Significantly funnier")