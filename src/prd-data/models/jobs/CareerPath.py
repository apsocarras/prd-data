from ....config import *
from ....config import Config as _Config
from .... import logging_config
import logging 
from ....errors import missing_required, catch_missing_cols

from ...schemas.jobs.Job import Job, JobRecord
from ...schemas.jobs.OccupationOEWS import OccupationOEWS
from ...schemas.pa_column_schemas import SharedFields as sf
from ...db import JOB_LOOKUP_DF

from ....funcs.utils import get_consecutive_year_ranges, inject_logger
from ....funcs.decorators import requires, output_may_omit

from bisect import bisect_left
import random

logger = logging.getLogger(__name__)
logger.setLevel(Config.logLevels.jobs)

class CareerPath(BaseModel): 
    """
    Model for a chronological sequence of past, present, and/or future jobs. 
    Requires all contained jobs to have a start year and end year and to fall with bounds of working years.
    """
    jobs: Sequence[Job] =  pyd.Field(..., description='Sequence of past, current, and/or future jobs.')
    starting_year: int = pyd.Field(Config.defaults.starting_year, description="Year to start career path.", ge=2023)
    starting_age: int = pyd.Field(Config.defaults.starting_age, description="Age to start career path.", ge=30)
    retirement_age: int = pyd.Field(Config.defaults.retirement_age, description="Year to start career path.", gt=0)

    def __init__(self, 
                 jobs: Sequence[Job],
                 starting_year: int = Config.defaults.starting_year,
                 starting_age: int = Config.defaults.starting_age,
                 retirement_age: int = Config.defaults.retirement_age): 
        
        # Sort jobs chronologically before adding them 
        jobs = sorted(jobs, reverse=False, key=lambda j: j.year_ended)

        super().__init__(jobs=jobs, starting_year=starting_year, starting_age=starting_age, retirement_age=retirement_age)
    
    def __iter__(self): 
        yield from self.jobs

    def __str__(self):
        return ", ".join([str(j) for j in self.jobs])
    
    def add_job(self, job: Job,/) -> None:
        """
        Insert a Job to the CareerPath in chronological order. 
        """
        for y in job.year_started, job.year_ended: 
            if not y: 
                raise ValueError(f'Job {job} must have year_started and year_ended set before being added to the CareerPath.')
            elif y not in self.working_years:
                raise ValueError(f'Job {job} must have year_started and year_ended within CareerPath().working_years.')
 
        job_index = bisect_left(self.jobs, job)
        self.jobs.insert(job_index, job)
    
    @property
    def working_years(self) -> range: 
        """
        Duration of career from start till retirement, including periods of unemployment.
        """
        return CareerPath._det_working_years(self.starting_year, self.starting_age, self.retirement_age)
    
    @property
    def years_employed(self) -> tuple[str]: 
        """
        Years actively worked (requires setting jobs list).
        """
        return CareerPath._det_years_employed(self.jobs, as_strings=False)
        
    @model_validator(mode='before')
    @classmethod
    def ensure_jobs_in_bounds(cls, data: dict): 
        working_range = cls._det_working_years(data['starting_year'], data['starting_age'], data['retirement_age'])
        for j in data['jobs']: 
            if j.year_started not in working_range or j.year_ended not in working_range: 
                raise ValueError(f"Provided Job {j} not in bounds of working age.")
        return data

    @field_validator('jobs')
    @classmethod
    def ensure_jobs_have_years(cls, jobs: Sequence[Job]): 
        """
        Ensure all jobs have start and end years.
        """
        for j in jobs: 
             if not j.year_started or not j.year_ended: 
                 raise ValueError(f"All jobs in CareerPath must have start year and end year.")
        return jobs 
    
    @classmethod 
    def _det_working_years(cls, starting_year: int, starting_age: int, retirement_age: int) -> range:
        """
        Determine overall start and end of career, ignoring gaps.
        """
        return range(starting_year, (retirement_age - starting_age) + starting_year + 1)
    
    @classmethod 
    def _det_years_employed(cls, jobs: Sequence[Job], as_strings=False) -> tuple: 
        """
        Get individual ranges of years actively worked (i.e. accounting for gaps).
        """        
        years = {}
        for j in jobs: 
            if j.year_started not in years:
                years.add(j.year_started)
            elif j.year_ended not in years: 
                years.add(j.year_ended)
        return get_consecutive_year_ranges(years, as_strings=as_strings)
    
    def to_records(self, insert_age: bool = True ) -> list['CareerPathRecord']:
        
        result = []
        
        if not insert_age: 
            for j in self.jobs: 
                result.extend(j.to_records())
        else: 
            for j in self.jobs: 
                starting_age = self.starting_age + (j.year_started - self.starting_year)
                ending_age = self.starting_age + (j.year_ended - self.starting_year)
                age_range = range(starting_age, ending_age+1)
                job_records = [{**t[0], **{'age':t[1]}} for t in zip(j.to_records(), age_range)]
                result.extend(job_records)

        return result
        
    @classmethod
    def random(cls, 
               starting_year: int = Config.defaults.starting_year, 
               starting_age: int = Config.defaults.starting_age, 
               retirement_age: int = Config.defaults.retirement_age, 
               occ_list: Sequence[OEWS_Code] | None = None) -> 'CareerPath': 
        """
        Generate a random career path of jobs starting from starting_age to retirement_age. 

        Args: 
            occ_list: Set of occupation codes from which to chose jobs.
            (If None, using full lookup table via OccupationOEWS.random())
        """
        year_range = CareerPath._det_working_years(starting_year, starting_age, retirement_age)
        n = min(year_range)
        end = max(year_range)
        jobs = []
        while n < end:
            m = n + random.randint(0,end - n)
            rand_occ = OccupationOEWS.random(from_list=occ_list)
            rand_hours = random.choice([20,40])
            rand_hourly_wage = random.randint(20, 101)
            rand_experience = random.choice([0,1,2,3,4])
            rand_empl_healthcare = random.choice([True, False])
            rand_education_duration = random.randint(0,4)
            j = Job(occ_code = rand_occ.occ_code,
                occ_title = rand_occ.occ_title,
                hours=rand_hours,
                year_started=n,
                year_ended=m,
                experience=rand_experience,
                hourly_wage=rand_hourly_wage,
                empl_healthcare=rand_empl_healthcare,
                education_duration=rand_education_duration
                )
            jobs.append(j)
            n = m + 1 # changed from n + (n-m) to not be overlapping
        return CareerPath(jobs=jobs, starting_year=starting_year, starting_age=starting_age, retirement_age=retirement_age)
  
