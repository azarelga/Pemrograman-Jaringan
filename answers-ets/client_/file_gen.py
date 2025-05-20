import os
import argparse


def generate_random_binary_file(filename, size_mb):
    size_bytes = size_mb * 1024 * 1024
    with open(filename, "wb") as f:
        f.write(os.urandom(size_bytes))
    print(f"Created {filename} ({size_mb} MB)")


def main():
    parser = argparse.ArgumentParser(description="Generate random binary files.")
    parser.add_argument(
        "--sizes",
        nargs="+",
        type=int,
        default=[10, 100, 50],
        help="Sizes of files to generate in MB (default: 10 100 500)",
    )
    parser.add_argument(
        "--prefix", type=str, default="random", help="Prefix for generated files"
    )
    args = parser.parse_args()

    for size in args.sizes:
        filename = f"{args.prefix}_{size}mb.bin"
        generate_random_binary_file(filename, size)


if __name__ == "__main__":
    main()
