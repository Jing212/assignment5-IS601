from decimal import Decimal
from unittest.mock import MagicMock, patch, call

import pytest

from app.calculator import Calculator
from app.calculator_repl import calculator_repl
from app.exceptions import OperationError, ValidationError
from app.operations import Addition


@pytest.fixture
def mock_calc():
    """A MagicMock standing in for the real Calculator, with spec=Calculator
    so isinstance() checks inside AutoSaveObserver/etc. still pass."""
    calc = MagicMock(spec=Calculator)
    calc.show_history.return_value = []
    return calc


def run_repl(monkeypatch, mock_calc, inputs):
    """Patch builtins.input with a scripted sequence of responses, patch
    app.calculator_repl.Calculator to return mock_calc, and run the REPL
    to completion (the input sequence must end in a way that exits the
    loop, e.g. with 'exit' or by running out of inputs to trigger EOFError).
    """
    input_iter = iter(inputs)

    def fake_input(prompt=""):
        try:
            return next(input_iter)
        except StopIteration:
            raise EOFError

    monkeypatch.setattr("builtins.input", fake_input)
    with patch("app.calculator_repl.Calculator", return_value=mock_calc):
        calculator_repl()


# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------

def test_repl_prints_welcome_message(monkeypatch, mock_calc, capsys):
    run_repl(monkeypatch, mock_calc, ["exit"])
    out = capsys.readouterr().out
    assert "Calculator started. Type 'help' for commands." in out


def test_repl_registers_logging_and_autosave_observers(monkeypatch, mock_calc, capsys):
    run_repl(monkeypatch, mock_calc, ["exit"])
    assert mock_calc.add_observer.call_count == 2


def test_repl_fatal_error_during_init_is_reported_and_reraised(monkeypatch, capsys):
    monkeypatch.setattr("builtins.input", MagicMock())
    with patch("app.calculator_repl.Calculator", side_effect=RuntimeError("boom")):
        with pytest.raises(RuntimeError, match="boom"):
            calculator_repl()
    out = capsys.readouterr().out
    assert "Fatal error: boom" in out


# ---------------------------------------------------------------------------
# help / exit / unknown command
# ---------------------------------------------------------------------------

def test_repl_help_command_lists_commands(monkeypatch, mock_calc, capsys):
    run_repl(monkeypatch, mock_calc, ["help", "exit"])
    out = capsys.readouterr().out
    assert "Available commands:" in out
    assert "add, subtract, multiply, divide, power, root" in out


def test_repl_exit_saves_history_and_says_goodbye(monkeypatch, mock_calc, capsys):
    run_repl(monkeypatch, mock_calc, ["exit"])
    mock_calc.save_history.assert_called_once()
    out = capsys.readouterr().out
    assert "History saved successfully." in out
    assert "Goodbye!" in out


def test_repl_exit_save_failure_still_exits_with_warning(monkeypatch, mock_calc, capsys):
    mock_calc.save_history.side_effect = OperationError("disk full")
    run_repl(monkeypatch, mock_calc, ["exit"])
    out = capsys.readouterr().out
    assert "Warning: Could not save history: disk full" in out
    assert "Goodbye!" in out


def test_repl_unknown_command(monkeypatch, mock_calc, capsys):
    run_repl(monkeypatch, mock_calc, ["frobnicate", "exit"])
    out = capsys.readouterr().out
    assert "Unknown command: 'frobnicate'. Type 'help' for available commands." in out


def test_repl_command_is_case_and_whitespace_insensitive(monkeypatch, mock_calc, capsys):
    run_repl(monkeypatch, mock_calc, ["  EXIT  "])
    out = capsys.readouterr().out
    assert "Goodbye!" in out


# ---------------------------------------------------------------------------
# history / clear
# ---------------------------------------------------------------------------

def test_repl_history_command_when_empty(monkeypatch, mock_calc, capsys):
    mock_calc.show_history.return_value = []
    run_repl(monkeypatch, mock_calc, ["history", "exit"])
    out = capsys.readouterr().out
    assert "No calculations in history" in out


