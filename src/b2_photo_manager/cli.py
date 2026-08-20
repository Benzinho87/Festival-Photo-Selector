import sys

from b2_photo_manager.bootstrap import prepare_runtime


def main() -> None:
    prepare_runtime()

    if "--packaging-smoke" in sys.argv:
        from b2_photo_manager.packaging import run_smoke_check

        run_smoke_check()
        return

    from b2_photo_manager.app import run

    run()
