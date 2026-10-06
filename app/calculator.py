########################
# Calculator Class      #
########################

from decimal import Decimal
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd

from app.calculation import Calculation
from app.calculator_config import CalculatorConfig
from app.calculator_memento import CalculatorMemento
from app.exceptions import OperationError, ValidationError
from app.history import HistoryObserver
from app.input_validators import InputValidator
from app.operations import Operation

# Type aliases for better readability
Number = Union[int, float, Decimal]
CalculationResult = Union[Number, str]


class Calculator:
    """
    Main calculator class implementing multiple design patterns.

    This class serves as the core of the calculator application, managing operations,
    calculation history, observers, configuration settings, and data persistence.
    It integrates various design patterns to enhance flexibility, maintainability, and
    scalability.
    """

    def __init__(self, config: Optional[CalculatorConfig] = None):
        """
        Initialize calculator with configuration.

        Args:
            config (Optional[CalculatorConfig], optional): Configuration settings for the calculator.
                If not provided, default settings are loaded based on environment variables.
        """
        if config is None:
            # Determine the project root directory if no configuration is provided
            current_file = Path(__file__)
            project_root = current_file.parent.parent
            config = CalculatorConfig(base_dir=project_root)

        # Assign the configuration and validate its parameters
        self.config = config
        self.config.validate()

        # Ensure that the log directory exists
        os.makedirs(self.config.log_dir, exist_ok=True)

        # Set up the logging system
        self._setup_logging()

        # Initialize calculation history and operation strategy
        self.history: List[Calculation] = []
        self.operation_strategy: Optional[Operation] = None

        # Initialize observer list for the Observer pattern
        self.observers: List[HistoryObserver] = []

        # Initialize stacks for undo and redo functionality using the Memento pattern
        self.undo_stack: List[CalculatorMemento] = []
        self.redo_stack: List[CalculatorMemento] = []

        # Create required directories for history management
        self._setup_directories()

        try:
            # Attempt to load existing calculation history from file
            self.load_history()
        except Exception as e: # pragma: no cover
            # Log a warning if history could not be loaded
            logging.warning(f"Could not load existing history: {e}") # pragma: no cover

        # Log the successful initialization of the calculator
        logging.info("Calculator initialized with configuration")

    def _setup_logging(self) -> None:
        """
        Configure the logging system.

        Sets up logging to a file with a specified format and log level.
        """
        try:
            # Ensure the log directory exists
            os.makedirs(self.config.log_dir, exist_ok=True)
            log_file = self.config.log_file.resolve()

            # Configure the basic logging settings
            logging.basicConfig(
                filename=str(log_file),
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s',
                force=True  # Overwrite any existing logging configuration
            )
            logging.info(f"Logging initialized at: {log_file}")
        except Exception as e:  # pragma: no cover
            # Print an error message and re-raise the exception if logging setup fails
            print(f"Error setting up logging: {e}")
            raise  # pragma: no cover

    def _setup_directories(self) -> None:
        """
        Create required directories.

        Ensures that all necessary directories for history management exist.
        """
        self.config.history_dir.mkdir(parents=True, exist_ok=True)

    def add_observer(self, observer: HistoryObserver) -> None:
        """
        Register a new observer.

        Args:
            observer (HistoryObserver): The observer to be added.
        """
        self.observers.append(observer)
        logging.info(f"Added observer: {observer.__class__.__name__}")

    def register_observer(self, observer: HistoryObserver) -> None:
        """Alias for add_observer to support REPL observer registration."""
        self.add_observer(observer)  # pragma: no cover

    def remove_observer(self, observer: HistoryObserver) -> None:
        """
        Remove an existing observer.

        Args:
            observer (HistoryObserver): The observer to be removed.
        """
        self.observers.remove(observer)
        logging.info(f"Removed observer: {observer.__class__.__name__}")

    def notify_observers(self, calculation: Calculation) -> None:
        """
        Notify all observers of a new calculation.

        Args:
            calculation (Calculation): The latest calculation performed.
        """
        for observer in self.observers:
            observer.update(calculation)

    def set_operation(self, operation: Operation) -> None:
        """
        Set the current operation strategy.

        Args:
            operation (Operation): The operation strategy to be set.
        """
        self.operation_strategy = operation
        logging.info(f"Set operation: {operation}")

    def perform_operation(
        self,
        a: Union[str, Number],
        b: Union[str, Number]
    ) -> CalculationResult:
        """
        Perform calculation with the current operation.

        Args:
            a (Union[str, Number]): The first operand.
            b (Union[str, Number]): The second operand.

        Returns:
            CalculationResult: The result of the calculation.
        """
        if not self.operation_strategy:
            raise OperationError("No operation set")

        try:
            # Validate and convert inputs to Decimal
            validated_a = InputValidator.validate_number(a, self.config)
            validated_b = InputValidator.validate_number(b, self.config)

            # Execute the operation strategy
            result = self.operation_strategy.execute(validated_a, validated_b)

            # Create a new Calculation instance with the operation details
            calculation = Calculation(
                operation=str(self.operation_strategy),
                operand1=validated_a,
                operand2=validated_b
            )

            # Save current state to undo stack
            self.undo_stack.append(CalculatorMemento(self.history.copy()))
            self.redo_stack.clear()

            # Append new calculation
            self.history.append(calculation)

            # Enforce max history size
            if len(self.history) > self.config.max_history_size:
                self.history.pop(0)  # pragma: no cover

            # Notify observers
            self.notify_observers(calculation)

            return result

        except ValidationError as e:
            logging.error(f"Validation error: {str(e)}")
            raise
        except Exception as e:  # pragma: no cover
            logging.error(f"Operation failed: {str(e)}")
            raise OperationError(f"Operation failed: {str(e)}")  # pragma: no cover

    def save_history(self, file_path: Optional[Union[str, Path]] = None) -> None:
        """
        Save calculation history to a CSV file using pandas.

        Args:
            file_path (Optional[Union[str, Path]], optional): Target file path.
                If None, uses self.config.history_file.
        """
        target_file = Path(file_path) if file_path else self.config.history_file
        try:
            target_file.parent.mkdir(parents=True, exist_ok=True)

            history_data = []
            for calc in self.history:
                history_data.append({
                    'operation': str(calc.operation),
                    'operand1': str(calc.operand1),
                    'operand2': str(calc.operand2),
                    'result': str(calc.result),
                    'timestamp': calc.timestamp.isoformat() if hasattr(calc.timestamp, 'isoformat') else str(calc.timestamp)
                })

            if history_data:
                df = pd.DataFrame(history_data)
                df.to_csv(target_file, index=False)
                logging.info(f"History saved successfully to {target_file}")
            else: # pragma: no cover
                pd.DataFrame(columns=['operation', 'operand1', 'operand2', 'result', 'timestamp']
                           ).to_csv(target_file, index=False)
                logging.info("Empty history saved")

        except Exception as e: # pragma: no cover
            logging.error(f"Failed to save history: {e}") # pragma: no cover
            raise OperationError(f"Failed to save history: {e}") # pragma: no cover

    def load_history(self, file_path: Optional[Union[str, Path]] = None) -> None:
        """
        Load calculation history from a CSV file using pandas.

        Args:
            file_path (Optional[Union[str, Path]], optional): Target file path.
                If None, uses self.config.history_file.
        """
        target_file = Path(file_path) if file_path else self.config.history_file
        try:
            if target_file.exists():
                df = pd.read_csv(target_file)
                if not df.empty:
                    self.history = [
                        Calculation.from_dict({
                            'operation': row['operation'],
                            'operand1': row['operand1'],
                            'operand2': row['operand2'],
                            'result': row['result'],
                            'timestamp': row['timestamp']
                        })
                        for _, row in df.iterrows()
                    ]
                    logging.info(f"Loaded {len(self.history)} calculations from history")
                else:
                    logging.info("Loaded empty history file") # pragma: no cover
            else:
                logging.info("No history file found - starting with empty history")
        except Exception as e: # pragma: no cover
            logging.error(f"Failed to load history: {e}")
            raise OperationError(f"Failed to load history: {e}") # pragma: no cover

    def get_history_dataframe(self) -> pd.DataFrame:
        """Get calculation history as a pandas DataFrame."""
        history_data = [] # pragma: no cover
        for calc in self.history: # pragma: no cover
            history_data.append({ # pragma: no cover
                'operation': str(calc.operation),
                'operand1': str(calc.operand1),
                'operand2': str(calc.operand2),
                'result': str(calc.result),
                'timestamp': calc.timestamp
            })
        return pd.DataFrame(history_data)  # pragma: no cover

    def show_history(self) -> List[str]:
        """Get formatted history of calculations."""
        return [ # pragma: no cover
            f"{calc.operation}({calc.operand1}, {calc.operand2}) = {calc.result}"
            for calc in self.history
        ]

    def clear_history(self) -> None:
        """Clear calculation history and Memento stacks."""
        self.history.clear()
        self.undo_stack.clear()
        self.redo_stack.clear()
        logging.info("History cleared")

    def undo(self) -> bool:
        """Undo the last operation."""
        if not self.undo_stack:
            return False # pragma: no cover
        memento = self.undo_stack.pop()
        self.redo_stack.append(CalculatorMemento(self.history.copy()))
        self.history = memento.history.copy()
        return True

    def redo(self) -> bool:
        """Redo the previously undone operation."""
        if not self.redo_stack:
            return False # pragma: no cover
        memento = self.redo_stack.pop()
        self.undo_stack.append(CalculatorMemento(self.history.copy()))
        self.history = memento.history.copy()
        return True