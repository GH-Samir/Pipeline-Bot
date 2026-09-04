def is_odd(n):
    """Return True if n is odd, False otherwise."""
    return n % 2 != 0


if __name__ == "__main__":
    import sys

    num = int(sys.argv[1]) if len(sys.argv) > 1 else int(input("Enter a number: "))
    print(f"{num} is {'odd' if is_odd(num) else 'not odd'}")
