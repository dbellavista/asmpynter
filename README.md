# ASMPYNTER a Python Assembly Interpreter

This utility aims to provide a simple console base interpreter for assembly
commands.

Ever want to check what an istruction does to register or flags? Asmpynter
provides a quick way to find it out!

## Requirements

 * Linux
 * python 2.7
 * gcc, gdb
 * readline

For arm:

 * qemu-arm
 * gdb and gcc arm-linux-gnueabi

## How does it work

Toolchains are defined via the configuration file. Essentially you must provide:

1. A template for the code. The assembly will be inserted in the specified position.
2. The compiler
2. The debugger to use (only GDB supported)
3. Optionally a QEMU to execute the compiled file (remote debugging).
4. Configuration stuff, like library path and how to parse the 'flags' register.

GDB inserts a breakpoint at the end of the main function and read the register
information. Of course if you code skips the breakpoint, the system wont work!
