# Migration from Metroliza

This package extracts the statistical analysis engine from Metroliza concepts without creating a runtime dependency on Metroliza.

## What moved

The reusable parts are the analysis primitives and orchestration:

- group preprocessing
- normality and variance checks
- test selection
- pairwise comparison logic
- correction methods
- effect sizes
- confidence intervals
- spec comparability policy
- diagnostics and summary generation

Those behaviors now live in `hexafe_groupstats` and return typed result models.

## What did not move

Metroliza-specific concerns stay out of the library core:

- workbook generation
- export layout
- chart creation
- UI state and PyQt coupling
- parser orchestration
- Google API integration
- local-path assumptions

Those are application concerns. They can consume the library, but the library does not depend on them.

## No runtime dependency on Metroliza

The new package does not import Metroliza modules at runtime.
That matters for three reasons:

1. the library can be installed and used independently
2. notebooks and Colab can use it without a local Metroliza checkout
3. future analysis tools can depend on it without pulling in UI/export code

## How integration works now

Use the public API for direct analysis:

- `analyze_metric(...)`
- `compare_groups(...)`
- `analyze_dataframe(...)`

Use the adapter layer when Metroliza-style payloads or row dicts are needed:

- `hexafe_groupstats.adapters.metroliza.analyze_metroliza_payload(...)`
- `hexafe_groupstats.adapters.metroliza.to_metroliza_rows(...)`

This keeps the Metroliza mapping isolated from the engine.

## Behavioral compatibility goals

The current implementation preserves the important analysis behaviors:

- numeric coercion and NaN dropping
- Shapiro-based normality handling
- variance-sensitive path selection
- 2-group tests: Student t-test, Welch t-test, Mann-Whitney U
- 3+ group tests: ANOVA, Welch ANOVA, Kruskal-Wallis
- Holm and Benjamini-Hochberg correction
- pairwise effect sizes
- bootstrap confidence intervals when enabled
- spec policy statuses and the pairwise/capability rules attached to them

The library is intentionally close to Metroliza behavior, but it is structured as a clean engine rather than a copied application layer.

