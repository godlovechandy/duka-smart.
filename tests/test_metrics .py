
import pandas as pd
import pytest

from metrics import calculate_metrics


def test_calculates_sales_metrics_correctly():
    sales = pd.DataFrame({
        "order_id": ["A", "A", "B"],
        "quantity": [2, 3, 4],
        "unit_price": [1000, 500, 2000],
    })

    result = calculate_metrics(sales)

    assert result["total_revenue"] == 11500
    assert result["total_orders"] == 2
    assert result["units_sold"] == 9
    assert result["average_order_value"] == 5750


def test_empty_sales_returns_zero_metrics():
    sales = pd.DataFrame({
        "order_id": pd.Series(dtype="str"),
        "quantity": pd.Series(dtype="int"),
        "unit_price": pd.Series(dtype="float"),
    })

    result = calculate_metrics(sales)

    assert result["total_revenue"] == 0
    assert result["total_orders"] == 0
    assert result["units_sold"] == 0
    assert result["average_order_value"] == 0


def test_missing_columns_raise_error():
    sales = pd.DataFrame({"product": ["Rice"]})

    with pytest.raises(ValueError):
        calculate_metrics(sales)
