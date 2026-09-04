def is_even(n):
    """Return True if n is even, False otherwise."""
    return n % 2 == 0


if __name__ == "__main__":
    import sys

    num = int(sys.argv[1]) if len(sys.argv) > 1 else int(input("Enter a number: "))
    print(f"{num} is {'even' if is_even(num) else 'odd'}")
