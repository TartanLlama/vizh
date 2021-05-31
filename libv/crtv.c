//If the user writes a function called main it'll get mangled to vizh_main
void vizh_main(char*);

//We then provide a C entry point which allocates some tape for the main function to work on
int main() {
    char primary_tape[4096] = {0};
    vizh_main(primary_tape);
}
