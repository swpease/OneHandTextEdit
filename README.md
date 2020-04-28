The deployment phase unfortunately isn't completely straightforward, because I wanted some features from Python 3.8, but I am using [fbs](https://build-system.fman.io/manual/), which requires Python 3.6. Also, because I developed without `fbs`, I have some import issues.

Differences:
  - `TypedDict` needs to be curated
  - some `Mock` accessors may raise errors
  - imports need to be changed
    - deployment: `from OHTE.x` --> `from x`
    - testing:    `from OHTE.x` --> `from src.main.python.x`
  - tests of `main` do not currently work, because `main` relies on an `fbs` object (vs `QApplication`) in deployment.
