"""
Formatting utilities for BizGuard.

Provides consistent number and text formatting across the application.
"""


def format_currency(value: float, symbol: str = "₹") -> str:
    """
    Format a number as Indian currency.
    
    Examples:
        format_currency(1234567.89) -> "₹12,34,567.89"
        format_currency(0) -> "₹0.00"
    """
    if value is None:
        return f"{symbol}0.00"
    
    # Use standard formatting for simplicity
    if abs(value) >= 10000000:  # 1 Crore
        return f"{symbol}{value / 10000000:,.2f} Cr"
    elif abs(value) >= 100000:  # 1 Lakh
        return f"{symbol}{value / 100000:,.2f} L"
    else:
        return f"{symbol}{value:,.2f}"


def format_number(value: float, decimals: int = 0) -> str:
    """Format a number with commas."""
    if value is None:
        return "0"
    if decimals == 0:
        return f"{int(value):,}"
    return f"{value:,.{decimals}f}"


def format_percentage(value: float, decimals: int = 1) -> str:
    """Format a decimal as percentage."""
    if value is None:
        return "0.0%"
    return f"{value * 100:.{decimals}f}%"


def format_change(value: float, prefix: str = "₹") -> str:
    """Format a change value with +/- sign and color indicator."""
    if value is None:
        return "—"
    sign = "+" if value > 0 else ""
    return f"{sign}{prefix}{value:,.2f}"


def format_change_pct(value: float) -> str:
    """Format a percentage change with +/- sign."""
    if value is None:
        return "—"
    sign = "+" if value > 0 else ""
    return f"{sign}{value:.1f}%"


def severity_emoji(severity: str) -> str:
    """Return an emoji for a severity level."""
    return {
        "error": "🔴",
        "warning": "🟡",
        "info": "🔵",
        "success": "🟢",
    }.get(severity, "⚪")
