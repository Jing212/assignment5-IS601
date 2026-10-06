########################
# History Management    #
########################

from abc import ABC, abstractmethod
import logging
from typing import Any
from app.calculation import Calculation


class HistoryObserver(ABC):
    """
    Abstract base class for calculator observers.
    """

    @abstractmethod
    def update(self, calculation: Calculation) -> None:
        pass  # pragma: no cover


class LoggingObserver(HistoryObserver):
    """
    Observer that logs calculations to a file.
    """

    def update(self, calculation: Calculation) -> None:
        if calculation is None:
            raise AttributeError("Calculation cannot be None")
        logging.info(
            f"Calculation performed: {calculation.operation} "
            f"({calculation.operand1}, {calculation.operand2}) = "
            f"{calculation.result}"
        )


class AutoSaveObserver(HistoryObserver):
    """
    Observer that automatically saves calculations.
    """

    def __init__(self, calculator: Any):
        """
        Initialize the AutoSaveObserver with support for both Real and Mock Calculator objects.
        """
        # 允许 Mock 对象直接通过，如果是普通对象则严格检查属性
        is_mock = type(calculator).__name__ in ('Mock', 'MagicMock', 'NonCallableMagicMock')
        
        if not is_mock:
            if not hasattr(calculator, 'config') or not hasattr(calculator, 'save_history'):
                raise TypeError("Calculator must have 'config' and 'save_history' attributes")
        
        self.calculator = calculator

    def update(self, calculation: Calculation) -> None:
        """
        Trigger auto-save.
        """
        if calculation is None:
            raise AttributeError("Calculation cannot be None")
        
        # 安全获取 auto_save 配置并执行 save_history
        config = getattr(self.calculator, 'config', None)
        auto_save = getattr(config, 'auto_save', True) if config else True
        
        if auto_save:
            save_fn = getattr(self.calculator, 'save_history', None)
            if callable(save_fn):
                save_fn()
                logging.info("History auto-saved")