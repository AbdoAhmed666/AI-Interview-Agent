# Feature engineering

## Why it matters

Good features often matter more than model choice. Feature engineering turns raw
data into signals a model can learn from.

## Encoding categorical variables

One-hot encoding suits low-cardinality categories; target or frequency encoding
suits high-cardinality ones. Never fit an encoder on the test set — fit on train
and transform the rest to avoid leakage.

## Scaling and transforms

Standardization (zero mean, unit variance) and min-max scaling help
distance-based and gradient-based models. Log transforms tame skewed
distributions. Tree-based models are largely scale-invariant.

## Selection and leakage

Remove redundant and low-variance features; use importance scores or
regularization to prune. The most common mistake is data leakage — deriving a
feature from information that would not be available at prediction time, which
inflates offline metrics and fails in production.
