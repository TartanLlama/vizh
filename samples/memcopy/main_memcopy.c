#include <stdio.h>
#include <stdint.h>
void memcopy(uint8_t*,uint8_t*,uint8_t*);

int main() {
    uint8_t str[] = "Hello!";
    uint8_t size = sizeof(str);
    uint8_t to[sizeof(str)];
    memcopy(&size, str, to);
    puts(to);
}