import geopandas as gpd
import pandas as pd

from ngen.config_gen.file_writer import DefaultFileWriter
from ngen.config_gen.hook_providers import DefaultHookProvider
from ngen.config_gen.generate import generate_configs

from ngen.config_gen.models.cfe import Cfe
from ngen.config_gen.models.pet import Pet

#basin_id = '1022500'
# or pass local file paths instead
#hf_file = f"s3://lynker-spatial/hydrofabric/v20.1/camels/Gage_{basin_id}.gpkg"
hf_file = "./Gage_1022500.gpkg"
hf_lnk_file = "s3://lynker-spatial/hydrofabric/v20.1/model_attributes.parquet"

hf: gpd.GeoDataFrame = gpd.read_file(hf_file, layer="divides")

hf_lnk_data: pd.DataFrame = pd.read_parquet(hf_lnk_file)

hf_lnk_data = hf_lnk_data[ hf_lnk_data['divide_id'].isin( hf['divide_id'] )]

hook_provider = DefaultHookProvider(hf=hf, hf_lnk_data=hf_lnk_data)
# files will be written to ./config
file_writer = DefaultFileWriter("./config/")

generate_configs(
    hook_providers=hook_provider,
    hook_objects=[Cfe, Pet],
    file_writer=file_writer,
)