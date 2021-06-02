#if __has_include("libv_vizh.h")
    #include "libv_vizh.h"
#endif
#include <stdint.h>

#define TAPE_SIZE 4096

typedef struct {
    size_t n_tapes; 
    size_t capacity; 
    uint8_t** tapes;
    uint8_t** to_free;
} vizh_tapes_t;

void readin(uint8_t* c);
void print(uint8_t* c);

// Calls to newtape and freetape are automatically fixed up by the compiler to pass tapes
void newtape(vizh_tapes_t* tapes);
void freetape(vizh_tapes_t* tapes);




