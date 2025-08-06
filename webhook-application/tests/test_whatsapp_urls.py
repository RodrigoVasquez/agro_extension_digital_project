"""
Test simple para verificar la configuración de URLs de WhatsApp.
"""
import sys
import os
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_whatsapp_urls():
    """Test the WhatsApp URL configuration."""
    print("🧪 Testing WhatsApp URL Configuration")
    print("=" * 40)
    
    from whatsapp_webhook.utils.config import get_whatsapp_api_url, get_whatsapp_config
    
    # Test AA
    print("📱 App AA:")
    url_aa = get_whatsapp_api_url('AA')
    print(f"   URL: {url_aa}")
    
    # Test PP
    print("📱 App PP:")
    url_pp = get_whatsapp_api_url('PP')
    print(f"   URL: {url_pp}")
    
    # Test complete config
    print("\n📊 Complete configurations:")
    config_aa = get_whatsapp_config('AA')
    config_pp = get_whatsapp_config('PP')
    
    print(f"AA Config: {config_aa}")
    print(f"PP Config: {config_pp}")
    
    # Verify URLs are correct
    expected_aa = "https://graph.facebook.com/v22.0/692894087240362"
    expected_pp = "https://graph.facebook.com/v22.0/619189944620159"
    
    print(f"\n✅ Verification:")
    print(f"AA URL correct: {url_aa == expected_aa} (expected: {expected_aa})")
    print(f"PP URL correct: {url_pp == expected_pp} (expected: {expected_pp})")
    
    return url_aa, url_pp

if __name__ == "__main__":
    test_whatsapp_urls()
