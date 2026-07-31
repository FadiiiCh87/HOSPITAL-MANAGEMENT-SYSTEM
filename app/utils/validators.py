def is_empty(value):

    return not value or not value.strip()


def is_positive_number(value):

    try:
        return float(value) >= 0
    except ValueError:
        return False