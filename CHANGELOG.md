# Changelog

## [Unreleased]

## [0.4.0] - 2020-05-26

### Added

-   Allow setting pre-defined secret_id.

### Fixed

-   Fix `secret_id` not being returned by the module in certain cases.

## [0.3.0] - 2020-01-24

### Added

-   Add ability to create tokens with a specific accessor ID.

### Changed

-   Extract common API code into a module utility.

### Fixed

-   Fix adding policies to bare tokens.

## [0.2.0] - 2019-02-24

### Changed

-   Improve error handling for API request errors.

### Fixed

-   Remove duplicate key in documentation.
-   Fix token comparison with no current policies.

## [0.1.0] - 2019-02-18

### Added

-   Repository documentation.

### Fixed

-   Fix documentation in modules.

## 0.0.1 - 2019-02-17

### Added

-   `consul_acl_policy` module.
-   `consul_acl_token` module.

[unreleased]: https://github.com/jsundh/ansible-modules-consul-acl/compare/0.4.0...HEAD
[0.4.0]: https://github.com/jsundh/ansible-modules-consul-acl/compare/0.3.0...0.4.0
[0.3.0]: https://github.com/jsundh/ansible-modules-consul-acl/compare/0.2.0...0.3.0
[0.2.0]: https://github.com/jsundh/ansible-modules-consul-acl/compare/0.1.0...0.2.0
[0.1.0]: https://github.com/jsundh/ansible-modules-consul-acl/compare/0.0.1...0.1.0
