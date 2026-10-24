
class OrderServiceError(Exception):
    """Base exception for order business-rule errors."""


class EmptyCartError(OrderServiceError):
    """Raised when checkout is attempted with an empty cart."""


class OrderNotFoundError(OrderServiceError):
    """Raised when an order cannot be found for the customer."""


class InvalidShippingAddressError(OrderServiceError):
    """Raised when the shipping address is invalid."""


class CheckoutNotReadyError(OrderServiceError):
    """Raised when checkout cannot proceed with the current catalog data."""


class CheckoutConfirmationError(OrderServiceError):
    """Raised when checkout confirmation is missing or invalid."""


class InvalidOrderStateError(OrderServiceError):
    """Raised when an order operation is invalid for its current status."""


class DemoCatalogDataError(OrderServiceError):
    """Raised when demo prices or stock prevent real order creation."""


class InvalidShippingFeeError(OrderServiceError):
    """Raised when the shipping fee is invalid."""


class CheckoutNotConfirmedError(OrderServiceError):
    """Raised when checkout has not been explicitly confirmed."""