class CareerPathRecord(JobRecord):
    """
    Schema for turning CareerPath into JSON row formatted data for creating a CareerPathInputDF.
    Note that this excludes location information -- the idea for a CareerPath object is just to have 
    a container for a sequence of Jobs with certain constraints. 
    """
    age: int 

### DataFrame Schemas 

## NOTE: When you're setting a DataFrame schema specifically as something a function needs to take in as input or give as output, 
# be careful of setting them as Optional if you/the function is going to need to add them in in order to use the schema. 
# Provide default values for those columns -- or if you have to calculate the defaults, just leave the columns as required. 
# Otherwise, it's confusing as to what these schemas represent.
# Since purpose of a schema is for testing, they should mainly represent the "checkpoints" you have to hit in the pipeline (leave them immutable and inflexible).
# To reinforce that role, you may want minimize or avoid non-validation methods.

class CareerPathInputDF(pa.DataFrameModel): 
    """
    Pandera DataFrameModel for input DataFrame to the project_CareerPathDF() function. 
    """    

    year: Series[Int16] = sf.Year()
    age: Series[Int8] = sf.Beneficiary.Eligibility.age()
    
    county_name: Series[str] = sf.Geo.county_name()
    state_name: Series[pl.Categorical] = sf.Geo.state_name()
    location: Series[CountyStateString] =  sf.Geo.location()

    occ_code: Series[pl.Categorical] = sf.Jobs.occ_code() # type: ignore
    occ_title: Series[pl.Categorical] = sf.Jobs.occ_title() # type: ignore
    
    experience: Series[Int8] = sf.Jobs.experience()
    empl_healthcare: Series[bool] = sf.Jobs.empl_healthcare()
    hours: Series[Int8] = sf.Jobs.hours()

    # Optional overrides of values in the Jobs database.
    starting_wage: Series[Float32] = sf.Jobs.starting_wage()
    education_duration: Series[Int8] = sf.Jobs.education_duration()
    
    class Config:        
        # https://pandera.readthedocs.io/en/stable/extensions.html
        ensure_enough_locations = ()

    class _PolarsSchema: 
        schema = {
            "year": pl.Int16,
            "age": pl.Int8, 
            "county_name": pl.String, 
            "state_name": pl.Categorical, 
            "location": pl.String,  
            "occ_code": pl.Categorical, 
            "occ_title": pl.Categorical,
            "experience": pl.Int8,
            "empl_healthcare": pl.Boolean,
            "hours": pl.Int8,
            "starting_wage":pl.Float32,
            "education_duration": pl.Int8
        }
    
    @classmethod
    @requires(('occ_code',))
    @output_may_omit(('starting_wage', 'county_name', 'state_name', 'location'))
    def attach_career_columns(cls, df: pl.LazyFrame,
                        starting_age: int = _Config.defaults.starting_age,
                        starting_year: int = _Config.defaults.starting_year, 
                        retirement_age: int = _Config.defaults.retirement_age,
                        empl_healthcare: bool = _Config.defaults.empl_healthcare,
                        hours: int = _Config.defaults.hours,
                        starting_wage: Optional[float] = None,
                        logger: logging.Logger | None = None,
                        self = None) -> pl.LazyFrame: 
        """
        Add missing job/career-related columns to the DataFrame which are needed to calculate the wages.  

        Args:
            df: DataFrame with at least a Column for job codes ('occ_code')
        """
        logger = inject_logger(logger)

        if missing_required(df, self.required_cols):
            return 

        col_names = set(df.collect_schema().names())

        ## Education 
        if 'education_duration' not in col_names: 
            if 'educationDuration' in col_names: 
                logger.debug('Renaming educationDuration to (education_duration)')
                df = df.rename({'educationDuration':'education_duration'})
            else: 
                logger.debug('Joining (education_duration) column.')
                df = df.join(JOB_LOOKUP_DF, how='left', on='occ_code')
            
        ## Employer Healthcare 
        if 'empl_healthcare' not in col_names: 
            logger.debug(f'TODO: Attaching (empl_healthcare) default setting for each OccupationOEWS in the source database.')
            df = df.with_columns(pl.lit(empl_healthcare).alias('empl_healthcare'))

        ## Working Hours
        if 'hours' not in col_names: 
            logger.debug(f'Attaching (hours) for weekly hours worked ({hours})')
            df = df.with_columns(pl.lit(hours).alias('hours'))

        ## Working Years and Worker Age 
        if 'year' not in col_names: 
            logger.debug('Attaching (year), (age) columns.')

            # Drop any existing age column 
            if 'age' in col_names: 
                logger.debug(f"Dropping existing age column to replace with years from starting_age={starting_age}.")
                df = df.drop('age')

            # Determine years worked and expand into DF 
            working_years = CareerPath._det_working_years(starting_year, starting_age, retirement_age)
            df_years = pl.from_dicts([{'year':y, 'age':starting_age + n} for n,y in enumerate(working_years)]).lazy()

            # Expand with cross product 
            df = df.join(df_years, how='cross')

        ## Years of experience
        if 'experience' not in col_names: 
            logger.debug(f'Attaching (experience) column based on years since starting_year={starting_year})')
            # Identify first year on the job for each job 
            df_min = df.group_by('occ_code')\
                .agg(pl.col('year').min())\
                .select(['occ_code', 'year'])\
                .rename({'year':'starting_year'})
            
            # Join back to df and subtract for experience 
            df = df.join(df_min, how='left', on='occ_code')\
                    .with_columns((pl.col('year') - pl.col('starting_year')).alias('experience'))\
                    .drop('starting_year')
        
        ## Starting wage 
        if starting_wage:
            if 'starting_wage' in col_names: 
                logger.debug('Replace existing (starting_wage) column')
                df = df.drop('starting_wage')
            else: 
                logger.debug('Attaching (starting_wage) column')

            df = df.with_columns('starting_wage', pl.lit(starting_wage))
            

        if logger.getEffectiveLevel() == logging.DEBUG:
            catch_missing_cols(df, CareerPathInputDF, self.output_may_omit)

        return df
        

