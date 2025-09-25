"""
STT Provider Factory.

This factory creates the appropriate STT repository based on configuration,
using Gladia as the primary STT provider.
"""

import os
import logging
from typing import Optional

from .gladia_api_repository import GladiaAPIRepository

logger = logging.getLogger(__name__)


class STTProviderFactory:
    """Factory for creating STT providers based on configuration."""
    
    SUPPORTED_PROVIDERS = {
        'gladia': 'Gladia STT API',
    }
    
    @classmethod
    def create_provider(cls, provider_name: Optional[str] = None) -> GladiaAPIRepository:
        """
        Create STT provider based on configuration.
        
        Args:
            provider_name: Override provider name, otherwise uses environment
            
        Returns:
            Configured STT provider repository
        """
        # Get provider from environment or parameter
        provider = provider_name or os.getenv('STT_PROVIDER', 'gladia').lower()
        
        if provider not in cls.SUPPORTED_PROVIDERS:
            logger.warning(
                f"Unsupported STT provider '{provider}'. "
                f"Supported: {list(cls.SUPPORTED_PROVIDERS.keys())}. "
                f"Defaulting to 'gladia'."
            )
            provider = 'gladia'
        
        logger.info(f"Creating STT provider: {cls.SUPPORTED_PROVIDERS[provider]}")
        
        return cls._create_gladia_provider()
    
    @classmethod
    def _create_gladia_provider(cls) -> GladiaAPIRepository:
        """Create Gladia provider (existing implementation)."""
        # Import here to avoid circular imports
        from .gladia_api_repository_impl import GladiaAPIRepositoryImpl, MockGladiaAPIRepository
        
        api_key = os.getenv('GLADIA_API_KEY')
        
        if not api_key or api_key == 'your_gladia_api_key_here':
            logger.warning("No valid Gladia API key found, using mock provider")
            return MockGladiaAPIRepository()
        
        logger.info("Creating real Gladia provider")
        return GladiaAPIRepositoryImpl(api_key)
    
    @classmethod
    def get_provider_info(cls) -> dict:
        """Get information about current provider configuration."""
        current_provider = os.getenv('STT_PROVIDER', 'gladia').lower()
        
        provider_info = {
            'current_provider': current_provider,
            'provider_name': cls.SUPPORTED_PROVIDERS.get(current_provider, 'Unknown'),
            'supported_providers': cls.SUPPORTED_PROVIDERS,
            'has_api_key': False,
            'is_mock': True
        }
        
        # Check if API key is configured
        if current_provider == 'gladia':
            api_key = os.getenv('GLADIA_API_KEY')
            provider_info['has_api_key'] = bool(api_key and api_key != 'your_gladia_api_key_here')
            provider_info['is_mock'] = not provider_info['has_api_key']
            
        return provider_info
    
    @classmethod
    def validate_configuration(cls) -> dict:
        """Validate current STT provider configuration."""
        provider_info = cls.get_provider_info()
        validation_result = {
            'is_valid': True,
            'warnings': [],
            'errors': [],
            'recommendations': []
        }
        
        current_provider = provider_info['current_provider']
        
        # Check if provider is supported
        if current_provider not in cls.SUPPORTED_PROVIDERS:
            validation_result['is_valid'] = False
            validation_result['errors'].append(
                f"Unsupported provider '{current_provider}'. "
                f"Supported: {list(cls.SUPPORTED_PROVIDERS.keys())}"
            )
        
        # Check API key configuration
        if not provider_info['has_api_key']:
            validation_result['warnings'].append(
                f"No API key configured for {current_provider}, using mock provider"
            )
            validation_result['recommendations'].append(
                f"Set {current_provider.upper()}_API_KEY environment variable for production use"
            )
        
        # Provider-specific recommendations
        if current_provider == 'gladia':
            validation_result['recommendations'].append(
                "Gladia STT provider configured - good choice for speech-to-text processing"
            )
            
        return validation_result


def get_stt_provider() -> GladiaAPIRepository:
    """Convenience function to get configured STT provider."""
    return STTProviderFactory.create_provider()


def get_provider_status() -> dict:
    """Convenience function to get provider status information."""
    factory = STTProviderFactory()
    provider_info = factory.get_provider_info()
    validation = factory.validate_configuration()
    
    return {
        'provider_info': provider_info,
        'validation': validation,
        'ready_for_production': validation['is_valid'] and provider_info['has_api_key']
    }