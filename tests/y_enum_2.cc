#include <algorithm> // For std::equal in C++20, or manual loop
#include <array>
#include <iostream>
#include <string_view>

#define yyEnable_Aliases
#include "../vendor/y.hpp"

// =========================================================
// 1. Preprocessor Magic (Counting & Looping)
// =========================================================

// Argument Counter (Up to 10)
#define NUM_ARGS_(_1, _2, _3, _4, _5, _6, _7, _8, _9, _10, N, ...) N
#define NUM_ARGS(...) NUM_ARGS_(__VA_ARGS__, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1)

// Looper (Same as before)
#define FE_1(WHAT, X) WHAT(X)
#define FE_2(WHAT, X, ...) WHAT(X) FE_1(WHAT, __VA_ARGS__)
#define FE_3(WHAT, X, ...) WHAT(X) FE_2(WHAT, __VA_ARGS__)
#define FE_4(WHAT, X, ...) WHAT(X) FE_3(WHAT, __VA_ARGS__)
#define FE_5(WHAT, X, ...) WHAT(X) FE_4(WHAT, __VA_ARGS__)
#define FE_6(WHAT, X, ...) WHAT(X) FE_5(WHAT, __VA_ARGS__)
#define FE_7(WHAT, X, ...) WHAT(X) FE_6(WHAT, __VA_ARGS__)
#define FE_8(WHAT, X, ...) WHAT(X) FE_7(WHAT, __VA_ARGS__)
#define FE_9(WHAT, X, ...) WHAT(X) FE_8(WHAT, __VA_ARGS__)
#define FE_10(WHAT, X, ...) WHAT(X) FE_9(WHAT, __VA_ARGS__)

#define GET_MACRO(_1, _2, _3, _4, _5, _6, _7, _8, _9, _10, NAME, ...) NAME
#define FOR_EACH(action, ...)                                                                      \
    GET_MACRO(__VA_ARGS__, FE_10, FE_9, FE_8, FE_7, FE_6, FE_5, FE_4, FE_3, FE_2,                  \
              FE_1)(action, __VA_ARGS__)

// =========================================================
// 2. The Worker Macros
// =========================================================
#define ENUM_DEF(entry) entry,
#define ENUM_QUALIFIED(entry) T::entry,
#define ENUM_CASE(entry)                                                                           \
    case T::entry:                                                                                 \
        return #entry;
#define ENUM_FROM_STRING(entry)                                                                    \
    if (name == #entry)                                                                            \
        return T::entry;

// =========================================================
// 3. The Generator (Constexpr Version)
// =========================================================

#define NEW_ENUM(EnumType, ...)                                                                    \
    enum struct EnumType { None, FOR_EACH(ENUM_DEF, __VA_ARGS__) };                                \
                                                                                                   \
    /* 1. All Values (Returns std::array) */                                                       \
    constexpr auto e_##EnumType##All() {                                                           \
        using T = EnumType;                                                                        \
        /* +1 for None */                                                                          \
        return std::array<EnumType, NUM_ARGS(__VA_ARGS__) + 1> { T::None, FOR_EACH(ENUM_QUALIFIED, \
                                                                                   __VA_ARGS__) }; \
    }                                                                                              \
    /* 2. To Index */                                                                              \
    constexpr size_t e_##EnumType##ToIndex(EnumType value) { return static_cast<size_t>(value); }  \
    /* 3. To String (Returns string_view) */                                                       \
    constexpr std::string_view e_##EnumType##ToString(EnumType value) {                            \
        using T = EnumType;                                                                        \
        switch (value) {                                                                           \
        case T::None:                                                                              \
            return "None";                                                                         \
            FOR_EACH(ENUM_CASE, __VA_ARGS__)                                                       \
        }                                                                                          \
        return "None";                                                                             \
    }                                                                                              \
    /* 4. From String (Input is string_view) */                                                    \
    constexpr EnumType e_##EnumType##FromString(std::string_view name) {                           \
        using T = EnumType;                                                                        \
        if (name == "None")                                                                        \
            return T::None;                                                                        \
        FOR_EACH(ENUM_FROM_STRING, __VA_ARGS__)                                                    \
        return T::None;                                                                            \
    }                                                                                              \
    /* 5. All Names (Returns array of string_views) */                                             \
    constexpr auto e_##EnumType##Names() {                                                         \
        constexpr size_t Count = NUM_ARGS(__VA_ARGS__) + 1;                                        \
        std::array<std::string_view, Count> names {};                                              \
        auto values = e_##EnumType##All();                                                         \
        for (size_t i = 0; i < Count; ++i) {                                                       \
            names[i] = e_##EnumType##ToString(values[i]);                                          \
        }                                                                                          \
        return names;                                                                              \
    }                                                                                              \
    struct e_##EnumType##_terminator

// =========================================================
// 4. User Code
// =========================================================

NEW_ENUM(LightsView, Simplified, Detailed, Complex);

// =========================================================
// 5. Test (Proof of Compile-Time Execution)
// =========================================================

int main() {
    // RUNTIME Usage
    auto v = e_LightsViewFromString("Detailed");
    std::cout << "Runtime: " << e_LightsViewToString(v) << "\n";

    // COMPILE-TIME Usage (static_assert proves it works at build time)
    static_assert(e_LightsViewToIndex(LightsView::Detailed) == 2, "Index check");
    static_assert(e_LightsViewFromString("Simplified") == LightsView::Simplified, "String check");

    // Even the loop over names is constexpr!
    constexpr auto allNames = e_LightsViewNames();
    static_assert(allNames[2] == "Detailed", "Array check");

    for (auto const &e : e_LightsViewNames()) {
        y_println("{}", e);
    }

    return 0;
}
