
#define yyEnable_Aliases
#include "../vendor/y.hpp"



////////////////////////////////////////////////////////////////////////////////

// clang-format off
// --- Variadic Macro Helpers ---
#define __yFE1(WHAT, X)     WHAT(X)
#define __yFE2(WHAT, X, ...) WHAT(X) __yFE1(WHAT, __VA_ARGS__)
#define __yFE3(WHAT, X, ...) WHAT(X) __yFE2(WHAT, __VA_ARGS__)
#define __yFE4(WHAT, X, ...) WHAT(X) __yFE3(WHAT, __VA_ARGS__)
#define __yFE5(WHAT, X, ...) WHAT(X) __yFE4(WHAT, __VA_ARGS__)
#define __yFE6(WHAT, X, ...) WHAT(X) __yFE5(WHAT, __VA_ARGS__)
#define __yFE7(WHAT, X, ...) WHAT(X) __yFE6(WHAT, __VA_ARGS__)
#define __yFE8(WHAT, X, ...) WHAT(X) __yFE7(WHAT, __VA_ARGS__)
#define __yFE9(WHAT, X, ...) WHAT(X) __yFE8(WHAT, __VA_ARGS__)
#define __yFE10(WHAT, X, ...) WHAT(X) __yFE9(WHAT, __VA_ARGS__)

// Helper to count arguments to size the std::array
#define __yCount(...) __yGetMacro(__VA_ARGS__, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1)

#define __yGetMacro(_1,_2,_3,_4,_5,_6,_7,_8,_9,_10,NAME,...) NAME
#define __yForEach(action, ...) __yGetMacro(__VA_ARGS__, __yFE10, __yFE9, __yFE8, __yFE7, __yFE6, __yFE5, __yFE4, __yFE3, __yFE2, __yFE1)(action, __VA_ARGS__)

#define __yEnumDef(entry)         entry,
#define __yEnumQualified(entry)   T::entry,
#define __yEnumCase(entry)        case T::entry: return #entry;
#define __yEnumFromStr(entry)     if (name == #entry) return T::entry;

// --- Main Macro ---
#define y_make_enum(EnumType, UType, ...)                                                          \
    enum struct EnumType : UType { __yForEach(__yEnumDef, __VA_ARGS__) };                          \
                                                                                                   \
    /* List all Values: Returns std::array for constexpr support */                                \
    constexpr auto e_##EnumType##All() {                                                           \
        using T = EnumType;                                                                        \
        return std::array<T, __yCount(__VA_ARGS__)>{ __yForEach(__yEnumQualified, __VA_ARGS__) };  \
    }                                                                                              \
                                                                                                   \
    /* To Index */                                                                                 \
    constexpr UType e_##EnumType##ToIndex(EnumType value) { return static_cast<UType>(value); }    \
                                                                                                   \
    /* To String: Returns string_view */                                                           \
    constexpr std::string_view e_##EnumType##ToString(EnumType value) {                            \
        using T = EnumType;                                                                        \
        switch (value) {                                                                           \
            __yForEach(__yEnumCase, __VA_ARGS__)                                                   \
        }                                                                                          \
        return "Unknown";                                                                          \
    }                                                                                              \
                                                                                                   \
    /* From String: Returns std::optional since there is no 'None' default */                      \
    constexpr std::optional<EnumType> e_##EnumType##FromString(std::string_view name) {            \
        using T = EnumType;                                                                        \
        __yForEach(__yEnumFromStr, __VA_ARGS__)                                                    \
        return std::nullopt;                                                                       \
    }                                                                                              \
                                                                                                   \
    /* List Names: Returns std::array of string_views */                                           \
    constexpr auto e_##EnumType##Names() {          \
        using T = EnumType;    \
        constexpr size_t count = __yCount(__VA_ARGS__) ;                                               \
        std::array<std::string_view, count> names{};                                \
        auto values = e_##EnumType##All();  \
        for (size_t i = 0; i < count; ++i)\
            names[i] = e_##EnumType##ToString(values[i]);\
        return names;\
    }                                                                                              \
    struct __e_##EnumType##_terminator
// clang-format on

////////////////////////////////////////////////////////////////////////////////


y_make_enum(LightsView, u32, Simplified, Detailed);

int main() {
    // Test Iteration
    y_println("\n--- Iteration ---\n");
    for (auto v : e_LightsViewAll()) {
        y_println("{}", e_LightsViewToString(v));
    }

    // Test Resolution
    y_println("\n--- Resolution ---\n");
    auto v = e_LightsViewFromString("Complex");
    y_println("Found: {}", e_LightsViewToIndex(v));

    return 0;
}
