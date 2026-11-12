from decimal import Decimal

GENERAL = "General clothing"
COMFORTER = "Comforters"
OPTIONS = [GENERAL, COMFORTER]

# Wash, dry, fold, detergent and fabric conditioner are free (included).
PER_KG = Decimal("30")
SMALL_LOAD_KG = Decimal("5")          # loads below this weight...
SMALL_LOAD_PRICE = Decimal("135")     # ...cost this flat price
PER_COMFORTER = Decimal("200")


def calculate_price(option, weight_kg=None, pieces=None):
    """The one place where an order's price is worked out."""
    if option == COMFORTER:
        return (PER_COMFORTER * int(pieces)).quantize(Decimal("0.01"))

    weight = Decimal(str(weight_kg))
    if weight < SMALL_LOAD_KG:
        return SMALL_LOAD_PRICE.quantize(Decimal("0.01"))
    return (weight * PER_KG).quantize(Decimal("0.01"))