from typing import Dict, Type, TypeVar, Any

T = TypeVar('T')

class ServiceLocator:
    """Service locator for dependency injection."""
    
    _services: Dict[Type, Any] = {}
    
    @classmethod
    def register(cls, interface_type: Type[T], implementation: T) -> None:
        """Register a service implementation for an interface.
        
        Args:
            interface_type: The interface/protocol type
            implementation: The concrete implementation
        """
        cls._services[interface_type] = implementation
        
    @classmethod
    def get(cls, interface_type: Type[T]) -> T:
        """Get a service implementation by its interface.
        
        Args:
            interface_type: The interface/protocol type
            
        Returns:
            The registered implementation
            
        Raises:
            KeyError: If no implementation is registered for the interface
        """
        if interface_type not in cls._services:
            raise KeyError(f"No implementation registered for {interface_type.__name__}")
        return cls._services[interface_type]
