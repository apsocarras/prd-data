import pandera.polars as pa 
import pandas as pd 
import polars as pl 
from ..schemas.pa_column_schemas import SharedFields as sf
import pandera.extensions as extensions
from typing import Union
from ...funcs.decorators import requires


from pandera.api.polars.types import PolarsData


# https://pandera.readthedocs.io/en/stable/checks.html
# https://pandera.readthedocs.io/en/stable/extensions.html

@extensions.register_check_method
def ensure_enough_locations(df:Union[pd.DataFrame, pl.DataFrame, pl.LazyFrame]): 
    """
    Check that a DataFrame has enough location columns.
    """
    match df: 
        case pd.DataFrame(): 
            col_names = set(df.columns)
        case pl.DataFrame() | pl.LazyFrame():
            col_names = set(df.lazy().collect_schema().names()) 
        case PolarsData(): 
            col_names = set(df.lazyframe.collect_schema().names()) 
        # not mentioned in documentation, but at least when registering a check, Pandera reads polars DataFrames as PolarsData() type objects
        case _:
            raise TypeError(f"({df}:{type(df)}) must be one of pd.DataFrame, pl.DataFrame, pl.LazyFrame")

    return ('location' in col_names) or ('county_name' in col_names and 'state_name' in col_names) 
