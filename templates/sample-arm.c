#include <stdlib.h>

__asm__(
    ".globl main\n"
    "main:\n"
    {0}
    "__main_end:\n"
      "bx lr");
