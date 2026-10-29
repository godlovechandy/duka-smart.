
import pandas as pd


def calculate_metrics(sales: pd.DataFrame) -> dict:
    """Calculate sales KPIs from the currently filtered sales data."""

    required_columns = {"order_id", "quantity", "unit_price"}

    missing = required_columns - set(sales.columns)
    if missing:
        raise ValueError(
            f"Missing required columns: {sorted(missing)}"
        )

    sales_amount = sales["quantity"] * sales["unit_price"]
    total_sales = float(sales_amount.sum())
    total_orders = int(sales["order_id"].nunique())
    units_sold = int(sales["quantity"].sum())

    average_order_value = (
        total_sales / total_orders if total_orders > 0 else 0.0
    )

    return {
        "total_sales": total_sales,
        "total_orders": total_orders,
        "units_sold": units_sold,
        "average_order_value": average_order_value,
    }
