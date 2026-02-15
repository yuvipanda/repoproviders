# Usage

`repoproviders` is primarily designed to be used as an async library.
There are two functions that offer the core functionality - `resolve`
and `fetch`

## `resolve`

`resolve` takes a URL, and tries to determine what kind of repository
it is.

## `fetch`

`fetch` takes a URL, resolves it using `resolve`, and then fetches
the contents of that repository to a path in the filesystem.
