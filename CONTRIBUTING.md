# Contributing

Thank you for helping make Shatter better! :)

## Main notes

We don't have much a formal policy surrounding contributions. However, here are some helpful notes:

### Coding style

1. There is currently no naming scheme that is strictly followed for names; however, it is recommended that you use:
	* `snake_case` for function names
	* `PascalCase` for class names
	* `snake_case` for variable names
	* `CAPITAL_SNAKE_CASE` for names of things that are supposed to be constants
2. You should set your text editor to keep trailing whitespace, and all lines in a block should be indented using tab characters (though you can use spaces for alignment), including whitespace only lines.
	* Of all the rules, this is the only one that matters. Yes this is not standard python style and no I do not care.
3. Similarly, there should be spaces around `=` in function calls: `func(param1 = 0, param2 = "h")`
4. Otherwise you can actually follow the typical python advice.

## Modules

* The addon files are mainly in `addon/shatter`.
* The `main` module is the main module.
* The `__init__` is where `bl_info` is stored.
* Any configuration or non-temporary, non-output files should use `common.TOOLS_HOME_FOLDER`.
