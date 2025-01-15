from ....config import *
from ....config import Config as _Config
from .... import logging_config
import logging
from ....funcs.decorators import *
from ....funcs.utils import anti_join, get_col_names
from ....errors import *

from ..pa_column_schemas import SharedFields as sf 
from .StateUS import StateUS
from .CountyUS import CountyUS
from .LocationRecord import LocationRecord
from ..pa_custom_checks import ensure_enough_locations

import random

from ....data.db import COUNTY_LOOKUP_DF, MSA_LOOKUP_DF, STATE_LOOKUP_DF

logger = logging.getLogger(__name__)
logger.setLevel(Config.logLevels.geog)

# @geog
class LocationDF(pa.DataFrameModel): 
    """
    Model for the columns of a DataFrame containing location data.
    Must at least provide county_name and state_name OR location.
    """
    # In _typing.LocationRecord
    county_name: Series[str] = sf.Geo.county_name()
    county_fips: Series[str] = sf.Geo.county_fips()
    state_name: Series[pl.Categorical] = sf.Geo.state_name()
    state_usps: Series[pl.Categorical] = sf.Geo.state_usps()
    state_fips: Series[pl.Categorical] = sf.Geo.state_fips()
    location: Series[str] = sf.Geo.location() 
    
    county_or_town_name: Series[str] = sf.Geo.location()
    town_fips: Series[str] = sf.Geo.town_fips()
    MSA: Series[pl.Categorical] = sf.Geo.MSA(nullable=True) # not all fields have MSA
    stcountyfips2010: Series[str] = sf.Geo.stcountyfips2010()

    class Config: 
        # https://pandera.readthedocs.io/en/stable/extensions.html
        ensure_enough_locations = () #  Must at least provide county_name and state_name OR location 

    class _PolarsSchema: 
        """
        For creating polars DataFrames from records matching this schema
        """
        schema = {
            'state_name': pl.Categorical,
            'state_fips': pl.Categorical, 
            'state_usps': pl.Categorical,
            'county_name': pl.String,
            'county_fips': pl.String,
            'location': pl.String, 
            'county_or_town_name': pl.String, 
            'town_fips': pl.String,
            'MSA': pl.Categorical,
            'stcountyfips2010':pl.String 
        }

    @classmethod
    def _make_records(cls, locations: 'LocationList') -> tuple[
                                                      tuple[LocationRecord,...] |  Literal['all'], 
                                                      tuple[LocationRecord,...] | Literal['all']
                                                      ]: 
        """
        Make LocationRecords from LocationList.

        Args: 
            locations (LocationList): US Counties, States, or 'all'
        Returns:
            county_records: Tuple of complete LocationRecords
            state_records: Tuple of LocationRecords (only state keys.)
        """
        # Create list copy of contents  
        match locations: 
            case str() | StateUS() | CountyUS(): 
                loc_list = [locations]
            case _ if isinstance(locations, Sequence):
                loc_list = list(locations)
            case _: 
                loc_list = None
                raise TypeError(f"locations unsupported type ({type(locations)})")        
    
        # Parse locations: str, StateUS, or CountyUS 
        state_records = [] # store any complete States -- can just filter down from GEOG.countypop reference table
        county_records = [] # to be made into DataFrame
        def append_record(r: LocationRecord):
            if r.get('county_name'): 
                county_records.append(r)
            else:
                state_records.append(r)

        for loc in loc_list:
            match loc: 
                case 'all': 
                    return 'all', 'all'

                case dict():
                    loc = LocationRecord(dict)
                    append_record(loc)

                case StateUS() | CountyUS():
                    append_record(loc.to_record())
                case str(): # location str or state name
                    try: 
                        county = CountyUS.from_location_str(loc)
                        append_record(county.to_record())
                    except ValueError: 
                        try: 
                            state = StateUS(loc)
                            append_record(state.to_record())
                        except ValueError: 
                            raise ValueError(f'Location {loc} must be a valid US State, County, or location str (<county_name>, <state_name>) (see schemas.geog)') 

                case _: 
                    raise TypeError(f'Location ({loc}) must be one of str, StateUS, or CountyUS')
            
        return tuple(county_records), tuple(state_records)

    @classmethod
    @output_may_omit(('MSA', 'stcountyfips2010', 'town_fips', 'county_or_town_name',))
    def from_location_list(cls, 
                    locations: 'LocationList', 
                    include_MSA: bool = True,
                    logger: logging.Logger | None = None,
                    self=None) -> DataFrame['LocationDF']: 
        """
        Create Locations DataFrame from LocationList.
        Args: 
            locations: List of location designators (see LocationList).
            include_MSA: Whether to join the MSA column from GEOG.msamap
        """
        
        logger = inject_logger(logger)

        county_records, state_records = cls._make_records(locations)

        if county_records ==  'all': 
            return COUNTY_LOOKUP_DF  #TODO: Also join MSA 
        
        # Create df from county records
        df_county_records = cls.from_records(county_records, parse=False).lazy()


        ## Expand records for all states to include all counties
        # get schema
        schema = {k:v for k,v in cls._PolarsSchema.schema.items() if k in ('state_usps', 'state_fips', 'state_name')} 

        df_state_records = pl.LazyFrame(state_records, schema) 
        df_state_records = COUNTY_LOOKUP_DF.join(df_state_records, 
                                                how='right', 
                                                on=['state_name'])\
                                          .select('state_name', 'state_fips', 'state_usps', 
                                                  'county_name', 'county_fips')\
                                          .with_columns(pl.concat_str([
                                              pl.col('county_name').str.to_titlecase(), 
                                              pl.lit(', '),
                                              pl.col('state_usps')
                                              ]).alias('location')
                                            )
        
        df_state_records = cls.order_columns(df_state_records)

        # Concatenate DataFrames (if both non-empty )
        if df_county_records.collect().is_empty(): 
            df_loc = df_state_records
        elif df_state_records.collect().is_empty():
            df_loc = df_county_records
        else:
            df_loc = pl.concat([df_state_records, df_county_records], how='vertical').lazy()

        if logger.getEffectiveLevel() == logging.DEBUG: 
            logger.debug(f"County records: {len(county_records)}; State records: {len(state_records)}")
            logger.debug("County columns: " + ", ".join(df_county_records.collect_schema().names()) + " - " + str(df_county_records.collect().shape))
            logger.debug("State columns: " + ", ".join(df_state_records.collect_schema().names()) + " - " + str(df_state_records.collect().shape))
            logger.debug(", ".join(df_loc.collect_schema().names()) + " - " + str(df_loc.collect().shape))

        # Join MSA data 
        if include_MSA: 
            df_loc = df_loc.join(MSA_LOOKUP_DF, how='left', 
                        on=['state_usps', 'county_name'], # added county_name to MSA_LOOKUP_DF
                        # left_on=['state_usps', 'county_name'],  
                        # right_on=['state_usps', 'county_or_town_name']
                        )
            
        if logger.getEffectiveLevel() == logging.DEBUG: 
            logger.debug(", ".join(df_loc.collect_schema().names()) +  " - " + str(df_loc.collect().shape))
            catch_missing_cols(df_loc, LocationDF, self.output_may_omit)

        return df_loc 

    @classmethod
    @output_may_omit(('MSA', 'stcountyfips2010', 'town_fips', 'county_or_town_name',))
    def from_records(cls, 
                    records: Sequence[LocationRecord], 
                    parse: bool = False, 
                    logger: logging.Logger | None = None, 
                    self=None) -> DataFrame['LocationDF']:    
        """
        Create DataFrame from LocationRecords.

        Args: 
            row_data: Sequence of dict containing location fields (see dir(LocationDF))
            parse: Whether to validate keys and fill missing keys in the LocationRecords before initializing the DataFrame. 
        """

        logger = inject_logger(logger)

        if parse: 
            parsed_records = []
            # Check required types have values
            for r in records:                                         
                # Validate state
                state = StateUS(
                    name=r['state_name'],
                    usps=r['state_usps'],
                    fips=r['state_fips'],
                )
                # Validate county
                county = CountyUS(
                    name=r['county_name'],
                    state=state,   
                    fips=r['county_fips'],   
                ) 

                # Validate/create location column 
                if location_str := r.get('location'): 

                    # Reconcile with state and county values, or create them from the location str 
                    location = CountyUS.from_location_str(location_str) # "location" is really a string representation of a CountyUS  
                    
                    if not state:
                        state = location.state
                    elif state != location.state:
                        raise ValueError(f'Provided state in location {location} does not match {state.name}')
                
                    if not county: 
                        county = location
                    elif county != location: 
                        raise ValueError(f'Provided county in location {location} does not match {county}')

                else: # Create from county and state
                    location_str = county.to_location_str() # Custom check should ensure input data has either state and county or a location column

                # Recreate LocationRecord object    
                row_parsed = LocationRecord(
                    state_name=state.name, 
                    state_fips=state.fips, 
                    state_usps=state.usps,
                    county_name=county.name,
                    county_fips=county.fips,
                    location=location_str,
                )

                # Append 
                parsed_records.append(row_parsed)
            
            # read into dataframe with specified schema 
            schema = {k:v for k,v in cls._PolarsSchema.schema.items() if k in get_annotations(LocationRecord).keys()}
            df = pl.LazyFrame(parsed_records, schema)

            if logger.getEffectiveLevel() == logging.DEBUG:
                catch_missing_cols(df, cls, self.output_may_omit)
        else: 
            schema = {k:v for k,v in cls._PolarsSchema.schema.items() if k in get_annotations(LocationRecord).keys()}
            df = pl.LazyFrame(records, schema)
        
        # Reorder columns 
        df = cls.order_columns(df)

        return df     
    
    @classmethod
    def order_columns(cls, df: DataFrame['LocationDF']): 
        """
        Reorder the location columns to the standard order.  
        """
        loc_cols_ordered = [

            "state_usps",
            "state_fips",
            "county_fips",
            "stcountyfips2010",
            "town_fips",
            "county_name",
            "state_name",
            "county_or_town_name",
            "location",
            "MSA"
        ]
        loc_col_set = set(loc_cols_ordered)
        col_names = df.collect_schema().names()
        # If a column is not in reference_order, assign it a large index (moving it to the end)
        def sort_key(col):
            return loc_cols_ordered.index(col) \
                if col in loc_col_set else len(loc_cols_ordered) + col_names.index(col)

        reordered_cols = sorted(col_names, key=sort_key)
        df = df.select(reordered_cols)

        return df

    @classmethod
    @output_may_omit(('county_or_town_name', 'town_fips', 'stcountyfips2010',))
    def attach_location_columns(cls, 
                                other: pl.LazyFrame, 
                                logger: logging.Logger | None = None, 
                                self=None) -> pl.LazyFrame: 
        """
        Attach missing location columns to a DataFrame.
        """

        logger = inject_logger(logger)

        df = other
        col_names = set(df.collect_schema().names())
        loc_base = {'location', 'county_name', 'state_name'}
        if len(col_names.intersection(loc_base)) == 0:
            logger.warning(f'Input DataFrame lacks any recognized location columns ({", ".join(col_names)}). Leaving unmodified.')
            return df
            
        if "location" not in col_names: 
            logger.debug('Attaching (location) column')
            # validation schema should ensure that the other location columns are included 
            df = df.with_columns(
                pl.concat_str([pl.col('county_name'), pl.col('state_name')],  separator=", ").alias('location'))

        elif any(x not in col_names for x in ('county_name', 'state_name')): 
            logger.debug(f'Attaching (county_name) (state_name) columns')
            df = df.with_columns(pl.col('location').str.split(', ').alias('location_list'))
            df = df.with_columns(
                pl.col('location_list').arr.get(0).alias('county_name'),
                pl.col('location_list').arr.get(1).alias('state_name')
            ).drop('location_list')

        if any(x not in col_names for x in ('state_usps', 'state_fips')):
            logger.debug(f'Attaching (state_usps) (state_fips) columns')
            # Drop other columns from statemap so not to produce duplicate columns 
            cols_to_keep = [c for c in STATE_LOOKUP_DF.collect_schema().names() 
                            if c == 'state_name' or c not in col_names]
            df_statemap = df_statemap.select(cols_to_keep)

            # Join
            df = df.join(df_statemap, 
                    how='left', on='state_name')
        
        if ('MSA' not in df.collect_schema().names()):
            logger.debug(f'Attaching (MSA) column')
            df = df.join(MSA_LOOKUP_DF, how='left', 
                        left_on=['state_usps', 'county_name'], 
                        right_on=['state_usps', 'county_or_town_name'])

        # Reorder location columns to standard order 
        df = LocationDF.order_columns(df)

        if logger.getEffectiveLevel() == logging.DEBUG:
            catch_missing_cols(df, cls, self.output_may_omit)

        return df
    
    @classmethod
    def random_loc_list(cls, n: int = 10, logger: logging.Logger | None = None) -> list[Union[CountyUS, StateUS]]:
        logger = inject_logger(logger)
        counties = CountyUS.random(n // 2)
        states = StateUS.random(n // 2)
        loc_list = counties + states
        if logger.getEffectiveLevel() == logging.DEBUG:
            logger.debug(loc_list)
        return loc_list
        
