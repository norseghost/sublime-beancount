sublime-beancount
=================

Bits and pieces to facilitate accounting with [Beancount](http://furius.ca/beancount/) using Sublime Text.

Currently, just a syntax definition and a build system.

The build system runs "bean-check" on the current file, and  works with "Build system: Automatic", and line navigation works.

## Contributing

To make changes to the syntax highlighting, edit `beancount.YAML-tmLanguage`. [PackageDev][1] provides a build system to convert the YAML file to XML plist. With PackageDev installed, press Ctrl+B (or Command+B on macOS) to perform the conversion.

[1]:https://packagecontrol.io/packages/PackageDev