def test_repl_history_command_lists_entries(monkeypatch, mock_calc, capsys):
    mock_calc.show_history.return_value = ["Addition(2, 3) = 5", "Subtraction(5, 2) = 3"]
    run_repl(monkeypatch, mock_calc, ["history", "exit"])
    out = capsys.readouterr().out
    assert "1. Addition(2, 3) = 5" in out
    assert "2. Subtraction(5, 2) = 3" in out


def test_repl_clear_command(monkeypatch, mock_calc, capsys):
    run_repl(monkeypatch, mock_calc, ["clear", "exit"])
    mock_calc.clear_history.assert_called_once()
    out = capsys.readouterr().out
    assert "History cleared" in out


# ---------------------------------------------------------------------------
# undo / redo
# ---------------------------------------------------------------------------

def test_repl_undo_success(monkeypatch, mock_calc, capsys):
    mock_calc.undo.return_value = True
    run_repl(monkeypatch, mock_calc, ["undo", "exit"])
    out = capsys.readouterr().out
    assert "Operation undone" in out


def test_repl_undo_nothing_to_undo(monkeypatch, mock_calc, capsys):
    mock_calc.undo.return_value = False
    run_repl(monkeypatch, mock_calc, ["undo", "exit"])
    out = capsys.readouterr().out
    assert "Nothing to undo" in out


def test_repl_redo_success(monkeypatch, mock_calc, capsys):
    mock_calc.redo.return_value = True
    run_repl(monkeypatch, mock_calc, ["redo", "exit"])
    out = capsys.readouterr().out
    assert "Operation redone" in out


def test_repl_redo_nothing_to_redo(monkeypatch, mock_calc, capsys):
    mock_calc.redo.return_value = False
    run_repl(monkeypatch, mock_calc, ["redo", "exit"])
    out = capsys.readouterr().out
    assert "Nothing to redo" in out


# ---------------------------------------------------------------------------
# save / load
# ---------------------------------------------------------------------------

def test_repl_save_command_success(monkeypatch, mock_calc, capsys):
    run_repl(monkeypatch, mock_calc, ["save", "exit"])
    out = capsys.readouterr().out
    assert "History saved successfully" in out


def test_repl_save_command_failure(monkeypatch, mock_calc, capsys):
    mock_calc.save_history.side_effect = [OperationError("permission denied"), None]
    run_repl(monkeypatch, mock_calc, ["save", "exit"])
    out = capsys.readouterr().out
    assert "Error saving history: permission denied" in out


def test_repl_load_command_success(monkeypatch, mock_calc, capsys):
    run_repl(monkeypatch, mock_calc, ["load", "exit"])
    mock_calc.load_history.assert_called_once()
    out = capsys.readouterr().out
    assert "History loaded successfully" in out


def test_repl_load_command_failure(monkeypatch, mock_calc, capsys):
    mock_calc.load_history.side_effect = OperationError("corrupt file")
    run_repl(monkeypatch, mock_calc, ["load", "exit"])
    out = capsys.readouterr().out
    assert "Error loading history: corrupt file" in out


# ---------------------------------------------------------------------------
# performing calculations
# ---------------------------------------------------------------------------

def test_repl_performs_addition(monkeypatch, mock_calc, capsys):
    mock_calc.perform_operation.return_value = Decimal("5")
    run_repl(monkeypatch, mock_calc, ["add", "2", "3", "exit"])

    mock_calc.set_operation.assert_called_once()
    assert isinstance(mock_calc.set_operation.call_args.args[0], Addition)
    mock_calc.perform_operation.assert_called_once_with("2", "3")

    out = capsys.readouterr().out
    assert "Result: 5" in out


def test_repl_normalizes_decimal_result(monkeypatch, mock_calc, capsys):
    mock_calc.perform_operation.return_value = Decimal("8.00")
    run_repl(monkeypatch, mock_calc, ["multiply", "4", "2", "exit"])
    out = capsys.readouterr().out
    assert "Result: 8" in out
    assert "Result: 8.00" not in out


def test_repl_non_decimal_result_is_printed_as_is(monkeypatch, mock_calc, capsys):
    mock_calc.perform_operation.return_value = "n/a"
    run_repl(monkeypatch, mock_calc, ["divide", "1", "2", "exit"])
    out = capsys.readouterr().out
    assert "Result: n/a" in out


