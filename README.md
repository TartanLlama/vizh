# vizh

An esoteric visual language based on a multi-tape turing machine.

## Language

### Abstract Machine

The vizh abstract machine consists of:

- A primary tape of 4096 8-bit unsigned integers
- Secondary tapes of 4096 8-bit unsigned integers which can be created and destroyed at runtime
- A read/write head with storage for a single 8-bit unsigned integer

The initial state of the abstract machine is:

- All primary tape cells are initialised to 0
- No secondary tapes are allocated
- The read/write head is initialised to the left-most cell of the primary tape

See [instructions](#instructions) for the valid operations on the abstract machine.

### Program

A vizh program consists of a number of functions, each in its own image file. (What image types are allowed? Ideally at least png and jpg)

The entry point to a vizh program is a function called `main`.

### Functions

A vizh function is an image file containing:

- The name of the function at the top left of the image
- A function signature at the top right of the image
- A sequnce of instructions in a horizontal line underneath these (can the instructions be split onto multiple lines? depends how easy that is to implement)

Function names are alphanumeric: `[a-zA-Z][a-zA-Z0-9]*`.

Function signatures are a sequence of parameter specifiers followed by a single return type specifier.

Valid parameter specifiers are:

- The capital letter `I` for integer
- The capital letter `P` for pointer

Valid return specifiers are:

- The capital letter `I` for integer
- The capital letter `P` for pointer
- The capital letter `V` for void (none)

### Instructions

The valid instructions in vizh and their encodings are:

- Left arrow: move the r/w head left
- Right arrow: move the r/w head right
- Up arrow: move the r/w head to the tape above the current one
- Down arrow: move the r/w head to the tape below the current one
- Function name in a circle: call the given function
- +: increment the value pointed to by the r/w head by `1`
- -: decrement the value pointed to by the r/w head by `1`
- Equilateral triangle with the point at the top: read the cell pointed to by the r/w head into the r/w head storage
- Equilateral triangle with the point at the bottom: write the value stored in r/w head storage into the cell pointed to by the r/w head
- {<instructions>}: loop over the instructions between the braces until the value pointed to by the r/w head at the start of the loop is `0` 

### Built-in Functions

Functions built-in to vizh are:

- `readin`: read an ASCII character from stdin and write its integral representation into the cell pointed to by the r/w head
- `print`: print the value of the cell pointed to by the r/w head to stout, interpreted as an ASCII character
- `newtape`: allocate a new secondary tape underneath the last one currently allocated (or the primary tape if there are no secondary tapes)
- `freetape`: deallocate the bottom-most secondary tape (no-op if there are not any)

### Examples

#### `memcopy`

![Implementation of memcpy in vizh](samples/memcopy.png)