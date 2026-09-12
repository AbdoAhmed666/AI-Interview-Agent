# Model evaluation

## Train, validation, test

Split data into training, validation, and test sets. Tune hyperparameters on
validation and report final numbers on a held-out test set. Cross-validation
gives a more robust estimate on small datasets.

## Classification metrics

Accuracy is misleading on imbalanced data. Precision is the fraction of positive
predictions that are correct; recall is the fraction of actual positives found.
F1 is their harmonic mean. ROC-AUC measures ranking quality across thresholds;
the precision-recall curve is more informative under heavy class imbalance.

## Regression metrics

MAE, MSE, and RMSE measure error magnitude; R² measures explained variance.
RMSE penalizes large errors more than MAE.

## Bias and variance

Underfitting is high bias; overfitting is high variance. The goal is the sweet
spot where both validation and training error are acceptable. Data leakage,
where information from the test set influences training, produces
over-optimistic metrics and must be avoided.
