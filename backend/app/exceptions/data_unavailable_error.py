"""
Data Availability Exceptions

Raised when analytics engines cannot calculate meaningful metrics
due to missing or insufficient market data.
"""

class DataUnavailableError(Exception):
    """Exception raised when market data is insufficient for analytics calculations."""
    pass


class InsufficientDataError(DataUnavailableError):
    """Exception raised when there's not enough data for reliable calculations."""
    pass


class MissingATMError(DataUnavailableError):
    """Exception raised when ATM strike data is unavailable."""
    pass


class MissingOIError(DataUnavailableError):
    """Exception raised when Open Interest data is missing."""
    pass


class MissingPremiumError(DataUnavailableError):
    """Exception raised when premium data is missing for calculations."""
    pass
