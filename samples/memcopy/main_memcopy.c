#include <stdio.h>
void memcopy(char*,char*,char*);

int main() {
    char str[] = "Hello!";
    char size = sizeof(str);
    char to[sizeof(str)];
    memcopy(&size, str, to);
    puts(to);
}