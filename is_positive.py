def is_positive(n):
    """Return True if n is positive, False otherwise."""
    return n > 0


if __name__ == "__main__":
    import sys

    n = int(sys.argv[1]) if len(sys.argv) > 1 else int(input("Enter a number: "))
    print(f"{n} is {'positive' if is_positive(n) else 'not positive'}")
