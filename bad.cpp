#include <iostream>
#include <vector>

class Test {
public:
    Test(int v) : value(v) {} // Constructor initializes value
    void show() { std::cout << "Value: " << value << std::endl; }
    
private:
    int* value; // Incorrectly allocated memory (should be an int, not a pointer)
};

void memoryLeakFunction() {
    int* leak = new int(10); // Memory leak (never freed)
}

void undefinedBehavior() {
    int* ptr = nullptr;
    *ptr = 5; // Dereferencing null pointer (undefined behavior)
}

void bufferOverflow() {
    int arr[5];
    for (int i = 0; i <= 5; i++) { // Out-of-bounds access (buffer overflow)
        arr[i] = i;
    }
}

int main() {
    Test* t = new Test(5); // Memory leak (not deleted)
    t->show(); // Might crash due to incorrect value initialization

    memoryLeakFunction();
    undefinedBehavior(); // Will cause segmentation fault
    bufferOverflow(); // Writes out of bounds

    std::vector<int>* vec = new std::vector<int>(10); // Memory leak
    delete vec; // Incorrect delete (vector should be allocated without new)

    return 0;
}
