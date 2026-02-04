import os
import sys
import platform
import shutil
import subprocess
from pathlib import Path
import tempfile
from typing import NoReturn, Callable, Generator
import glob
import json
import traceback
from collections import namedtuple
import enum
import unicodedata
from contextlib import contextmanager
from dataclasses import dataclass

################################################################################
### Globals
################################################################################

EXIT_CB: Callable | None = None
TRACE_CB: Callable | None = None
PROCESS_CB: Callable | None = None
PROCESS_TH: int = 10
PROCESS_FILEPATH: str | None = None
SHOW_TRACEBACK: bool = False
SHOW_TRACEBACK_ENTRYPOINT: bool = False
REQUIRED_VERBOSE: bool = False
MAX_WIDTH: int = 80


################################################################################
### Logger
################################################################################

__GLOBAL_TEE: Generator[None, str, None] | None = None
__GLOBAL_TEE_WITH_CALLBACK: Generator[None, str, None] | None = None


def tee(msg: str, run_cb: bool = False):
    target_tee = __GLOBAL_TEE_WITH_CALLBACK if run_cb else __GLOBAL_TEE
    if target_tee:
        target_tee.send(msg)


def tee_make(
    log_filepath: str | None = None,
    log_threshold: int = 1,
    closure: Callable[[str], None] | None = None,
) -> Generator[None, str, None]:

    def _worker():
        count: int = 0
        partial: str = ""

        effective_threshold = 1 if log_threshold < 1 else log_threshold

        if log_filepath and not os.path.isfile(log_filepath):
            raise Exception("LogFile not found")

        try:
            while True:
                line = yield

                if line:
                    sys.stdout.write(line)
                    sys.stdout.flush()
                    count += 1
                    partial += line

                    if log_filepath:
                        with open(log_filepath, "a") as file:
                            file.write(line)

                if count >= effective_threshold:
                    if partial and closure:
                        closure(partial)
                    count = 0
                    partial = ""

        finally:
            if partial and closure:
                closure(partial)

    t = _worker()
    next(t)
    return t


def _log_error(message: str, exception=None) -> None | NoReturn:

    exception_err = f" | {type(exception)}\n{str(exception)}" if exception else ""
    err = f"\n\n@ ERROR | {message}{exception_err}\n"

    tee(err)

    if EXIT_CB:
        EXIT_CB(err)

    if SHOW_TRACEBACK:
        tee(f"\n{traceback.format_exc()}")

    tee("")


def error_exit(msg: str, exception=None) -> NoReturn:
    _log_error(msg, exception)
    sys.exit(1)


def log_error(msg: str, exception=None):
    _log_error(msg, exception)
    tee("- - - - - Execution will continue below - - - - -\n")


def log_info(msg: str, prefix="· ", ln="\n"):
    tee(f"{prefix}{msg}{ln}")


def println(msg: str = ""):
    log_info(msg, "")


def print(msg: str = ""):
    log_info(msg, "", "")


