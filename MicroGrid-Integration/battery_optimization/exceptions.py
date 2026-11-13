"""
Custom exceptions for the MicroGrid Battery Optimization system.
"""


class OptimizationError(Exception):
    """
    Raised when the battery optimization process fails.

    This covers solver unavailability, infeasible problems,
    numerical issues, and other optimization-related failures.
    """
    pass


class ForecastError(Exception):
    """
    Raised when PV or load forecasting fails.

    This covers missing model artifacts, feature mismatch,
    API failures, and invalid forecast data.
    """
    pass


class ConfigurationError(Exception):
    """
    Raised when the system configuration is invalid or incomplete.

    This covers missing required parameters, out-of-range values,
    inconsistent settings, and schema validation errors.
    """
    pass
