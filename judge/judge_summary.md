## Rating Judge Pipeline Summary

**Stage 1: Admissibility Assessment**
Liberal evaluation that checks if the input is an intended, complete, appropriate, coherent, and accessible joke - errs on the side of inclusion rather than rejection.

**Stage 2: Category Classification**
Categorizes jokes using predefined categories from XML, or routes to dynamic factor generation if no standard categories apply.

**Stage 3: Factor Identification**
Identifies relevant evaluation factors from XML database for categorized jokes, or generates custom factors for unique humor types.

**Stage 4: Factor Scoring (Convergence Point)**
Scores all relevant factors on a 0-5 scale and calculates final ratings (max score, mean score, individual factor scores).

---

## Duel Judge Pipeline Summary

**Stage 1: Parallel Comparison**
Performs bias-mitigated pairwise comparison by evaluating Joke A vs B and Joke B vs A simultaneously in parallel positions.

**Stage 2: Result Combination**
Checks consistency between parallel comparisons, resolves conflicts if needed, and outputs final decision with confidence factor (1.0-10.0+ scale).