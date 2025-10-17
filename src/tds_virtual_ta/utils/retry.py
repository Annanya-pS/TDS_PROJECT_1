
import asyncio
import random
from typing import TypeVar, Callable, Type, Tuple
from functools import wraps
import logging

from ..config import settings

logger = logging.getLogger(__name__)

T = TypeVar('T')


def exponential_backoff(
    attempt: int,
    base: float = 1.0,
    factor: float = 2.0,
    max_delay: float = 60.0,
    jitter: bool = True
) -> float:
    """
    Calculate exponential backoff delay.
    
    Args:
        attempt: Attempt number (0-indexed)
        base: Base delay
        factor: Exponential factor
        max_delay: Maximum delay
        jitter: Add random jitter
    
    Returns:
        Delay in seconds
    """
    delay = min(base * (factor ** attempt), max_delay)
    
    if jitter:
        jitter_amount = delay * 0.25
        delay = delay + random.uniform(-jitter_amount, jitter_amount)
    
    return max(0, delay)


def retry_async(
    max_attempts: int = None,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    backoff_factor: float = None
):
    """
    Decorator for async functions with retry logic.
    
    Args:
        max_attempts: Max retry attempts
        exceptions: Exception types to retry on
        backoff_factor: Backoff multiplier
    """
    if max_attempts is None:
        max_attempts = settings.max_retries
    
    if backoff_factor is None:
        backoff_factor = settings.retry_backoff_factor
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts - 1:
                        logger.error(
                            f"{func.__name__} failed after {max_attempts} attempts: {e}"
                        )
                        raise
                    
                    delay = exponential_backoff(attempt, factor=backoff_factor)
                    
                    logger.warning(
                        f"{func.__name__} attempt {attempt + 1} failed, "
                        f"retrying in {delay:.2f}s: {e}"
                    )
                    
                    await asyncio.sleep(delay)
            
            raise last_exception
        
        return wrapper
    return decorator


def retry_sync(
    max_attempts: int = None,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    backoff_factor: float = None
):
    """
    Decorator for sync functions with retry logic.
    """
    if max_attempts is None:
        max_attempts = settings.max_retries
    
    if backoff_factor is None:
        backoff_factor = settings.retry_backoff_factor
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            import time
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts - 1:
                        logger.error(
                            f"{func.__name__} failed after {max_attempts} attempts"
                        )
                        raise
                    
                    delay = exponential_backoff(attempt, factor=backoff_factor)
                    logger.warning(
                        f"{func.__name__} attempt {attempt + 1} failed, "
                        f"retrying in {delay:.2f}s"
                    )
                    time.sleep(delay)
            
            raise last_exception
        
        return wrapper
    return decorator

