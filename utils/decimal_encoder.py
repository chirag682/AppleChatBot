# decimal_encoder.py
import json
from decimal import Decimal

class DecimalEncoder(json.JSONEncoder):
    """
    Custom JSON encoder that converts Decimal to float.
    """
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


def convert_decimals(obj):
    """
    Recursively convert Decimals in a data structure to floats.
    """
    if isinstance(obj, list):
        return [convert_decimals(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: convert_decimals(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        return float(obj)
    return obj