def test_repl_calculation_cancelled_on_first_number(monkeypatch, mock_calc, capsys):
    run_repl(monkeypatch, mock_calc, ["add", "cancel", "exit"])
    mock_calc.perform_operation.assert_not_called()
    out = capsys.readouterr().out
    assert "Operation cancelled" in out


def test_repl_calculation_cancelled_on_second_number(monkeypatch, mock_calc, capsys):
    run_repl(monkeypatch, mock_calc, ["add", "2", "cancel", "exit"])
    mock_calc.perform_operation.assert_not_called()
    out = capsys.readouterr().out
    assert "Operation cancelled" in out


def test_repl_cancel_is_case_insensitive(monkeypatch, mock_calc, capsys):
    run_repl(monkeypatch, mock_calc, ["add", "CANCEL", "exit"])
    mock_calc.perform_operation.assert_not_called()
    out = capsys.readouterr().out
    assert "Operation cancelled" in out


def test_repl_validation_error_is_reported(monkeypatch, mock_calc, capsys):
    mock_calc.perform_operation.side_effect = ValidationError("Invalid number format: abc")
    run_repl(monkeypatch, mock_calc, ["add", "abc", "3", "exit"])
    out = capsys.readouterr().out
    assert "Error: Invalid number format: abc" in out


def test_repl_operation_error_is_reported(monkeypatch, mock_calc, capsys):
    mock_calc.perform_operation.side_effect = OperationError("Division by zero is not allowed")
    run_repl(monkeypatch, mock_calc, ["divide", "5", "0", "exit"])
    out = capsys.readouterr().out
    assert "Error: Division by zero is not allowed" in out


def test_repl_unexpected_error_during_calculation_is_caught(monkeypatch, mock_calc, capsys):
    mock_calc.perform_operation.side_effect = RuntimeError("something broke")
    run_repl(monkeypatch, mock_calc, ["add", "2", "3", "exit"])
    out = capsys.readouterr().out
    assert "Unexpected error: something broke" in out


@pytest.mark.parametrize(
    "command,op_class_name",
    [
        ("add", "Addition"),
        ("subtract", "Subtraction"),
        ("multiply", "Multiplication"),
        ("divide", "Division"),
        ("power", "Power"),
        ("root", "Root"),
    ],
)
def test_repl_each_operation_creates_matching_strategy(
    monkeypatch, mock_calc, capsys, command, op_class_name
):
    mock_calc.perform_operation.return_value = Decimal("1")
    run_repl(monkeypatch, mock_calc, [command, "1", "1", "exit"])
    created_operation = mock_calc.set_operation.call_args.args[0]
    assert created_operation.__class__.__name__ == op_class_name


# ---------------------------------------------------------------------------
# KeyboardInterrupt / EOFError handling inside the loop
# ---------------------------------------------------------------------------

def test_repl_keyboard_interrupt_is_caught_and_loop_continues(monkeypatch, mock_calc, capsys):
    calls = {"count": 0}

    def fake_input(prompt=""):
        calls["count"] += 1
        if calls["count"] == 1:
            raise KeyboardInterrupt
        return "exit"

    monkeypatch.setattr("builtins.input", fake_input)
    with patch("app.calculator_repl.Calculator", return_value=mock_calc):
        calculator_repl()

    out = capsys.readouterr().out
    assert "Operation cancelled" in out
    assert "Goodbye!" in out


def test_repl_eof_error_breaks_the_loop(monkeypatch, mock_calc, capsys):
    monkeypatch.setattr("builtins.input", MagicMock(side_effect=EOFError))
    with patch("app.calculator_repl.Calculator", return_value=mock_calc):
        calculator_repl()
    out = capsys.readouterr().out
    assert "Input terminated. Exiting..." in out


def test_repl_unexpected_exception_in_loop_is_caught_and_continues(monkeypatch, mock_calc, capsys):
    # First "command" raises a generic exception inside the try block (e.g.
    # show_history() blowing up), second input exits cleanly.
    mock_calc.show_history.side_effect = RuntimeError("unexpected")
    run_repl(monkeypatch, mock_calc, ["history", "exit"])
    out = capsys.readouterr().out
    assert "Error: unexpected" in out
    assert "Goodbye!" in out