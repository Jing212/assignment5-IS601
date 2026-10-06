import datetime
from decimal import Decimal

import pytest

from app.calculation import Calculation
from app.calculator_memento import CalculatorMemento


def make_calculation(operation="Addition", a="2", b="3"):
    return Calculation(
        operation=operation,
        operand1=Decimal(a),
        operand2=Decimal(b),
    )


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

def test_memento_stores_history_list():
    calc = make_calculation()
    memento = CalculatorMemento(history=[calc])
    assert memento.history == [calc]


def test_memento_default_timestamp_is_set_automatically():
    before = datetime.datetime.now()
    memento = CalculatorMemento(history=[])
    after = datetime.datetime.now()
    assert before <= memento.timestamp <= after


def test_memento_accepts_explicit_timestamp():
    ts = datetime.datetime(2026, 1, 1, 12, 0, 0)
    memento = CalculatorMemento(history=[], timestamp=ts)
    assert memento.timestamp == ts


def test_memento_with_empty_history():
    memento = CalculatorMemento(history=[])
    assert memento.history == []


def test_memento_with_multiple_calculations():
    calc1 = make_calculation("Addition", "1", "1")
    calc2 = make_calculation("Subtraction", "5", "3")
    memento = CalculatorMemento(history=[calc1, calc2])
    assert memento.history == [calc1, calc2]
    assert len(memento.history) == 2


# ---------------------------------------------------------------------------
# to_dict
# ---------------------------------------------------------------------------

def test_to_dict_contains_expected_keys():
    calc = make_calculation()
    memento = CalculatorMemento(history=[calc])
    data = memento.to_dict()
    assert set(data.keys()) == {"history", "timestamp"}


def test_to_dict_serializes_each_calculation():
    calc = make_calculation()
    memento = CalculatorMemento(history=[calc])
    data = memento.to_dict()
    assert data["history"] == [calc.to_dict()]


def test_to_dict_serializes_timestamp_as_isoformat_string():
    ts = datetime.datetime(2026, 6, 15, 9, 30, 0)
    memento = CalculatorMemento(history=[], timestamp=ts)
    data = memento.to_dict()
    assert data["timestamp"] == ts.isoformat()


def test_to_dict_with_empty_history():
    memento = CalculatorMemento(history=[])
    data = memento.to_dict()
    assert data["history"] == []


def test_to_dict_with_multiple_calculations():
    calc1 = make_calculation("Addition", "1", "1")
    calc2 = make_calculation("Multiplication", "4", "5")
    memento = CalculatorMemento(history=[calc1, calc2])
    data = memento.to_dict()
    assert data["history"] == [calc1.to_dict(), calc2.to_dict()]


# ---------------------------------------------------------------------------
# from_dict
# ---------------------------------------------------------------------------

def test_from_dict_restores_history():
    calc = make_calculation()
    data = {
        "history": [calc.to_dict()],
        "timestamp": datetime.datetime.now().isoformat(),
    }
    memento = CalculatorMemento.from_dict(data)
    assert len(memento.history) == 1
    assert memento.history[0].operation == calc.operation
    assert memento.history[0].operand1 == calc.operand1
    assert memento.history[0].operand2 == calc.operand2
    assert memento.history[0].result == calc.result


def test_from_dict_restores_timestamp():
    ts = datetime.datetime(2026, 3, 10, 8, 0, 0)
    data = {"history": [], "timestamp": ts.isoformat()}
    memento = CalculatorMemento.from_dict(data)
    assert memento.timestamp == ts


def test_from_dict_with_empty_history():
    data = {"history": [], "timestamp": datetime.datetime.now().isoformat()}
    memento = CalculatorMemento.from_dict(data)
    assert memento.history == []


def test_from_dict_with_multiple_calculations():
    calc1 = make_calculation("Addition", "1", "1")
    calc2 = make_calculation("Division", "10", "2")
    data = {
        "history": [calc1.to_dict(), calc2.to_dict()],
        "timestamp": datetime.datetime.now().isoformat(),
    }
    memento = CalculatorMemento.from_dict(data)
    assert len(memento.history) == 2
    assert memento.history[0] == calc1
    assert memento.history[1] == calc2


def test_from_dict_raises_on_malformed_calculation_data():
    data = {
        "history": [
            {
                "operation": "Addition",
                "operand1": "invalid",
                "operand2": "3",
                "result": "5",
                "timestamp": datetime.datetime.now().isoformat(),
            }
        ],
        "timestamp": datetime.datetime.now().isoformat(),
    }
    from app.exceptions import OperationError

    with pytest.raises(OperationError, match="Invalid calculation data"):
        CalculatorMemento.from_dict(data)


def test_from_dict_raises_on_missing_history_key():
    data = {"timestamp": datetime.datetime.now().isoformat()}
    with pytest.raises(KeyError):
        CalculatorMemento.from_dict(data)


def test_from_dict_raises_on_missing_timestamp_key():
    data = {"history": []}
    with pytest.raises(KeyError):
        CalculatorMemento.from_dict(data)


# ---------------------------------------------------------------------------
# Round-trip (to_dict -> from_dict)
# ---------------------------------------------------------------------------

def test_round_trip_preserves_history_and_timestamp():
    calc1 = make_calculation("Addition", "2", "3")
    calc2 = make_calculation("Power", "2", "3")
    original = CalculatorMemento(history=[calc1, calc2])

    restored = CalculatorMemento.from_dict(original.to_dict())

    assert restored.timestamp == original.timestamp
    assert restored.history == original.history


def test_round_trip_with_empty_history():
    original = CalculatorMemento(history=[])
    restored = CalculatorMemento.from_dict(original.to_dict())
    assert restored.history == []
    assert restored.timestamp == original.timestamp
