"""
Test script for CRTM Python interface.
Tests basic functionality and provides example usage.
"""

import os
import sys
import numpy as np
from crtm_interface import CRTM, CRTMAtmosphere, CRTMSurface, load_test_profile

def test_initialization():
    """Test CRTM initialization with various coefficient paths"""
    print("\nTesting CRTM initialization...")
    
    # Test with environment variable
    original_path = os.environ.get('CRTM_COEFFS_PATH')
    os.environ['CRTM_COEFFS_PATH'] = './fix'
    try:
        crtm = CRTM()
        print("✓ Initialization with CRTM_COEFFS_PATH successful")
    except Exception as e:
        print(f"✗ Initialization with CRTM_COEFFS_PATH failed: {e}")
    finally:
        if original_path:
            os.environ['CRTM_COEFFS_PATH'] = original_path
        else:
            del os.environ['CRTM_COEFFS_PATH']
    
    # Test with default paths
    try:
        crtm = CRTM()
        print("✓ Initialization with default paths successful")
    except Exception as e:
        print(f"✗ Initialization with default paths failed: {e}")

def test_profile_loading():
    """Test loading of atmospheric profiles"""
    print("\nTesting profile loading...")
    
    # Test default profile creation
    try:
        atm, sfc, geo = load_test_profile()
        print("✓ Default profile creation successful")
        print(f"  Atmosphere layers: {atm.n_layers}")
        print(f"  Number of absorbers: {atm.n_absorbers}")
    except Exception as e:
        print(f"✗ Default profile creation failed: {e}")
    
    # Test YAML profile loading
    try:
        atm, sfc, geo = load_test_profile("testinput/single_profile.yaml")
        print("✓ YAML profile loading successful")
    except Exception as e:
        print(f"✗ YAML profile loading failed: {e}")

def test_forward_model():
    """Test CRTM forward model calculation"""
    print("\nTesting forward model calculation...")
    
    try:
        # Create a simple profile
        atm = CRTMAtmosphere(
            n_layers=92,
            n_absorbers=2,
            absorber_id=np.array([1, 2]),
            absorber=np.ones((92, 2)) * 1e-6,  # Simple constant mixing ratio
            temperature=np.linspace(300, 200, 92),
            pressure=np.logspace(5, 2, 92)
        )
        
        sfc = CRTMSurface(
            land_coverage=1.0,
            water_coverage=0.0,
            snow_coverage=0.0,
            ice_coverage=0.0,
            land_temperature=288.0,
            water_temperature=288.0,
            snow_temperature=273.0,
            ice_temperature=273.0
        )
        
        geo = {
            "sensor_zenith_angle": 30.0,
            "sensor_azimuth_angle": 180.0,
            "sensor_height": 800000.0
        }
        
        # Run forward model
        with CRTM() as crtm:
            crtm.initialize(sensor_ids=["atms_n21"])
            results = crtm.forward(atm, sfc, geo)
            
            # Check results
            if 'brightness_temp' in results and 'radiance' in results:
                print("✓ Forward calculation successful")
                print(f"  Number of channels: {len(results['brightness_temp'])}")
                print(f"  Brightness temperature range: {results['brightness_temp'].min():.1f} - {results['brightness_temp'].max():.1f} K")
            else:
                print("✗ Forward calculation failed: missing results")
                
    except Exception as e:
        print(f"✗ Forward calculation failed: {e}")

def main():
    """Run all tests"""
    print("CRTM Python Interface Tests")
    print("==========================")
    
    try:
        test_initialization()
        test_profile_loading()
        test_forward_model()
        print("\nAll tests completed.")
    except Exception as e:
        print(f"\nTest suite failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