def fill_str(ref: str, sep: str, **kwargs):
    sep = sep if len(sep) > 0 else " "

    kwargs["s"] = ""
    intermediate_str = ref.format(**kwargs)

    sep_count = ref.count("{s}")
    sep_chars_count = max(MAX_WIDTH - emoji_str_len(intermediate_str, True), 0)
    n_sep = (sep_chars_count // sep_count // emoji_str_len(sep)) + (sep_chars_count % sep_count)
    kwargs["s"] = sep * n_sep

    final_str = ref.format(**kwargs)

    tries = 0
    while emoji_str_len(final_str, True) > MAX_WIDTH and tries < 10:
        head, _, tail = final_str.rpartition(sep)
        final_str = head + tail
        tries += 1

    return final_str


def println_fill(ref: str, sep: str, **kwargs):
    println(fill_str(ref, sep, **kwargs))


def print_fill(ref: str, sep: str, **kwargs):
    print(fill_str(ref, sep, **kwargs))


class BoxStyle(enum.Enum):
    Light = enum.auto()
    Bold = enum.auto()
    Double = enum.auto()
    Rounded = enum.auto()
    Ascii = enum.auto()


@dataclass
class BoxTheme:
    tl: str  # Top Left
    tr: str  # Top Right
    h: str  # Horizontal
    v: str  # Vertical
    bl: str  # Bottom Left
    br: str  # Bottom Right
    junc: str  # Junction (Tree middle)
    term: str  # Terminator (Tree end)

    @classmethod
    def get(cls, style: BoxStyle):
        # fmt: off
        themes = {
            BoxStyle.Light:   cls("┌", "┐", "─", "│", "└", "┘", "├", "└"),
            BoxStyle.Bold:    cls("┏", "┓", "━", "┃", "┗", "┛", "┣", "┗"),
            BoxStyle.Double:  cls("╔", "╗", "═", "║", "╚", "╝", "╠", "╚"),
            BoxStyle.Rounded: cls("╭", "╮", "─", "│", "╰", "╯", "├", "╰"),
            BoxStyle.Ascii:   cls("·", "·", "-", "|", "·", "·", "·", "L"),
        }
        # fmt: on
        return themes[style]


def print_header(
    msg,
    pre: str = "\n\n",
    post: str = "\n",
    is_tree: bool = False,
    fill_char="·",
    box: BoxTheme = BoxTheme.get(BoxStyle.Bold),
):
    bl = box.junc if is_tree else box.bl
    fill_char = fill_char if len(fill_char) else " "

    print(pre)
    print_fill("{tl}{s}{tr}" "\n", box.h, tl=box.tl, tr=box.tr)
    print_fill("{ml} {s} {m} {s} {mr}" "\n", fill_char, m=(msg.upper()), ml=box.v, mr=box.v)
    print_fill("{bl}{s}{br}" "\n", box.h, bl=bl, br=box.br)
    print(post)


@contextmanager
def temp_width(width):
    global MAX_WIDTH
    prev_max_width = MAX_WIDTH
    MAX_WIDTH = width
    try:
        yield
    finally:
        MAX_WIDTH = prev_max_width


################################################################################
### Run command
################################################################################


class RunCmdInfo:
    def __init__(self, returncode: int = -1, stdout: str = ""):
        self.returncode: int = returncode
        self.stdout: str = stdout

    def safe_stdout(self):
        return self.stdout.strip() if not self.returncode else None


def run_cmd(
    cmd: list[str],
    cwd: str | None = None,
    shell: bool = False,
    err_info: str = "",
    verbosity: int = 2,
    permissive: bool = False,
    external: bool = False,
) -> RunCmdInfo:

    cmd_str: str = " ".join(cmd)
    cmd_str += "" if not cwd else f"  (at {cwd})"
    if verbosity > 0:
        log_info(cmd_str, prefix="@ ")

    if external:  # TODO : Add a windows solution, 'stdbuf' is Linux only
        cmd = ["stdbuf", "-oL"] + cmd

    process = subprocess.Popen(
        cmd,
        shell=shell,  # Process input as a shell (to support &&, |, <<, etc)
        stdout=subprocess.PIPE,  # Capture stdout
        stderr=subprocess.STDOUT,  # Merge stderr into stdout
        text=True,  # Decode output to strings
        bufsize=1,  # Line-buffered pipe reading
        cwd=cwd,  # Set folder where execute the command
        env=os.environ.copy(),
    )

    stdout: str = ""

    if process.stdout:
        _tee = tee_make(PROCESS_FILEPATH, PROCESS_TH, PROCESS_CB)
        for line in iter(process.stdout.readline, ""):
            stdout += line
            if verbosity > 1:
                _tee.send(line)
        _tee.close()
        process.stdout.close()

    returncode = process.wait()
    if returncode:
        output: str = f"\n{stdout}" if stdout and verbosity < 2 else ""
        err_info = f"{err_info}. " if err_info else ""
        err_info = f"{err_info}Command failed with return code: {returncode}{output}"
        if not permissive:
            error_exit(err_info)
        elif verbosity > 1:
            log_info(err_info)

    return RunCmdInfo(returncode=returncode, stdout=stdout)


################################################################################
### Interactive
################################################################################


def get_chars(max_digits=2) -> str:
    result = ""

    def get_one_char():
        if sys.platform == "win32":
            import msvcrt

            return msvcrt.getche().decode("utf-8")
        else:
            import tty, termios

            fd = sys.stdin.fileno()
            prev_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                char = sys.stdin.read(1)
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, prev_settings)
            return char

    while len(result) < max_digits:
        char = get_one_char()

        if char in ("q"):
            result = ""
            break

        if char in ("\r", "\n"):
            break

        if char.isdigit():
            result += char
            sys.stdout.write(char)
            sys.stdout.flush()

    return result


