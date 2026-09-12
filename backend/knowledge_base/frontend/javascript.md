# JavaScript and TypeScript

## The event loop

JavaScript is single-threaded and uses an event loop. Synchronous code runs on
the call stack; asynchronous callbacks wait in task queues. Microtasks (promise
callbacks) run before macrotasks (timers) after each tick.

## Closures and scope

A closure is a function bundled with the lexical scope it was created in, so it
can read and update outer variables after the outer function returns. `let` and
`const` are block-scoped; `var` is function-scoped and hoisted.

## Asynchronous patterns

Promises represent a future value with `then`/`catch`. `async/await` is
syntactic sugar over promises and makes asynchronous code read sequentially.
Unhandled promise rejections should always be caught.

## TypeScript

TypeScript adds static types on top of JavaScript. Interfaces and types describe
object shapes; generics let functions and components work over many types while
staying type-safe. Union and narrowing let the compiler prove which branch runs.
Types are erased at build time and do not exist at runtime.
