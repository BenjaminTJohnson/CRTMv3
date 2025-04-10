import os
import ctypes
import numpy as np
from dataclasses import dataclass
from typing import List, Optional

# Define CRTM constants
N_ABSORBERS = 2
N_CLOUDS = 1
N_AEROSOLS = 1
SUCCESS = 0

@dataclass
class CRTMAtmosphere:
    n_layers: int
    n_absorbers: int
    absorber_id: np.ndarray  # (n_absorbers,)
    absorber: np.ndarray     # (n_layers, n_absorbers)
    temperature: np.ndarray  # (n_layers,)
    pressure: np.ndarray    # (n_layers,)

@dataclass
class CRTMSurface:
    land_coverage: float
    water_coverage: float
    snow_coverage: float
    ice_coverage: float
    land_temperature: float
    water_temperature: float
    snow_temperature: float
    ice_temperature: float

class CRTM:
    def __init__(self, coefficient_path: str = None):
        """Initialize CRTM interface
        
        Args:
            coefficient_path: Path to CRTM coefficient files. If None, will try:
                1. Environment variable CRTM_COEFFS_PATH
                2. ./fix/
                3. ./test_data/crtm/3.0.0/
        """
        # Determine coefficient path
        self.coeff_path = coefficient_path
        if self.coeff_path is None:
            if "CRTM_COEFFS_PATH" in os.environ:
                self.coeff_path = os.environ["CRTM_COEFFS_PATH"]
            elif os.path.exists("./fix"):
                self.coeff_path = "./fix"
            elif os.path.exists("./test_data/crtm/3.0.0"):
                self.coeff_path = "./test_data/crtm/3.0.0"
            else:
                raise RuntimeError("Could not find CRTM coefficient files. Please specify coefficient_path or set CRTM_COEFFS_PATH")
        
        # Load the CRTM shared library
        lib_paths = [
            "libcrtm.so",                    # Standard system path
            "./lib/libcrtm.so",              # Local build
            "../lib/libcrtm.so",             # Parent directory
            os.path.expanduser("~/lib/libcrtm.so")  # User's lib directory
        ]
        
        for lib_path in lib_paths:
            try:
                self.lib = ctypes.CDLL(lib_path)
                break
            except OSError:
                continue
        else:
            raise RuntimeError("Could not find CRTM shared library. Please ensure it is built and in your library path.")
            
        self.initialized = False
        
    def initialize(self, sensor_ids: List[str], aerosol_model: str = "CRTM"):
        if self.initialized:
            return
            
        # Convert sensor_ids to Fortran-compatible strings
        sensor_arr = (ctypes.c_char_p * len(sensor_ids))()
        for i, sensor in enumerate(sensor_ids):
            sensor_arr[i] = sensor.encode("utf-8")
        
        # Call CRTM_Init
        status = self.lib.crtm_init(sensor_arr, len(sensor_ids))
        if status != SUCCESS:
            raise RuntimeError(f"CRTM initialization failed with status {status}")
            
        self.initialized = True

    def forward(self, atmosphere: CRTMAtmosphere, surface: CRTMSurface, geometry: dict) -> dict:
        if not self.initialized:
            raise RuntimeError("CRTM not initialized")
            
        # Convert atmosphere data to C-compatible arrays
        temp_arr = np.ascontiguousarray(atmosphere.temperature, dtype=np.float32)
        pres_arr = np.ascontiguousarray(atmosphere.pressure, dtype=np.float32)
        absorber_arr = np.ascontiguousarray(atmosphere.absorber, dtype=np.float32)
        
        # Convert surface data
        sfc_data = (ctypes.c_float * 8)(
            surface.land_coverage,
            surface.water_coverage,
            surface.snow_coverage,
            surface.ice_coverage,
            surface.land_temperature,
            surface.water_temperature,
            surface.snow_temperature,
            surface.ice_temperature
        )
        
        # Set up geometry
        geo_data = (ctypes.c_float * 3)(
            geometry["sensor_zenith_angle"],
            geometry["sensor_azimuth_angle"],
            geometry["sensor_height"]
        )
        
        # Allocate space for results
        n_channels = 1  # This should be determined from sensor info
        radiance = np.zeros(n_channels, dtype=np.float32)
        bt = np.zeros(n_channels, dtype=np.float32)
        
        # Call CRTM_Forward
        status = self.lib.crtm_forward(
            ctypes.c_int(atmosphere.n_layers),
            temp_arr.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
            pres_arr.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
            absorber_arr.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
            sfc_data,
            geo_data,
            radiance.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
            bt.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
        )
        
        if status != SUCCESS:
            raise RuntimeError(f"CRTM forward calculation failed with status {status}")
            
        return {
            "radiance": radiance,
            "brightness_temp": bt
        }

    def destroy(self):
        if self.initialized:
            status = self.lib.crtm_destroy()
            if status != SUCCESS:
                raise RuntimeError(f"CRTM destruction failed with status {status}")
            self.initialized = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.destroy()

def load_test_profile(yaml_path: str = "testinput/single_profile.yaml"):
    """Load test profile data from YAML configuration
    
    Args:
        yaml_path: Path to YAML configuration file
        
    Returns:
        tuple: (atmosphere, surface, geometry) objects ready for CRTM forward model
    """
    try:
        import yaml
    except ImportError:
        raise ImportError("PyYAML is required to load test profiles. Install with: pip install pyyaml")
        
    with open(yaml_path) as f:
        config = yaml.safe_load(f)
    
    # Extract relevant configuration
    obs_config = config["Observations"]["ObsTypes"][0]["ObsOperator"]
    
    # Create atmosphere profile
    atm = CRTMAtmosphere(
        n_layers=92,  # Standard atmospheric layers
        n_absorbers=obs_config.get("n_Absorbers", N_ABSORBERS),
        absorber_id=np.array([1, 2]),  # H2O and O3 by default
        absorber=np.zeros((92, N_ABSORBERS)),
        temperature=np.linspace(300, 200, 92),  # Example temperature profile
        pressure=np.logspace(5, 2, 92)  # Example pressure profile in Pa
    )
    
    # Create surface data (example values)
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
    
    # Create geometry from configuration
    geo = {
        "sensor_zenith_angle": 30.0,  # Default viewing angle
        "sensor_azimuth_angle": 180.0,
        "sensor_height": 800000.0  # Typical satellite height in meters
    }
    
    return atm, sfc, geo

def example_usage():
    """Example of how to use the CRTM Python interface"""
    # Load test profile
    try:
        atm, sfc, geo = load_test_profile()
    except Exception as e:
        print(f"Could not load test profile, using defaults: {e}")
        # Fall back to default values
        atm = CRTMAtmosphere(
            n_layers=92,
            n_absorbers=N_ABSORBERS,
            absorber_id=np.array([1, 2]),
            absorber=np.zeros((92, N_ABSORBERS)),
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
    
    # Use CRTM
    with CRTM() as crtm:
        # Use sensor from test configuration or default
        sensor_id = "atms_n21"  # Common test sensor
        crtm.initialize(sensor_ids=[sensor_id])
        results = crtm.forward(atm, sfc, geo)
        print(f"Results for sensor {sensor_id}:")
        print(f"  Brightness temperatures: {results['brightness_temp']}")
        print(f"  Radiances: {results['radiance']}")

if __name__ == "__main__":
    example_usage()
