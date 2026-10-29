
import subprocess


def run_command(command, cwd):
    result = subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
        shell=False
    )

    return result
