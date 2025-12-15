/*
C unit tests for shared memory reader.

Compile with: gcc -o test_shm test_shm.c ../src/shm_reader.c -I../src -I../bindings -lrt -lpthread

Note: This is a stub test file. Full implementation requires linking
against compiled libviz components.
*/

#include <stdio.h>
#include <assert.h>
#include <string.h>
#include "../src/shm_reader.h"

void test_frame_header_size() {
    // Verify header size matches protocol
    assert(sizeof(FrameHeader) == HEADER_SIZE);
    printf("✓ Frame header size correct\n");
}

void test_frame_size() {
    // Verify frame size matches slot size
    assert(sizeof(Frame) == SLOT_SIZE);
    printf("✓ Frame size correct\n");
}

void test_magic_number() {
    // Verify magic number constant
    assert(MAGIC_NUMBER == 0x56495A46);
    printf("✓ Magic number correct\n");
}

int main() {
    printf("Running libviz unit tests...\n");
    
    test_frame_header_size();
    test_frame_size();
    test_magic_number();
    
    printf("\nAll tests passed!\n");
    return 0;
}
