#!/usr/bin/env python

import os
import shutil
import argparse

import vendor.y as y

################################################################################
### Globals
################################################################################

BUILD_DIR: str = "build"
TESTS_DIR: str = "tests"


################################################################################
### Build
################################################################################


def build(build_type, generator, cwd, build_tests):
    y.h1("CONFIG")

    config_cmd: list[str] = [
        "cmake",
        "-G",
        generator,
        "../..",
        f"-DCMAKE_BUILD_TYPE={build_type}",
        "-DCMAKE_POLICY_VERSION_MINIMUM=3.10",
        f"-DY_BUILD_TESTS={"ON" if build_tests else "OFF"}",
    ]
    y.run_cmd(config_cmd, cwd=cwd)

    y.h1("BUILD")

    build_cmd: list[str] = [
        "cmake",
        "--build",
        ".",
        "-j",
        str(os.cpu_count()),
        "--config",
        build_type,
    ]

    y.run_cmd(build_cmd, cwd=cwd)


################################################################################
### Tests
################################################################################


def tests():
    y.h1("TESTs", ln=False)

    tests_dir: str = os.path.abspath(f"{BUILD_DIR}/tests")

    if not os.path.isdir(tests_dir):
        y.log_error(f"Dir '{tests_dir}' not found. Tests not executed.")

    tests_total: int = 0
    tests_passed: int = 0

    for root, _, files in os.walk(tests_dir):
        for filename in files:
            filepath: str = os.path.join(root, filename)

            if not y.file_is_binary(filepath):
                continue

            y.println()

            tests_total += 1
            p: y.RunCmdInfo = y.run_cmd(
                [filepath],
                verbosity=0,
                permissive=True,
                external=True,
            )

            down_char = "-" if not p.stdout else "  ⌄  "
            y.print_fill("┌{s}┐" "\n", "─")
            y.print_fill("| {m} {s} |" "\n", " ", m=filename.upper())
            y.print_fill("• {s}{m}{s} •" "\n", "-", m=down_char)
            # y.print_fill("|{s}|" "\n", " ")
            # y.h2(filename, ln=False)

            if p.stdout:
                y.println("")
                y.println(p.stdout.strip('\n'))
                y.println("")
                y.print_fill("•{s}{m}{s}•" "\n", "-", m="  ⌃  ")

            ok: bool = not p.returncode
            status: str = "PASSED 🟢" if ok else "FAILED 🔴"
            # y.println_fill("··· {m1} {s} {m2}", "·", m1=filename, m2=f"{status}")
            y.print_fill("| Test of {m} {s} |" "\n", " ", m=f"{filename.upper()} has {status}")
            y.print_fill("└{s}┘" "\n", "─")

            tests_passed += int(ok)

    status: str = "PASS ✅️" if (tests_passed == tests_total) else "FAIL ⛔️"

    y.println()
    y.log_info(f"Passed tests ({tests_passed}/{tests_total}) ❱ {status}")


################################################################################
### Main
################################################################################


def main():

    # - Setup ------------------------------------------------------------------

    y.setup(show_traceback=True)

    # - Args -------------------------------------------------------------------

    parser = argparse.ArgumentParser(description="Build script")

    parser.add_argument("-t", "--tests", action="store_true", help="Run project tests")
    parser.add_argument("-b", "--build", action="store_true", help="Run config/build step")
    parser.add_argument("-c", "--clean", action="store_true", help="Cleanup sub-build directory")
    parser.add_argument("-C", "--fresh", action="store_true", help="Cleanup build directory")

    parser.add_argument("--debug", action="store_true", help="Build in Debug mode")
    parser.add_argument("-g", "--generator", type=str, default="Ninja", help="CMake generator")

    args = parser.parse_args()

    # - Vars -------------------------------------------------------------------

    build_type: str = "Release" if not args.debug else "Debug"
    sub_build_dir: str = f"{BUILD_DIR}/sub-build"
    generator: str = args.generator

    # - Required ---------------------------------------------------------------

    y.required_command("cmake")

    if generator == "Ninja":
        y.required_command("ninja")

    # - Cleanup ----------------------------------------------------------------

    if args.fresh and os.path.isdir(BUILD_DIR):
        shutil.rmtree(BUILD_DIR)
    os.makedirs(BUILD_DIR, exist_ok=True)

    if args.clean and os.path.isdir(sub_build_dir):
        shutil.rmtree(sub_build_dir)
    os.makedirs(sub_build_dir, exist_ok=True)

    # - Cmake ------------------------------------------------------------------

    if args.build:
        build(build_type, generator, cwd=sub_build_dir, build_tests=args.tests)

    # - Tests ------------------------------------------------------------------

    if args.tests:
        tests()


################################################################################
### Entry Point
################################################################################

y.entrypoint(main)
