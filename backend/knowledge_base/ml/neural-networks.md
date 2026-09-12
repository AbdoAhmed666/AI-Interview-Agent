# Neural networks

## Fundamentals

A neural network is layers of weighted sums followed by non-linear activations
(ReLU, sigmoid, tanh). Training minimizes a loss function with gradient descent;
backpropagation computes gradients via the chain rule.

## Architectures

CNNs (convolutional neural networks) share weights through convolutional filters
and are strong on images and spatial data. RNNs and LSTMs process sequences and
carry state across time steps; LSTMs use gates to mitigate vanishing gradients.

## Regularization and overfitting

Overfitting is low training error but high validation error. Common remedies are
dropout, weight decay (L2), early stopping, data augmentation, and simpler
models. Batch normalization stabilizes and speeds up training.

## Optimization

Optimizers such as SGD with momentum and Adam adapt the update step. The
learning rate is the most important hyperparameter; too high diverges, too low
trains slowly. Learning-rate schedules and warmup are common in practice.
