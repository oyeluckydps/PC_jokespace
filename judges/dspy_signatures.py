import dspy

class CombinedAdmissibilitySignature(dspy.Signature):
    """Comprehensive admissibility check for joke content with bias mitigation"""
    evaluation_criteria = dspy.InputField(desc="All five liberal evaluation criteria with detailed instructions")
    bias_mitigation_guidelines = dspy.InputField(desc="Specific bias mitigation measures and warnings")
    examples = dspy.InputField(desc="Examples of jokes that pass and fail each criterion")
    joke_text = dspy.InputField(desc="The joke text to evaluate")
    
    # Individual binary outputs for each criterion
    intent_passed = dspy.OutputField(desc="Boolean indicating if joke has comedic intent")
    completeness_passed = dspy.OutputField(desc="Boolean indicating if joke is complete")
    appropriateness_passed = dspy.OutputField(desc="Boolean indicating if joke is appropriate")
    coherence_passed = dspy.OutputField(desc="Boolean indicating if joke is coherent")
    accessibility_passed = dspy.OutputField(desc="Boolean indicating if joke is accessible")

class CategoryAssignmentSignature(dspy.Signature):
    """Assign joke to relevant categories"""
    joke_text = dspy.InputField(desc="The joke text to categorize")
    all_categories = dspy.InputField(desc="Full list of available category names")
    categories = dspy.OutputField(desc="List of relevant category names, or empty list if none fit")
    is_independent = dspy.OutputField(desc="true if no existing categories fit well, false otherwise")
    reasoning = dspy.OutputField(desc="Explanation for category assignments")

class FactorSelectionSignature(dspy.Signature):
    """Select relevant factors for a category"""
    joke_text = dspy.InputField(desc="The joke text to evaluate")
    category = dspy.InputField(desc="Category name to consider")
    available_factors = dspy.InputField(desc="List of factors for this category with descriptions")
    relevant_factors = dspy.OutputField(desc="List of relevant factor names from available factors")
    reasoning = dspy.OutputField(desc="Explanation for factor selection")

class FactorScoringSignature(dspy.Signature):
    """Score joke on specific factor"""
    joke_text = dspy.InputField(desc="The joke text to score")
    factor_name = dspy.InputField(desc="Name of the factor being evaluated")
    factor_description = dspy.InputField(desc="Detailed description of what this factor measures")
    positive_examples = dspy.InputField(desc="Examples of jokes that score well on this factor")
    negative_examples = dspy.InputField(desc="Examples of jokes that score poorly on this factor")
    score = dspy.OutputField(desc="Integer score from 0 to 5")
    reasoning = dspy.OutputField(desc="Explanation for the score")

class DuelComparisonSignature(dspy.Signature):
    """Compare two jokes with examples"""
    joke_a = dspy.InputField(desc="First joke text")
    joke_b = dspy.InputField(desc="Second joke text")
    good_examples = dspy.InputField(desc="Examples of good jokes for reference")
    bad_examples = dspy.InputField(desc="Examples of bad jokes for reference")
    winner = dspy.OutputField(desc="Either 'joke_a' or 'joke_b'")
    confidence_factor = dspy.OutputField(desc="Float >= 1.0 indicating confidence in decision")
    reasoning = dspy.OutputField(desc="Detailed explanation for the choice")

    