# CSS and layout

## The box model

Every element is a box made of content, padding, border, and margin.
`box-sizing: border-box` includes padding and border inside the declared width,
which makes layouts easier to reason about.

## Flexbox and grid

Flexbox lays out items in one dimension (a row or a column) and is ideal for
toolbars, navigation, and distributing space. CSS Grid lays out items in two
dimensions and is ideal for page-level and card layouts. They are complementary,
not competitors.

## Specificity and the cascade

Styles are resolved by origin, specificity, and source order. Inline styles beat
IDs, which beat classes, which beat element selectors. Overusing `!important`
signals a specificity problem.

## Responsive design

Media queries adapt layout to viewport size. Relative units (`rem`, `%`, `fr`,
`vw`) scale better than fixed pixels. A mobile-first approach starts from the
smallest layout and adds complexity at larger breakpoints. Utility frameworks
such as Tailwind CSS express these rules as composable classes.
