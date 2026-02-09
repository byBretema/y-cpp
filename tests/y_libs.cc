
#define yyLib_Fmt
#define yyEnable_Aliases
#include "../vendor/y.hpp"

int main() {
    auto const s = y::str_join({ "a", "b", "c" }, ",");
    [[maybe_unused]] auto fmt_str = y_fmt("{}", s);
    y_print("AAAAA: {}\n", 3);
}