def menu(
    options: list[str],
    header: str = "Choose one",
    prompt: str = "Option:",
    starts_at=1,
) -> str | None:

    if not options:
        return None

    #! Handy menu

    if shutil.which("fzf"):
        s = "\n".join(options)
        p = subprocess.run(["fzf"], input=s, check=False, stdout=subprocess.PIPE, text=True)
        return p.stdout.strip() if not p.returncode else None

    #! Classic menu

    box = BoxTheme.get(BoxStyle.Rounded)
    with temp_width(len(header) + 8):
        print_header(header.capitalize(), pre="", post="", is_tree=True, box=box)

    for i, t in enumerate(options, starts_at):
        println(f"{box.junc}{box.h} {i} {box.v} {t}")
    println(f"{box.v} ")

    try:
        print(f"{box.term}{box.h} {prompt.capitalize()}: ")
        max_digits = len(str(len(options)))
        choice = get_chars(max_digits).strip()
        if not choice:
            println()
            return None

        if choice.isdigit():
            idx = int(choice) - starts_at
            if 0 <= idx < len(options):
                return options[idx]

    except (EOFError, KeyboardInterrupt, ValueError):
        println()
        return None


################################################################################
### Required
################################################################################


def _required_base(
    item: str,
    cb: Callable[[str], bool | str | None],
    type: str,
    info: str = "",
    verbose: bool = False,
):
    info = f" {info}" if info else ""
    if not cb(item):
        error_exit(f"{type.capitalize()} '{item}' is required.{info}")
    if verbose:
        log_info(f"Found: {item}")


def required_command(cmd: str, info: str = "", verbose: bool = REQUIRED_VERBOSE):
    _required_base(cmd, shutil.which, "Command", info, verbose)


def required_file(path: str, info: str = "", verbose: bool = REQUIRED_VERBOSE):
    _required_base(path, os.path.isfile, "File", info, verbose)


def required_folder(path: str, info: str = "", verbose: bool = REQUIRED_VERBOSE):
    _required_base(path, os.path.isdir, "Folder", info, verbose)


################################################################################
### Conversions
################################################################################


def to_int(s: str, fallback: int):
    try:
        return int(s)
    except ValueError:
        return fallback


def to_bool(v):
    if isinstance(v, str):
        return v.lower() == "true"
    else:
        return bool(v)


################################################################################
### Env Utils
################################################################################


def env_path_add(to_add: list[str] | str):
    to_add = [to_add] if isinstance(to_add, str) else to_add
    prev_path = [os.environ.get("PATH", "")]
    os.environ["PATH"] = os.pathsep.join(to_add + prev_path)


def script_path():
    """
    returns the script path for the callee script
    """
    # try:
    #     return os.path.abspath(os.path.dirname(__file__))
    # except Exception as e:
    return os.path.abspath(os.path.dirname(sys.argv[0]))


################################################################################
### File Utils
################################################################################


def file_is_binary(file_path, chunk_size=1024, null_byte_threshold=0.1):
    if not os.path.exists(file_path):
        return False

    try:
        with open(file_path, "rb") as f:
            chunk = f.read(chunk_size)
    except IOError:
        return False

    null_count = chunk.count(b"\x00")
    if null_count / len(chunk) > null_byte_threshold:
        return True


################################################################################
### OS Utils
################################################################################


def os_tempfile(filename: str, check: bool = True):
    try:
        filepath = Path(os.path.join(tempfile.gettempdir(), filename))
        filepath.touch()
        return str(filepath)
    except Exception as e:
        if check:
            error_exit(f"Failed to create temp file: {e}")
        return ""


def os_home():
    return str(Path.home()).replace("\\", "/")


def mac_bundle(start_path: str, app_name: str, is_bundle: bool = True):
    # Mac paths
    if is_bundle:
        bundle = f"{start_path}/{app_name}.app"
        contents = f"{bundle}/Contents"
        frameworks = f"{contents}/Frameworks"
        bin = f"{contents}/MacOS/{app_name}"
        # Ensure Frameworks path exists and, consequently, Contents.
        os.makedirs(frameworks, exist_ok=True)
    else:
        bundle = start_path
        contents = start_path
        frameworks = start_path
        bin = f"{start_path}/{app_name}"
    # Return them as class-like object with fields
    MacBundle = namedtuple("MacBundle", "bundle contents frameworks bin")
    return MacBundle(bundle, contents, frameworks, bin)


