# Pandas and data wrangling

## Core structures

A Series is a labeled 1D array; a DataFrame is a labeled 2D table. Vectorized
operations over columns are far faster than Python loops over rows.

## Cleaning data

Handle missing values with `dropna` or `fillna`, and understand whether data is
missing at random. Fix dtypes early. Remove or cap outliers deliberately, not by
accident. Deduplicate with `drop_duplicates`.

## Reshaping and aggregation

`groupby` splits data, applies an aggregation, and combines the result.
`merge`/`join` combine tables on keys; know the difference between inner, left,
right, and outer joins. `pivot_table` reshapes long data into wide summaries.

## Performance

Prefer vectorized NumPy/pandas operations over `apply` with Python functions.
Use appropriate dtypes (categoricals for low-cardinality strings) to save
memory. Chunked reading handles files larger than memory.
