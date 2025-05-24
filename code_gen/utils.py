from collections import defaultdict

def generate_unique_index(first_index: int, second_index: int) -> str:
    return str(first_index).ljust(10, '0') + str(second_index)