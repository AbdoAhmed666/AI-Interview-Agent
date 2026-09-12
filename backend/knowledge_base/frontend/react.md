# React

React is a component-based library for building user interfaces.

## Components and props

A component is a function that returns JSX. Props are read-only inputs passed
from a parent to a child. A component must never mutate its own props.

## State and hooks

`useState` holds local state that triggers a re-render when updated.
`useEffect` runs side effects after render and can clean up on unmount or when
its dependency array changes. `useMemo` and `useCallback` memoize expensive
values and stable function identities. `useRef` holds a mutable value that does
not trigger re-renders.

## Rendering and reconciliation

React builds a virtual DOM and diffs it against the previous tree to compute the
minimal set of real DOM updates. Stable `key` props on list items let React
match elements across renders and avoid unnecessary remounts.

## Common pitfalls

Stale closures capture old state inside effects and callbacks. Missing
dependencies in `useEffect` cause bugs. Deriving state that could be computed
during render leads to duplicated sources of truth. Lifting state up is the
usual fix for sharing data between siblings.
