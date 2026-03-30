"""Common error handler for 0dai Python scripts.

Import and call wrap_main() in any script's if __name__ block:

    from scripts._error_handler import wrap_main
    if __name__ == "__main__":
        wrap_main(main)
"""
from __future__ import annotations

import sys
import traceback


def wrap_main(fn):
    """Run fn() with graceful error handling."""
    try:
        fn()
    except KeyboardInterrupt:
        print("\n[0dai] interrupted")
        sys.exit(130)
    except BrokenPipeError:
        sys.exit(0)
    except SystemExit:
        raise
    except FileNotFoundError as e:
        print(f"[0dai] file not found: {e.filename or e}", file=sys.stderr)
        sys.exit(1)
    except PermissionError as e:
        print(f"[0dai] permission denied: {e.filename or e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        # Show clean error, not stack trace
        error_type = type(e).__name__
        print(f"[0dai] error: {e}", file=sys.stderr)
        if "--debug" in sys.argv:
            traceback.print_exc()
        else:
            print(f"[0dai] run with --debug for full traceback", file=sys.stderr)
        sys.exit(1)
