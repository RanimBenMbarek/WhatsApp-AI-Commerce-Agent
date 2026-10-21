
class CartServiceError(Exception):
    """Base exception for cart business-rule errors."""


class CartNotFoundError(CartServiceError):
    """Raised when a cart or cart item cannot be found."""


class VariantUnavailableError(CartServiceError):
    """Raised when a product variant or its product is unavailable."""


class InsufficientStockError(CartServiceError):
    """Raised when verified stock cannot satisfy the requested quantity."""


class InvalidQuantityError(CartServiceError):
    """Raised when a quantity is less than one."""
