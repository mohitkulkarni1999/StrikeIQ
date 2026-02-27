"""
Symbol-scoped LiveOptionChainBuilder Registry
Ensures SINGLE builder instance per symbol
"""

from typing import Dict
from app.services.live_option_chain_builder import LiveOptionChainBuilder

# 🔥 SYMBOL SCOPED INSTANCE STORE
_builder_instances: Dict[str, LiveOptionChainBuilder] = {}


def get_live_chain_builder(symbol: str) -> LiveOptionChainBuilder:
    """
    Returns SAME builder instance per symbol.
    Prevents dual instance ingestion bug.
    """
    symbol = symbol.upper()

    if symbol not in _builder_instances:
        _builder_instances[symbol] = LiveOptionChainBuilder()

    return _builder_instances[symbol]