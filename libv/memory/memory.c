#include <string.h>
#include <stdlib.h>
#include <stdint.h>
#include "libv.h"

void newtape(vizh_tapes_t* tapes) {    
    // This is the first time we've allocated a new tape in this function
    if (tapes->capacity == 0) {
        // Initially allocate enough space for one additional pointer
        tapes->capacity = tapes->n_tapes + 1;
        uint8_t** new_tapes = (uint8_t**)malloc(sizeof(uint8_t*) * tapes->capacity);
        memcpy(new_tapes, tapes->tapes, tapes->n_tapes * sizeof(uint8_t**));

        tapes->tapes = new_tapes; 
        tapes->tapes[tapes->n_tapes] = (uint8_t*)malloc(TAPE_SIZE);
        memset(tapes->tapes[tapes->n_tapes], 0, TAPE_SIZE);

        tapes->to_free = (uint8_t**)malloc(sizeof(uint8_t*) * tapes->capacity);
        memset(tapes->to_free, NULL, tapes->n_tapes);
        tapes->to_free[tapes->n_tapes] = tapes->tapes[tapes->n_tapes];

        ++tapes->n_tapes;
    }

    // Otherwise, if there's enough capacity, create a new tape
    else if (tapes->n_tapes < tapes->capacity) {
        tapes->tapes[tapes->n_tapes] = (uint8_t*)malloc(TAPE_SIZE);
        memset(tapes->tapes[tapes->n_tapes], 0, TAPE_SIZE);
        tapes->to_free[tapes->n_tapes] = tapes->tapes[tapes->n_tapes];
        ++tapes->n_tapes;
    }

    // Otherwise double the capacity 
    else {
        tapes->capacity *= 2;
        tapes->tapes = (uint8_t**)realloc(tapes->tapes, tapes->capacity * sizeof(uint8_t*));
        tapes->tapes[tapes->n_tapes] = (uint8_t*)malloc(TAPE_SIZE);
        memset(tapes->tapes[tapes->n_tapes], 0, TAPE_SIZE);
        tapes->to_free[tapes->n_tapes] = tapes->tapes[tapes->n_tapes];
        ++tapes->n_tapes;
    }
}

void freetape(vizh_tapes_t* tapes) {
    --tapes->n_tapes;
    free(tapes->to_free[tapes->n_tapes]);
}