class CareerPathOutputDF(CareerPathInputDF):
    """
    Model for validating the output of the project wages function. Inherits columns from CareerPathInput. All fields are required.
    """

    # Geo
    county_name: Series[str] = sf.Geo.county_name()
    state_name: Series[pl.Categorical] = sf.Geo.state_name()
    location: Series[str] = sf.Geo.location()
    MSA: Series[pl.Categorical] = sf.Geo.MSA()
    MSA_replaced_w_state: Series[bool] = sf.Geo.MSA_replaced_w_state()

    # Calculated values
    wage_hourly: Series[float] 
    income_weekly: Series[float]
    income_annual: Series[float]

    # Other variables used in projections formula 
    minwage: Series[float] = pa.Field(description="Default is from db.Jobs.minWage", nullable=Config.defaults.nullable) 
    minwage_old: Series[float] = pa.Field(description="Default is from db.Jobs.minWage", nullable=Config.defaults.nullable)
    wagegain: Series[float] = pa.Field(description="Difference between old and current minimum wage", nullable=Config.defaults.nullable)
    experiencegain: Series[float] = pa.Field(description='Portion of wage increase attributable to increase in income', nullable=Config.defaults.nullable) 
    phaseout: Series[float] = pa.Field(description="min_wage + wagegain * .5. Used to model a tapering-off effect of the minimum wage increase for jobs earning more than minimum wage starting (0 effect if more than 1.5x times).", nullable=Config.defaults.nullable)
    starting_wage_adjusted: Series[float] = pa.Field(description='Adjust starting_wage to be A.) above minwage_old (if below) B.) tapered off by phaseout', nullable=Config.defaults.nullable) 
    
    class _PolarsSchema:    
        """
        Includes all the columns for the output of the project_CareerPath function.
        """
        schema = {
            "state_usps": pl.Categorical,
            "state_fips": pl.Categorical,
            "county_fips": pl.String, 
            "county_name": pl.String,
            "state_name": pl.Categorical,
            "location": pl.String, 
            "MSA":pl.Categorical, 
            "year": pl.Int16,
            "age": pl.Int8, 
            "location": pl.String,  
            "occ_code": pl.Categorical, 
            "occ_title": pl.Categorical,
            "experience": pl.Int8,
            "empl_healthcare": pl.Boolean,
            "hours": pl.Int8,
            "starting_wage":pl.Float32,
            "education_duration": pl.Int8, 
            "area_occ":pl.String,
            "MSA_replaced_w_state":pl.Boolean,
            "minwage":pl.Float32,
            "minwage_old": pl.Float32,
            "yrsofexpsqrt": pl.Float32,
            "yrsofexp": pl.Float32,
            "intercept":pl.Float32,
            "wagegain":pl.Float32,
            "phaseout":pl.Float32,
            "starting_wage_adjusted":pl.Float32, 
            "experiencegain": pl.Float32, 
            "wage_hourly":pl.Float32,
            "income_weekly":pl.Float32, 
            "income_annual":pl.Float32,
            "experiencegain":pl.Float32,
            "career_path":pl.String,
            "location_list":pl.String
        }


    @classmethod
    def to_json(cls, df: DataFrame['CareerPathOutputDF'], json_schema: dict): 
        """
        (TODO:) Dump a validated DataFrame to JSON schema for frontend 
        """
        