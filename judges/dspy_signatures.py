import dspy

class AdmissibilitySignature(dspy.Signature):
    """Check if text is admissible as a joke"""
    joke_text = dspy.InputField(desc="The joke text to evaluate")
    check_type = dspy.InputField(desc="Type of admissibility check: intent/completeness/appropriateness/coherence/accessibility")
    instruction_prompt = dspy.InputField(desc="Liberal evaluation instructions for this check")
    passed = dspy.OutputField(desc="true or false")
    reasoning = dspy.OutputField(desc="Brief explanation for the decision")

class CategoryAssignmentSignature(dspy.Signature):
    """Assign joke to relevant categories based on analysis of joke content against available category definitions"""
    joke_text = dspy.InputField(desc="The joke text to categorize")
    available_categories = dspy.InputField(desc="List of CategoryInfo objects containing name, description, and examples for all available categories")
    instruction = dspy.InputField(desc="Detailed instructions for categorization analysis and bias avoidance")
    
    reasoning = dspy.OutputField(desc="Analysis of which categories the joke should fit into and why")
    selected_categories = dspy.OutputField(desc="List of applicable category names only (do not include descriptions or examples)")
    is_independent = dspy.OutputField(desc="true if no existing categories fit well, false otherwise")

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