# Guide for calibrating camels basins using ngen-cal

## Activate your ngen venv
For this guide, it is assumed that a valid ngen build with python and C support is available.  We will use the ngen virtual environment to setup the calibration workflow.  You can build ngen in this directory, or symlink your ngen directory here for simplicity.

```sh
source ngen/venv/bin/activate
```

## Git and install the calibration code for development

Pull the source code from GitHub

```sh
git clone https://github.com/noaa-owp/ngen-cal
cd ngen-cal
```

Now we will install the packages to use them, but do so in a development mode which allows changes to the code to reflect in the installed packages.  This is useful for developing and testing.

There are a few different packages in this repository which support calibration and other configuration mechanics around NextGen.  We will focus mostly on the calibration package here.

### Install the calibration package in development mode

```sh
pip install -e python/ngen_cal
```

See [the wiki](https://github.com/NOAA-OWP/ngen-cal/wiki/Installing-ngen-cal) for additional installation notes.

### Install the ngen_config_gen package
We will use this later to generate some BMI initialization files

```sh
pip install python/ngen_config_gen
cd ..
```

## Get a camels hydrofabric geopackage from Lynker-Spatial
This will pull the hydrofabric for camels basin 1022500
```sh
wget http://lynker-spatial.s3.amazonaws.com/hydrofabric/v20.1/camels/Gage_1022500.gpkg
```
## Prepare the calibration configurations

We assume that a valid ngen build exists, as well as the CFE module library.  For details on setting these up, see the [ngen wiki](https://github.com/NOAA-OWP/ngen-cal/wiki/Installing-ngen-cal)

#[!FIXME] routing?

### ngen realization config
The following realiation will be used as the intial configuration for the calibration run.  Copy this to your working direcctory.

<details>
<summary>realization.json</summary>

```json
{
    "global": {
        "formulations": [
            {
                "name": "bmi_multi",
                "params": {
                    "name": "bmi_multi",
                    "model_type_name": "SLOTH_PET_CFE",
                    "forcing_file": "",
                    "init_config": "",
                    "allow_exceed_end_time": true,
                    "main_output_variable": "Q_OUT",
                    "modules": [
			            {
			                "name": "bmi_c++",
			                "params": {
                                "name": "bmi_c++",
                                "model_type_name": "SLOTH",
                                "library_file": "/Users/nelsfrazier/workspace/demo/camels_calibration/ngen/extern/sloth/cmake_build/libslothmodel",
                                "init_config": "/dev/null",
                                "allow_exceed_end_time": true,
                                "main_output_variable": "z",
                                "uses_forcing_file": false,
                                "model_params": {
				                    "sloth_ice_fraction_schaake(1,double,m,node)": 0.0,
				                    "sloth_ice_fraction_xinanjiang(1,double,1,node)": 0.0,
				                    "sloth_smp(1,double,1,node)": 0.0
                                }
			                }
                        },
                        {
                            "name": "bmi_c",
                            "params": {
                                "name": "bmi_c",
                                "model_type_name": "PET",
                                "library_file": "/Users/nelsfrazier/workspace/demo/camels_calibration/ngen/extern/evapotranspiration/cmake_build/libpetbmi",
                                "forcing_file": "",
                                "init_config": "/Users/nelsfrazier/workspace/demo/camels_calibration/config/PET_{{id}}.ini",
                                "allow_exceed_end_time": true,
                                "main_output_variable": "water_potential_evaporation_flux",
                                "registration_function": "register_bmi_pet",
                                "variables_names_map": {
                                    "water_potential_evaporation_flux": "potential_evapotranspiration"
                                }
                            }
                        },
                        {
                            "name": "bmi_c",
                            "params": {
                                "name": "bmi_c",
                                "model_type_name": "CFE",
                                "library_file": "/Users/nelsfrazier/workspace/demo/camels_calibration/ngen/extern/cfe/cmake_build/libcfebmi",
                                "forcing_file": "",
                                "init_config": "/Users/nelsfrazier/workspace/demo/camels_calibration/config/CFE_{{id}}.ini",
                                "allow_exceed_end_time": true,
                                "main_output_variable": "Q_OUT",
                                "registration_function": "register_bmi_cfe",
                                "variables_names_map": {
                                    "water_potential_evaporation_flux": "potential_evapotranspiration",
                                    "atmosphere_water__liquid_equivalent_precipitation_rate": "APCP_surface",
                                    "ice_fraction_schaake" : "sloth_ice_fraction_schaake",
                                    "ice_fraction_xinanjiang" : "sloth_ice_fraction_xinanjiang",
                                    "soil_moisture_profile" : "sloth_smp"
                                }
                            }
                        }
                    ]
                }
            }
        ],
        "forcing": {
            "file_pattern": "{{id}}_1022500_2018_to_2019.csv", 
            "path": "/Users/nelsfrazier/workspace/demo/camels_calibration/forcing/2018_to_2019/camels_1022500_2018_to_2019/",
            "provider": "CsvPerFeature"
        }
    },
    "time": {
        "start_time": "2018-01-01 00:00:00",
        "end_time": "2018-01-01 23:00:00",
        "output_interval": 3600
    },
   
    "routing": {
        "t_route_config_file_with_path": "/Users/nelsfrazier/workspace/demo/camels_calibration/routing.yaml"
    }
}
```

</details>

### BMI initial configs

Use the `gen_init_config.py` script to generate bmi initialization files for CFE and PET modules.

```sh
AWS_NO_SIGN_REQUEST=yes python ./gen_init_config.py
```

### Calibration config
<details>
<summary>config.yaml</summary>

```yaml
# file: calibration_config.yaml
general:
  strategy: 
      # Type of strategy, currently supported is estimation
      type: estimation
      # defaults to dds (currently, the only supported algorithm)
      algorithm: "dds"

  # Enable model runtime logging (captures standard out and error and writes to file)
  # logs will be written to <model.type>.log when enabled
  # defaults to False, which sends all output to /dev/null
  log: True

  start_iteration: 0
  # The total number of search iterations to run
  iterations: 100

# Define parameters to calibrate, their bounds, and initial values.
cfe_params: &cfe_params
  - 
      name: maxsmc
      min: 0.2
      max: 1.0
      init: 0.439
  - 
      name: satdk
      min: 0.0
      max: 0.000726
      init: 3.38e-06
  - 
      name: slope
      min: 0.0
      max: 1.0
      init: 0.01
  - 
      name: expon
      min: 1.0
      max: 8.0
      init: 6.0

# Model specific configuration
model:
    type: ngen
    # NOTE: you may need to adjust this to the location of your NextGen installation
    # A binary in $PATH or a qualified path to the binary to run
    binary: "/Users/nelsfrazier/workspace/demo/camels_calibration/ngen/cmake_build/ngen"
    realization: ./realization.json
    # Required path to catchment hydrofabirc file
    hydrofabric: ./Gage_1022500.gpkg
    eval_feature: wb-3550
    # Each catchment upstream of observable nexus gets its own permuted parameter space, evaluates at one observable nexus 
    strategy: independent
    params: 
        CFE: *cfe_params
    
    eval_params:
      # choices are "kling_gupta", "nnse", "custom", "single_peak", "volume"
      objective: "kling_gupta"
```

</details>

### Routing config

<details>

<summary>routing.yaml</summary>

```yaml

#--------------------------------------------------------------------------------
log_parameters:
    #----------
    showtiming: True
    log_level : DEBUG
#--------------------------------------------------------------------------------
network_topology_parameters:
    #----------
    supernetwork_parameters:
        title_string: "Ngen"
        #----------
        network_type: HYFeaturesNetwork 
        geo_file_path: /Users/nelsfrazier/workspace/demo/camels_calibration/Gage_1022500.gpkg
        mask_file_path: # domain/unit_test_noRS/coastal_subset.txt
        synthetic_wb_segments:
            #- 4800002
            #- 4800004
            #- 4800006
            #- 4800007
        columns: 
            key: 'id'
            downstream: 'toid'
            dx : 'length_m'
            n : 'n'
            ncc : 'nCC'
            s0 : 'So'
            bw : 'BtmWdth'
            waterbody : 'rl_NHDWaterbodyComID'
            gages : 'rl_gages'
            tw : 'TopWdth'
            twcc : 'TopWdthCC'
            musk : 'MusK'
            musx : 'MusX'
            cs : 'ChSlp'
            alt: 'alt'
    waterbody_parameters:
        #----------
        break_network_at_waterbodies: False 
        level_pool:
            #----------
            level_pool_waterbody_parameter_file_path: /Users/nelsfrazier/workspace/demo/camels_calibration/Gage_1022500.gpkg
        #rfc:
            #----------
            #reservoir_parameter_file                : domain/reservoir_index_AnA.nc
            #reservoir_rfc_forecasts                 : False
            #reservoir_rfc_forecasts_time_series_path: rfc_TimeSeries/
            #reservoir_rfc_forecasts_lookback_hours  : 48
#--------------------------------------------------------------------------------
compute_parameters:
    #----------
    parallel_compute_method: by-subnetwork-jit-clustered #serial 
    compute_kernel         : V02-structured
    assume_short_ts        : True
    subnetwork_target_size : 10000
    cpu_pool               : 1
    restart_parameters:
        #----------
        start_datetime: "2018-01-01 00:00:00"
    forcing_parameters:
        #----------
        qts_subdivisions            : 12
        dt                          : 300 # [sec]
        qlat_input_folder           : ./ 
        qlat_file_pattern_filter    : "nex-*"
        binary_nexus_file_folder    : ./ # this is required if qlat_file_pattern_filter="nex-*"
        nts                         : 288 #288 for 1day
        max_loop_size               : 288 # [hr]  
    data_assimilation_parameters:
    #    #----------
    #    usgs_timeslices_folder   : #usgs_TimeSlice/
    #    usace_timeslices_folder  : #usace_TimeSlice/
    #    timeslice_lookback_hours : #48 
    #    qc_threshold             : #1
        streamflow_da:
    #        #----------
            streamflow_nudging            : False
            diffusive_streamflow_nudging  : False
        reservoir_da:
            #----------
            reservoir_persistence_da:
                #----------
                reservoir_persistence_usgs  : False
                reservoir_persistence_usace : False
            reservoir_rfc_da:
                #----------
                reservoir_rfc_forecasts: False
#--------------------------------------------------------------------------------
output_parameters:
    csv_output:
        csv_output_folder: ./
    #----------

```

</details>

## Get some forcing data

We are going to borrow a forcing generator to get nextgen forcings for our camels basin.

Clone the following repository

```sh
git clone https://github.com/jmframe/CIROH_DL_NextGen
```
and copy this config into your working directory

<details>
<summary>forcing.yaml</summary>

```yaml
aorc_source: "s3://noaa-nws-aorc-v1-1-1km" # url of AORC data stored as zarr files in s3
aorc_year_url_template: "{source}/{year}.zarr" # filename format of AORC zarr data files
basin_url_template: "s3://lynker-spatial/hydrofabric/v20.1/camels/Gage_{basin_id}.gpkg" # URL of CAMELS basin geopackages
basins:
  - 1022500 #may list out basins of interest, or simply specify 'all'
  #- 'all'
years:
  - 2018 # The beginning year of interest, bgn_yr. May go as low as 1979.
  - 2019 # This must be at least bgn_yr + 1 to represent a single year. e.g. bgn_yr = 2018, end_year = 2019 means grab data throughout 2018 only. Default 2024 means data through 2023 grabbed.
cvar: 8 # Chunk size for variables. Default 8.
ctime_max: 120 # The max chunk time frame. Units of hours.
cid: -1 # The divide_id chunk size. Default -1 means all divide_ids in a basin. A small value may be needed for very large basins with many catchments.
redo: false # Set to true if you want to ensure intermediate data files not read in from local storage
x_lon_dim: "longitude" # The longitude term in the AORC dataset
y_lat_dim: "latitude" # The latitude term in the AORC dataset
out_dir: "./forcing" # The local storage data output directory. 

```

</details>

Then run the following commands to generate a year's worth of forcings

```sh
pip install -r CIROH_DL_NextGen/forcing_prep/requirements.txt
python CIROH_DL_NextGen/forcing_prep/generate.py forcing.yaml
```

# Running the calibration

```sh
python -m ngen.cal config.yaml  
```
# Acknowledgements

Hydrofabric data used in this guide provided curtesey of Lynker and Lynker-Spatial.
See the [copyright notice](https://lynker-spatial.s3-us-west-2.amazonaws.com/copyright.html) associated with the hydrofabric data for more information on it acceptable use.