def os_binpath(start_path: str, bin_name: str, macos_get_bundle: bool = False) -> str:
    p = platform.system().lower()

    if p == "windows":
        return f"{start_path}/{bin_name}.exe"

    if p == "linux":
        return f"{start_path}/{bin_name}"

    if p == "darwin":
        mac = mac_bundle(start_path, bin_name)
        if macos_get_bundle:
            return mac.bundle
        else:
            return mac.bin

    return ""


def os_copy_to(src: str, dst: str, only_content: bool = True):

    if os.path.isdir(src):
        log_info(f"Copying dir: {src} -> {dst}")
        if only_content:
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            folder_name = os.path.basename(src)
            shutil.copytree(src, f"{dst}/{folder_name}", dirs_exist_ok=True)

    else:
        log_info(f"Copying file: {src} -> {dst}")
        shutil.copy(src, dst)


class GlobSort(enum.Enum):
    Nope = enum.auto()
    Alpha = enum.auto()
    VerNum = enum.auto()


def os_glob(
    pattern: str,
    sort: GlobSort = GlobSort.Alpha,
    rev: bool = False,
    err_info: str = "",
) -> str | NoReturn:
    glob_res = glob.glob(pattern)

    if not sort is GlobSort.Nope:
        sort_algo = None  # If None its default is Alphabectically

        if sort is GlobSort.VerNum:
            rev = True
            sort_algo = lambda s: [int(u) for u in s.split(os.sep)[-1].split(".")]

        glob_res.sort(key=sort_algo, reverse=rev)

    final_path: str = glob_res[0].replace("\\", "/") if glob_res else ""

    if not final_path:
        err_info = f" {err_info}" if err_info else ""
        error_exit(f"Glob '{pattern}' has failed.{err_info}")

    return final_path


def os_parent(path: str, levels_up: int = 1):
    parent = os.path.dirname(path)
    for i in range(levels_up - 1):
        parent = os.path.dirname(parent)
    return parent


################################################################################
### Misc
################################################################################


def zip_it(dst: str, src: str):
    cmd = ["7z", "a", "-tzip", "-bso0", "-bsp0", "-bse1"]
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    run_cmd([*cmd, dst, src], verbosity=1)


def emoji_str_len(text: str, ignore_newline=False):
    width = 0
    for char in text:
        # Get the East Asian Width property
        eaw = unicodedata.east_asian_width(char)
        is_newline_char = ignore_newline and char == "\n"

        # 'W' (Wide) and 'F' (Fullwidth) usually take 2 columns
        if eaw in ("W", "F"):
            width += 2
        # Zero-width characters (like combining marks or ZWJ)
        # Category 'Mn' = Mark, Nonspacing; 'Cf' = Other, Format (includes ZWJ)
        elif unicodedata.category(char) in ("Mn", "Cf") or is_newline_char:
            width += 0
        else:
            width += 1

    return width


################################################################################
### AWS
################################################################################


def aws_copy_file(filepath: str, aws_filepath: str, content_type: str | None = None):

    cmd = ["aws", "s3", "cp", "--cache-control", "max-age:no-cache", filepath, aws_filepath]

    if content_type:
        cmd.insert(5, content_type)
        cmd.insert(5, "--content-type")

    run_cmd(cmd, verbosity=0, err_info=f"Could not update {filepath} to AWS", permissive=True)


def aws_auth(pem_filepath: str, key_filepath: str, trust_arn: str, profile_arn: str, role_arn: str, info: str = ""):

    info = int(len(info) < 1) * " " + f" {info}"

    required_file(pem_filepath, f"Missing AWS certificate file.{info}")
    required_file(key_filepath, f"Missing AWS private-key file.{info}")

    required_command(
        "aws_signing_helper",
        f"Get from https://github.com/aws/rolesanywhere-credential-helper/releases "
        "or 'chmod +x aws_signing_helper' if it's already in the path'",
    )

    aws_auth_cmd: list[str] = [
        "aws_signing_helper",
        "credential-process",
        "--certificate",
        pem_filepath,
        "--private-key",
        key_filepath,
        "--trust-anchor-arn",
        trust_arn,
        "--profile-arn",
        profile_arn,
        "--role-arn",
        role_arn,
    ]
    aws_auth_output: str = run_cmd(aws_auth_cmd, verbosity=0).stdout
    aws_auth: dict = json.loads(aws_auth_output)

    for key in ["AccessKeyId", "SecretAccessKey", "SessionToken"]:
        if not key in aws_auth:
            error_exit(f"Missing key '{key}' during AWS Auth")

    os.environ["AWS_ACCESS_KEY_ID"] = aws_auth["AccessKeyId"]
    os.environ["AWS_SECRET_ACCESS_KEY"] = aws_auth["SecretAccessKey"]
    os.environ["AWS_SESSION_TOKEN"] = aws_auth["SessionToken"]


