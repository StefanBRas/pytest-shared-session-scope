# Changelog

## [Unreleased]

## [0.5.0]
- Add `shared_session_scope_pickle` that uses `pickle` for de/serialization.
Make fixture that does cleanup also save missing test (which is then an empty set). Should make no runtime in supported use cases.
- Make fixture that does cleanup also save missing test (which is then an empty set). Should make no runtime in supported use cases.

## [0.4.0]
- Changed `CleanupToken` to be just `Enum` instead of `str, Enum`.
- BREAKING: The first yield now returns a `SetupToken` instead of `None` to signal that a worker should calculate the value.

## [0.3.0]
- BREAKING: Rename `shared_json_session_scope` to `shared_session_scope_json`

## [0.2.1]
- Remove fancy generic typing.
- Renamed generic `_T` to `_StoreType`.

## [0.2.0]

- Add `parse` argument to allow for parsing data before returning it to the test.

## [0.1.0]
- Initial release
