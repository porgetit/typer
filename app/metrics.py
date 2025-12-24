"""Pure functions for computing typing metrics."""


class MetricsCalculator:
    """Encapsulates metric calculations to keep them easily testable."""

    @staticmethod
    def count_errors(typed: str, target: str) -> int:
        overlap = min(len(typed), len(target))
        errors = sum(1 for i in range(overlap) if typed[i] != target[i])
        errors += max(len(typed) - len(target), 0)
        return errors

    @staticmethod
    def accuracy(typed_length: int, errors: int) -> float:
        if typed_length <= 0:
            return 100.0
        correct = max(typed_length - errors, 0)
        return max(0.0, min(100.0, (correct / typed_length) * 100))

    @staticmethod
    def words_per_minute(char_count: int, elapsed_seconds: float) -> int:
        if elapsed_seconds <= 0:
            return 0
        words = char_count / 5  # industry convention
        return max(0, int(words / (elapsed_seconds / 60)))
