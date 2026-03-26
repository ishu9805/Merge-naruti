import os
import signal
import subprocess
import sys
import time


def terminate(proc):
    if proc.poll() is not None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()


def main():
    port = os.environ.get("PORT", "8000")

    web_proc = subprocess.Popen(
        [
            "gunicorn",
            "--chdir",
            "bladeweb-files",
            "app:app",
            "--bind",
            f"0.0.0.0:{port}",
        ]
    )

    bot_env = os.environ.copy()
    bot_env["DISABLE_INTERNAL_WEB"] = "1"
    bot_proc = subprocess.Popen([sys.executable, "-m", "shivu"], env=bot_env)

    def handle_signal(signum, _frame):
        terminate(web_proc)
        terminate(bot_proc)
        sys.exit(0)

    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    try:
        while True:
            web_code = web_proc.poll()
            bot_code = bot_proc.poll()
            if web_code is not None or bot_code is not None:
                terminate(web_proc)
                terminate(bot_proc)
                sys.exit(web_code if web_code is not None else bot_code)
            time.sleep(1)
    finally:
        terminate(web_proc)
        terminate(bot_proc)


if __name__ == "__main__":
    main()
