from pydantic import BaseModel, Field
from typing import Optional, Literal, Union
from datetime import date

class Budget(BaseModel):
    """
    Class for modeling total household budget. Any default values provided will override estimates from ALICE.
    """
    year: int = Field(..., description="Year the budget applies to.", gte=2023)
    month: Optional[Union[str, int, date]] = Field(None, description="Month the budget applies to.")

    own_or_rent: Literal['own','rent'] = Field(..., description="Whether the family owns or rents their home (determines meaning of rentormortgage).")
    budget_mode: Literal['survivalforcliff'] = Field(..., description="Mode for calculating the estimated expenses.")
    buget_period: Literal['annual', 'monthly'] = Field('annual', description="Whether the given budget is annualized or monthly.")

    # Output Columns (in output of calculator)
    exp_childcare: Optional[Union[int,float]] = Field(None, description="OOP childcare costs.", gt=0)
    exp_food: Optional[Union[int, float]] = Field(None, description="Food costs.", gt=0)
    exp_rentormortgage: Optional[Union[int, float]] = Field(None, description="Rent or mortgage.", gt=0) 
    exp_healthcare: Optional[Union[int, float]] = Field(None, description="OOP healthcare costs.", gt=0) 
    exp_utilities: Optional[Union[int, float]] = Field(None, description="OOP utility costs.", gt=0)    
    exp_transportation: Optional[Union[int, float]] = Field(None, description="Transportation costs.", gt=0)    
    exp_tech: Optional[Union[int, float]] = Field(None, description="Expenses for tech.", gt=0)    
    exp_misc: Optional[Union[int, float]] = Field(None, description="Miscellaneous other expenses.", gt=0)    

    # Factoring in subsidies/benefits 
    netexp_childcare: Optional[Union[int,float]] = Field(None, description="OOP childcare costs after subsidies.", gt=0)
    netexp_food: Optional[Union[int, float]] = Field(None, description="OOP food costs after subsidies.", gt=0)
    netexp_rentormortgage: Optional[Union[int, float]] = Field(None, description="OOP rent or mortgage after subsidies.", gt=0) 
    netexp_healthcare: Optional[Union[int, float]] = Field(None, description="OOP healthcare costs after subsidies.", gt=0) 
    netexp_utilities: Optional[Union[int, float]] = Field(None, description="OOP utility costs after subsidies.", gt=0) 
