#include <random>
#include <iostream>
#include <string>
#include <glog/logging.h>

// Function: random_string
// Description: Generates a random string.
// Returns:
//  std::string: A random string.
std::string random_string() {
    const char charset[] = "abcdefghijklmnopqrstuvwxyz";

    std::random_device random_device;
    std::mt19937 generator(random_device());
    std::uniform_int_distribution<> dist(0, 25);

    std::string random_string;
    for (int i = 0; i < 10; ++i) {
        random_string += charset[dist(generator)];
    }

    return random_string;
}
