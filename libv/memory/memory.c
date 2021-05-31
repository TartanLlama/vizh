#include <string.h>
#include <stdlib.h>
#include "libv.h"

void newtape(vizh_tapes_t* tapes) {    
    // This is the first time we've allocated a new tape in this function
    if (tapes->capacity == 0) {
        // Initially allocate enough space for one additional pointer
        tapes->capacity = tapes->n_tapes + 1;
        char** new_tapes = (char**)malloc(sizeof(char*) * tapes->capacity);
        memcpy(new_tapes, tapes->tapes, tapes->n_tapes * sizeof(char**));

        tapes->tapes = new_tapes; 
        tapes->tapes[tapes->n_tapes] = (char*)malloc(TAPE_SIZE);
        ++tapes->n_tapes;
    }

    // Otherwise, if there's enough capacity, create a new tape
    else if (tapes->n_tapes < tapes->capacity) {
        tapes->tapes[tapes->n_tapes] = (char*)malloc(TAPE_SIZE);
        ++tapes->n_tapes;
    }

    // Otherwise double the capacity 
    else {
        tapes->capacity *= 2;
        tapes->tapes = (char**)realloc(tapes->tapes, tapes->capacity * sizeof(char*));
        tapes->tapes[tapes->n_tapes] = (char*)malloc(TAPE_SIZE);
        ++tapes->n_tapes;
    }
}

void freetape(vizh_tapes_t* tapes) {
    --tapes->n_tapes;
    free(tapes->tapes[tapes->n_tapes]);
}