#include "random.h"

namespace Random {
    std::random_device rd;
    std::mt19937 rng(rd());
}
