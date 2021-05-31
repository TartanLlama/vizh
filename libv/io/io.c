#include <stdio.h>
#include <stdint.h>
void readin(uint8_t* c) {
    *c = getchar();
}

void print(uint8_t* c) {
    putchar(*c);
}