################################################################################
### Qt
################################################################################


class QtInfo:
    def __init__(self):
        self.path: str = ""
        self.tools_path: str = ""
        self.plugins_path: str = ""
        self.deployqt: str = ""  # As path in windows and a command in macos
        self.cmake_defs: list[str] = []

        p = platform.system().lower()

        if p == "windows":
            self.path = f"{Path.home().drive}/Qt"
            required_folder(self.path)

            self.tools_path = f"{self.path}/Tools"
            required_folder(self.tools_path)

            qt_version_path = os_glob(f"{self.path}/*.*.*", GlobSort.VerNum)
            qt_msvc_path = os_glob(f"{qt_version_path}/msvc*_64", rev=True)

            log_info(f"Using Qt Version {os.path.basename(qt_version_path)}")
            log_info(f"Using MSVC Version {os.path.basename(qt_msvc_path)}")

            self.plugins_path = f"{qt_msvc_path}/plugins"
            required_folder(self.plugins_path)
            self.deployqt = f"{qt_msvc_path}/bin/windeployqt.exe"
            required_file(self.deployqt)
            self.cmake_defs = [f"-DCMAKE_PREFIX_PATH={qt_msvc_path}/lib/cmake"]

            env_path_add([f"{self.tools_path}/CMake_64/bin", f"{self.tools_path}/Ninja"])

        if p == "darwin":
            self.deployqt = "macdeployqt"
            required_command(self.deployqt)


################################################################################
### Entrypoint
################################################################################


def entrypoint(main: Callable, *args):
    import inspect

    callee_name = inspect.stack()[1].frame.f_globals.get("__name__", "")

    if callee_name != "__main__":
        return

    try:
        _init1()
        main(*args)
    except KeyboardInterrupt:
        _before_exit()
        error_exit("User interrupts execution.")
    except PermissionError as e:
        _before_exit()
        error_exit("Some files are in use, execution blocked", e)
    except Exception as e:
        _before_exit()
        error_exit("Unexpected", e)


################################################################################
### Setup
################################################################################


def _init1():
    global __GLOBAL_TEE
    if not __GLOBAL_TEE:
        __GLOBAL_TEE = tee_make(None, 1, None)


def _init2():
    global __GLOBAL_TEE_WITH_CALLBACK
    if not __GLOBAL_TEE_WITH_CALLBACK:
        __GLOBAL_TEE_WITH_CALLBACK = tee_make(None, 1, TRACE_CB)


def _before_exit():
    global SHOW_TRACEBACK
    SHOW_TRACEBACK = SHOW_TRACEBACK_ENTRYPOINT


def setup(
    exit_cb: Callable | None = None,
    trace_cb: Callable | None = None,
    process_cb: Callable | None = None,
    process_th: int = 10,
    process_filepath: str | None = None,
    show_traceback: bool = False,
    show_traceback_entrypoint: bool = False,
    required_verbose: bool = False,
    max_width: int = 80,
):

    global EXIT_CB
    EXIT_CB = exit_cb

    global TRACE_CB
    TRACE_CB = trace_cb

    global PROCESS_CB, PROCESS_TH, PROCESS_FILEPATH
    PROCESS_CB = process_cb
    PROCESS_TH = process_th
    PROCESS_FILEPATH = process_filepath

    global SHOW_TRACEBACK
    SHOW_TRACEBACK = show_traceback

    global SHOW_TRACEBACK_ENTRYPOINT
    SHOW_TRACEBACK_ENTRYPOINT = show_traceback_entrypoint

    global REQUIRED_VERBOSE
    REQUIRED_VERBOSE = required_verbose

    global MAX_WIDTH
    MAX_WIDTH = max_width

    _init2()
