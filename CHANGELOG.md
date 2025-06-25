## [2.0.1](https://github.com/jguice/penguin/compare/v2.0.0...v2.0.1) (2025-06-25)


### Bug Fixes

* reliably set Slack search sort order to 'Oldest'\n\nUses robust Playwright selectors to ensure export is chronological regardless of UI changes. ([c7e851a](https://github.com/jguice/penguin/commit/c7e851a845e7e3339e986b1a71354aaace1d0972))
* support Slack pagination with numbered page buttons ([eefe316](https://github.com/jguice/penguin/commit/eefe316c7b258932af9787d52f57b5f385dd687b))

# [2.0.0](https://github.com/jguice/penguin/compare/v1.2.0...v2.0.0) (2024-12-04)


* fix!: increase timeouts for Slack workspace and search operations ([35310d1](https://github.com/jguice/penguin/commit/35310d1def54132e19ecad6fe21a5a3d96a2c96c))


### Bug Fixes

* ignore all .txt files ([cc0c4f8](https://github.com/jguice/penguin/commit/cc0c4f829e4ba09c938313e6b8e9e1a2fc243338))


### Features

* improve message formatting with html2text ([38303c9](https://github.com/jguice/penguin/commit/38303c90c132699e2c91b6af1040093a5bc6d24a))


### BREAKING CHANGES

* Significantly increased timeouts may affect automation workflows

Increase timeouts to improve reliability:
- Workspace loading timeout: 30s -> 120s
- Post-login wait: 5s -> 10s
- Search operation timeouts: 30s -> 120s

# [1.3.0](https://github.com/jguice/penguin/compare/v1.2.0...v1.3.0) (2024-11-29)


### Bug Fixes

* ignore all .txt files ([cc0c4f8](https://github.com/jguice/penguin/commit/cc0c4f829e4ba09c938313e6b8e9e1a2fc243338))


### Features

* improve message formatting with html2text ([38303c9](https://github.com/jguice/penguin/commit/38303c90c132699e2c91b6af1040093a5bc6d24a))

# [1.2.0](https://github.com/jguice/penguin/compare/v1.1.1...v1.2.0) (2024-11-28)


### Features

* expand truncated messages and add verbose mode ([994fcca](https://github.com/jguice/penguin/commit/994fccaf615fc66e9fa50d394cb071e24f53581a))

## [1.1.1](https://github.com/jguice/penguin/compare/v1.1.0...v1.1.1) (2024-11-28)


### Bug Fixes

* update license link to point to GitHub ([6654157](https://github.com/jguice/penguin/commit/6654157c817127a4897ffef5f87a252968de8e0f))

# [1.1.0](https://github.com/jguice/penguin/compare/v1.0.0...v1.1.0) (2024-11-27)


### Features

* enhance output with rich formatting and progress tracking 🎨 ([8a770c0](https://github.com/jguice/penguin/commit/8a770c0c352ceb627a2e60b05261c68126f8fcc1))
* enhance progress display with better colors and message counts ([7cfe0da](https://github.com/jguice/penguin/commit/7cfe0da9a0f2b5589dbb32836470c2e0eeb7b7a0))
