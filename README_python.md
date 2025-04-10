# CRTM Python Interface

This Python interface provides a way to use the Community Radiative Transfer Model (CRTM) from Python using ctypes to interface with the Fortran library.

## Prerequisites

1. Built CRTM library (`libcrtm.so`)
2. CRTM coefficient files
3. Python 3.6+ with the following packages:
   - numpy
   - pyyaml (for loading test configurations)

## Installation

1. First, build CRTM following the main README.md instructions
2. Ensure `libcrtm.so` is in your library path or in one of these locations:
   - Standard system library path
   - ./lib/libcrtm.so
   - ../lib/libcrtm.so
   - ~/lib/libcrtm.so

3. Set up coefficient files in one of these locations:
   - Set environment variable CRTM_COEFFS_PATH
   - ./fix/
   - ./test_data/crtm/3.0.0/

4. Copy `crtm_interface.py` to your project

## Usage Example

```python
from crtm_interface import CRTM, load_test_profile

# Load example profile data
atm, sfc, geo = load_test_profile()

# Initialize CRTM and run forward model
with CRTM() as crtm:
    crtm.initialize(sensor_ids=["atms_n21"])
    results = crtm.forward(atm, sfc, geo)
    print(f"Brightness temperatures: {results['brightness_temp']}")
```

## Interface Details

The interface provides these main classes:

### CRTMAtmosphere
Represents atmospheric profile data:
- n_layers: Number of vertical layers
- n_absorbers: Number of absorbing species
- absorber_id: Array of absorber IDs
- absorber: Array of absorber amounts
- temperature: Layer temperatures (K)
- pressure: Layer pressures (Pa)

### CRTMSurface
Represents surface properties:
- land_coverage: Fraction of land (0-1)
- water_coverage: Fraction of water (0-1)
- snow_coverage: Fraction of snow (0-1)
- ice_coverage: Fraction of ice (0-1)
- land_temperature: Land surface temperature (K)
- water_temperature: Water surface temperature (K)
- snow_temperature: Snow surface temperature (K)
- ice_temperature: Ice surface temperature (K)

### CRTM
Main interface class:
- initialize(sensor_ids): Initialize CRTM with specified sensors
- forward(atmosphere, surface, geometry): Run forward model
- destroy(): Clean up CRTM resources

## Common Issues

1. "Could not find CRTM shared library"
   - Ensure CRTM is built successfully
   - Add library directory to LD_LIBRARY_PATH
   - Check if libcrtm.so exists in expected locations

2. "Could not find CRTM coefficient files"
   - Set CRTM_COEFFS_PATH environment variable
   - Check if coefficient files exist in ./fix/ or ./test_data/crtm/3.0.0/

3. Import errors
   - Ensure numpy is installed: `pip install numpy`
   - For test profile loading: `pip install pyyaml`

## Testing

The interface includes a test data loader that can use the same YAML configurations as the CRTM test suite. To run with test data:

```python
from crtm_interface import CRTM, load_test_profile

# Load standard test profile
atm, sfc, geo = load_test_profile("testinput/single_profile.yaml")

# Or use defaults if test file not available
atm, sfc, geo = load_test_profile()
```

## Contributing

When contributing to this interface:
1. Ensure changes maintain compatibility with CRTM's test suite
2. Add tests for new functionality
3. Update documentation for any interface changes
4. Follow Python style guidelines (PEP 8)
