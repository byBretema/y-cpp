
#define yyEnable_Aliases
#include "../vendor/y.hpp"

y_make_enum(LightsView, u32, Simplified, Detailed);

// =========================================================
// 5. Test
// =========================================================
int main() {
    // Test Iteration
    y_println("--- Iteration ---");
    for (auto v : e_LightsViewAll()) {
        y_println(e_LightsViewToString(v));
    }

    // Test Resolution
    y_println("--- Resolution ---");
    auto v = e_LightsViewFromString("Complex");
    y_println("Found: {}", e_LightsViewToIndex(v));

    return 0;
}
