
#define yyEnable_Aliases
#define yyEnable_Testing
// #define yyDisable_LogFileAndLine
#define yyLib_Glm
#include <y.hpp>

int main() {

    y::Test T {};
    // T.set_align_column(42);


    T.make_section("Fmt");
    {
        T.test("vec i32", [] {
            Vec v { 1, 2, 3, 4 };
            auto str1 = y_fmt("{}", v);
            Vec3 gv3 { 1, 2, 3 };
            auto str2 = y_fmt("{}", gv3);
            return true;
        });
    }


    T.make_section("Defer Ref");
    {
        i32 count = 0;
        {
            y_defer(count += 2);
            T.eq("Before", count, 0);
        }
        T.eq("After", count, 2);
    }


    T.make_section("Defer Copy");
    {
        static i32 static_defer_count = 0;
        i32 defer_count = 3;
        {
            // y::Defer D { [=] { static_defer_count += defer_count; } };
            y_deferc(static_defer_count += defer_count);
            T.eq("Before", static_defer_count, 0);
        }
        T.eq("After", static_defer_count, 3);
    }


    T.make_section("Str Format");
    {
        T.eq("Str", y_fmt("Test {}", "String"), "Test String");
        T.eq("i32", y_fmt("Test {}", 42), "Test 42");
        T.eq("f32", y_fmt("Test {}", 3.14159f), "Test 3.14159");
        T.eq("f64", y_fmt("Test {}", 3.14159), "Test 3.14159");
    }


    T.make_section("Bit Ops");
    {
        T.eq("Bit 1", y::bit(1), 2);
        T.eq("Bit 2", y::bit(2), 4);
        T.eq("Bit 3", y::bit(3), 8);
        T.eq("Bit 4", y::bit(4), 16);
        T.eq("Bit 5", y::bit(5), 32);
    }


    T.make_section("Cast Types");
    {
        T.eq("As i8 (clamp)", i8(3.14159), 3);
        T.eq("As i8 (size)", sizeof(i8(3.14159)), sizeof(i8));
        T.eq("As f32", sizeof(f32(3.14159)), sizeof(f32));

        i32 *heap_i = new i32(5);
        T.ok("As void*", typeid(((void *)(heap_i))) == typeid(void *));
        delete heap_i;
    }


    T.make_section("Numeric Aliases");
    {
        T.eq("u8 min", u8_min, std::numeric_limits<uint8_t>::min());
        T.eq("u8 max", u8_max, std::numeric_limits<uint8_t>::max());
        T.eq("u16 min", u16_min, std::numeric_limits<uint16_t>::min());
        T.eq("u16 max", u16_max, std::numeric_limits<uint16_t>::max());
        T.eq("u32 min", u32_min, std::numeric_limits<uint32_t>::min());
        T.eq("u32 max", u32_max, std::numeric_limits<uint32_t>::max());
        T.eq("u64 min", u64_min, std::numeric_limits<uint64_t>::min());
        T.eq("u64 max", u64_max, std::numeric_limits<uint64_t>::max());
        T.eq("usize min", usize_min, std::numeric_limits<size_t>::min());
        T.eq("usize max", usize_max, std::numeric_limits<size_t>::max());

        T.eq("i8 min", i8_min, std::numeric_limits<int8_t>::min());
        T.eq("i8 max", i8_max, std::numeric_limits<int8_t>::max());
        T.eq("i16 min", i16_min, std::numeric_limits<int16_t>::min());
        T.eq("i16 max", i16_max, std::numeric_limits<int16_t>::max());
        T.eq("i32 min", i32_min, std::numeric_limits<int32_t>::min());
        T.eq("i32 max", i32_max, std::numeric_limits<int32_t>::max());
        T.eq("i64 min", i64_min, std::numeric_limits<int64_t>::min());
        T.eq("i64 max", i64_max, std::numeric_limits<int64_t>::max());
        T.eq("isize min", isize_min, std::numeric_limits<ptrdiff_t>::min());
        T.eq("isize max", isize_max, std::numeric_limits<ptrdiff_t>::max());

        T.eq("f32 min", f32_min, std::numeric_limits<float>::min());
        T.eq("f32 max", f32_max, std::numeric_limits<float>::max());
        T.eq("f32 epsilon", f32_epsilon, std::numeric_limits<float>::epsilon());

        T.eq("f64 min", f64_min, std::numeric_limits<double>::min());
        T.eq("f64 max", f64_max, std::numeric_limits<double>::max());
        T.eq("f64 epsilon", f64_epsilon, std::numeric_limits<double>::epsilon());
    }


    T.make_section("Pointers Aliases");
    {
        struct A {
            Str s = "A";
            f32 f = 3.14159f;
        } a;

        y::Uptr<A> ua = y::u_new<A>("A", 3.14159f);
        T.eq("Uptr 1", a.s, ua->s);
        T.eq("Uptr 2", a.f, ua->f);

        y::Sptr<A> sa = y::s_new<A>("A", 3.14159f);
        T.eq("Sptr 1", a.s, sa->s);
        T.eq("Sptr 2", a.f, sa->f);
    }


    T.make_section("Optional Reference");
    {
        struct A {
            i32 i = 42;
        } a;

        auto const fn_value = [](A &received_a) -> OptRef<A> { return received_a; };
        auto opt = fn_value(a);
        T.ok("Has Value", opt.has_value());
        T.eq("Check Value", opt.value().get().i, 42);

        auto const fn_null = [](A &received_a) -> OptRef<A> { return {}; };
        T.ok("Not Has Value", !fn_null(a).has_value());
    }


    T.make_section("Elapsed Timer");
    {
        using namespace std::chrono_literals;
        y::ETimer timer {};
        T.ok("Init Invalid 1", !timer.is_valid());
        T.eq("Init Invalid 2", timer.elapsed_ns() * timer.is_valid(), 0);
        timer.reset();
        std::this_thread::sleep_for(10ms);
        T.gt("After Reset", timer.elapsed_ms() * timer.is_valid(), 9);
    }


    T.make_section("String Ops");
    {
        {
            Str const s = "test STRING to PERFORM the tests";
            T.eq("To Lower", y::str_lower(s), "test string to perform the tests");
            T.eq("To Upper", y::str_upper(s), "TEST STRING TO PERFORM THE TESTS");
            T.eq("To Capital", y::str_capital(s), "Test string to perform the tests");
        }

        {
            Str const s = "1,2,3,4,5";
            T.eq("Replace All", y::str_replace(s, ",", " / "), "1 / 2 / 3 / 4 / 5");
            T.eq("Replace First", y::str_replace(s, ",", " / ", true), "1 / 2,3,4,5");
        }

        {
            Str const s = "1.2-3:4·5";
            Str const s_ok = "1[1] 2[2] 3[3] 4[4] 5";

            Vec<Str> from = { "-", ".", "·", ":" };
            Vec<Str> to = { "[2] ", "[1] ", "[4] ", "[3] " };
            T.eq("Replace Many Unsorted", y::str_replace_many(s, from, to), s_ok);

            from = { ".", "-", ":", "·" };
            to = { "[1] ", "[2] ", "[3] ", "[4] " };
            T.eq("Replace Many Sorted", y::str_replace_many(s, from, to, true), s_ok);
        }

        {
            Str const s = "1,2,3,4,5";
            Vec<Str> const s_res = { "1", "2", "3", "4", "5" };
            T.ok("Split", y::str_split(s, ",") == s_res);
            T.ok("Join", y::str_join(s_res, ",") == s);
        }

        {
            T.eq("Cut", y::str_cut(" / a / b / c / ", 3), "a / b / c");
            T.eq("Cut L", y::str_cut_l(" / a / b / c", 3), "a / b / c");
            T.eq("Cut R", y::str_cut_r("a / b / c / ", 3), "a / b / c");

            T.ok("Contains", y::str_contains("a / b / c / ", " b "));

            T.eq("Trim", y::str_trim(" aaa "), "aaa");
            T.eq("Trim L", y::str_trim_l(" aaa "), "aaa ");
            T.eq("Trim R", y::str_trim_r(" aaa "), " aaa");

            // yInfo("==> {}", y::str_trim("***aaa***", "***"));
            T.eq("Trim Not Space", y::str_trim("***aaa***", "***"), "aaa");
        }
    }


    T.make_section("Files Ops");
    {
        auto constexpr s_write_bin { "./tests/output/to_file_write.bin" };
        auto constexpr s_append_txt { "./tests/output/to_file_append.txt" };
        auto constexpr s_read_txt { "./tests/input/to_file_read.txt" };

        {
            Str const content = y::file_read(s_read_txt);
            Str const expected = "Test\nFile\nFor\nTesting\nFile\nReading\n";
            T.eq("Read", content, expected);
        }

        {
            Str const stamp = y::time_stamp();
            T.ok("Append", y::file_append(s_append_txt, stamp + "\n"));

            Str const content = y::file_read(s_append_txt);
            Vec<Str> const split = y::str_split(content, "\n");
            T.eq("Append > Read > Split", split[split.size() - 1], stamp);
        }

        {
            Vec<u8> const bin { 'T', 'e', 's', 't', '\n', 'D', 'a', 't', 'a' };
            T.ok("Write", y::file_overwrite(s_write_bin, bin));
            T.ok("Write Validation", y::fs::exists(s_write_bin));

            auto const bin_content = y::bin_read(s_write_bin);
            Vec<u8> const magic { 'T', 'e', 's', 't' };
            T.ok("Magic", y::bin_check_magic(bin_content, magic));
        }

        {
            T.ok("Extension", y::file_check_extension("./to_file_write.bin", "BiN"));
        }
    }


    T.show_results();
    return T.cli_result();
}
