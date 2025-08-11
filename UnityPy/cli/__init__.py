from argparse import ArgumentParser

from UnityPy.cli.update_tpk import update_tpk


def main():
    parser = ArgumentParser(
        prog="UnityPy",
        description="UnityPy cli utility",
    )

    subparsers = parser.add_subparsers(title="utils")

    update_tpk_parser = subparsers.add_parser("update_tpk", help="Updates TPK (typetree dump) file")
    update_tpk_parser.set_defaults(func=update_tpk)

    args = parser.parse_args()

    if not hasattr(args, "func"):
        parser.print_help()
        return

    operands = getattr(args, "operands", [])
    args.func(*operands)


if __name__ == "__main__":
    main()
