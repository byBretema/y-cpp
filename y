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


def title_print(msg, ln=True):
    newline = "\n" * ln if ln > 0 else ""
    y.println_fill("\n\n{s}  {t}  {s}" f"{newline}", "░", t=msg)


################################################################################
### Build
################################################################################


def build(build_type, generator, cwd):
    title_print("⚙️ : CONFIG")

    config_cmd: list[str] = [
        "cmake",
        "-G",
        generator,
        "../..",
        f"-DCMAKE_BUILD_TYPE={build_type}",
        "-DCMAKE_POLICY_VERSION_MINIMUM=3.10",
    ]
    y.run_cmd(config_cmd, cwd=cwd)

    title_print("🔨 : BUILD")

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
    title_print("🧪 : TESTs", ln=False)

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

            if p.stdout:
                y.println_fill("··· {m1} {s}", "·", m1=filename)
                y.println()
                y.println(p.stdout)

            ok: bool = not p.returncode
            status: str = "PASS 🟢" if ok else "FAIL 🔴"
            y.println_fill("··· {m1} {s} {m2}", "·", m1=filename, m2=f"{status}")

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

    parser.add_argument("-r", "--release", action="store_true", help="Build in Release mode")
    parser.add_argument("-g", "--generator", type=str, default="Ninja", help="CMake generator")

    args = parser.parse_args()

    # - Vars -------------------------------------------------------------------

    build_type: str = "Release" if args.release else "Debug"
    sub_build_dir: str = f"{BUILD_DIR}/sub-build"
    generator: str = args.generator

    # - Required ---------------------------------------------------------------

    y.required_command("cmake")

    if generator == "Ninja":
        y.required_command("ninja")

    # - Cleanup ----------------------------------------------------------------

    if args.fullcleanup and os.path.isdir(BUILD_DIR):
        shutil.rmtree(BUILD_DIR)
    os.makedirs(BUILD_DIR, exist_ok=True)

    if args.cleanup and os.path.isdir(sub_build_dir):
        shutil.rmtree(sub_build_dir)
    os.makedirs(sub_build_dir, exist_ok=True)

    # - Cmake ------------------------------------------------------------------

    if args.build:
        build(build_type, generator, cwd=sub_build_dir)

    # - Tests ------------------------------------------------------------------

    if args.tests:
        tests()


################################################################################
### Entry Point
################################################################################

y.entrypoint(main)
