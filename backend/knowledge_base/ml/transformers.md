# Transformers

## Attention

The transformer architecture replaces recurrence with self-attention. Each token
attends to every other token, weighting them by learned query-key similarity, so
long-range dependencies are captured directly. Multi-head attention lets the
model attend to different relationships in parallel.

## Structure

A transformer block is multi-head self-attention followed by a feed-forward
network, each wrapped with residual connections and layer normalization.
Positional encodings inject word order, which attention alone does not model.

## Pretraining and fine-tuning

Large models are pretrained on huge corpora with objectives like masked or
next-token prediction, then fine-tuned on downstream tasks. Transfer learning
from a pretrained backbone usually beats training from scratch.

## Practical concerns

Attention is quadratic in sequence length, which limits context size and drives
techniques like efficient attention and retrieval augmentation. Tokenization
choices affect how text is split before it reaches the model.
