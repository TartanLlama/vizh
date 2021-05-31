#if __has_include("libv_vizh.h")
    #include "libv_vizh.h"
#endif

#define TAPE_SIZE 4096

typedef struct {
    size_t n_tapes; 
    size_t capacity; 
    char** tapes;
} vizh_tapes_t;

void readin(char* c);
void print(char* c);

// Calls to newtape and freetape are automatically fixed up by the compiler to pass tapes
void newtape(vizh_tapes_t* tapes);
void freetape(vizh_tapes_t* tapes);




