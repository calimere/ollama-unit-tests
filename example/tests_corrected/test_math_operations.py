"""
Tests unitaires pour math_operations.py
Générés automatiquement avec Ollama
"""

from example.math_operations import *


import pytest
@pytest.fixture
def test_calculator():
    return Calculator()
@pytest.fixture
def test_statistics():
    return Statistics()
def test_calculator_init(calculator):
    assert calculator.precision == 2
    assert calculator.history == []
def test_calculator_add(calculator):
    result = calculator.add(2.5, 3.7)
    assert round(result, 2) == 6.2
    assert "2.5 + 3.7 = 6.20" in calculator.history
def test_calculator_subtract(calculator):
    result = calculator.subtract(4.8, 2.1)
    assert round(result, 2) == 2.7
    assert "4.8 - 2.1 = 2.70" in calculator.history
def test_calculator_multiply(calculator):
    result = calculator.multiply(3.5, 4.9)
    assert round(result, 2) == 17.15
    assert "3.5 * 4.9 = 17.15" in calculator.history
def test_calculator_divide(calculator):
    with pytest.raises(ValueError):
        calculator.divide(10, 0)
def test_calculator_power(calculator):
    result = calculator.power(2, 3)
    assert round(result, 2) == 8.00
    assert "2 ^ 3 = 8.00" in calculator.history
def test_calculator_square_root(calculator):
    with pytest.raises(ValueError):
        calculator.square_root(-4)
def test_calculator_get_history(calculator):
    result = calculator.add(1, 2)
    history = calculator.get_history()
    assert "1 + 2 = 3.00" in history
def test_calculator_clear_history(calculator):
    calculator.history.append("Test")
    calculator.clear_history()
    assert not calculator.history
def test_statistics_init(statistics):
    assert statistics.data == []
def test_statistics_add_value(statistics):
    statistics.add_value(1)
    statistics.add_value(2)
    assert statistics.data == [1, 2]
def test_statistics_mean(statistics):
    statistics.add_value(1)
    statistics.add_value(2)
    mean = statistics.mean()
    assert round(mean, 2) == 1.5
def test_statistics_median(statistics):
    statistics.add_value(1)
    statistics.add_value(2)
    median = statistics.median()
    assert round(median, 2) == 1.5
def test_statistics_variance(statistics):
    statistics.add_value(1)
    statistics.add_value(2)
    variance = statistics.variance()
    assert round(variance, 2) == 0.25
def test_statistics_standard_deviation(statistics):
    statistics.add_value(1)
    statistics.add_value(2)
    std_dev = statistics.standard_deviation()
    assert round(std_dev, 2) == 0.5
def test_statistics_min_value(statistics):
    statistics.add_value(1)
    statistics.add_value(2)
    min_val = statistics.min_value()
    assert min_val == 1
def test_statistics_max_value(statistics):
    statistics.add_value(1)
    statistics.add_value(2)
    max_val = statistics.max_value()
    assert max_val == 2
def test_factorial():
    for i in range(10):
        result = factorial(i)
        assert isinstance(result, int)
def test_fibonacci():
    for i in range(10):
        result = fibonacci(i)
        assert isinstance(result, int)
def test_is_prime():
    for i in range(20):
        if is_prime(i):
            assert i > 1
        else:
            assert i <= 1
def test_find_gcd():
    for a in range(-10, 11):
        for b in range(-10, 11):
            result = find_gcd(a, b)
            assert isinstance(result, int)