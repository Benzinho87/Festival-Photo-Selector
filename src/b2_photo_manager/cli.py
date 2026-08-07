from b2_photo_manager.bootstrap import prepare_runtime


def main() -> None:
    prepare_runtime()

    from b2_photo_manager.app import run

    run()
