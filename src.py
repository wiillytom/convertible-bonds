from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime, timedelta
import yfinance as yf
from fredapi import Fred
import pandas as pd

fred = Fred(api_key='5079f41d061a4037d81f3da69e018803')

frequency_mapping_dict = {
    'Annually': 1,
    'Semi-Annually': 2,
    'Quarterly': 4
}

@dataclass 
class Stock:
    Ticker: str

    def price(self):
        return yf.Ticker(self.Ticker).fast_info['lastPrice']

@dataclass
class Interest_Rates:
    Maturity: str
    Frequency: str

    Num_Frequency: int = field(init=False)
    T: int = field(init=False)

    def __post_init__(self):
        try:
            self.Num_Frequency = frequency_mapping_dict[self.Frequency]
        except KeyError:
            raise ValueError(f'Incorrect Frequency: {self.Frequency} should be one of {list(frequency_mapping_dict.keys())}')

        try:
            self.T = (datetime.strptime(self.Maturity, '%Y-%m-%d')-datetime.today()).days/365
        except ValueError:
            raise ValueError(f'Incorrect date : {self.Maturity}. Please use YYYY-MM-DD format')

    def _most_recent_business_day():
        ref_date = datetime.today().date()
        while ref_date.weekday() >= 5: 
            ref_date -= timedelta(days=1)
        previous_bd = ref_date-timedelta(days=1)
        data = pd.Series()
        while len(data)==0:
            data = fred.get_series('DGS1', observation_start= previous_bd, observation_end = last_bd)
            previous_bd -= timedelta(days=1)
        
        return ref_date.isoformat(), previous_bd.isoformat()


@dataclass
class Convertible:
    Face_Value: float
    Coupon: float
    Coupon_Frequency : str
    Conversion_Ratio : float
    Conversion_Strike : float 

    First_Coupon_Date : str
    Maturity: str
    Redemption : float
    Underlying_stock_ticker : str
    Day_Count_Convention : Optional[str] = 'ACT/ACT'
    Bond_Currency : Optional[str] = 'EUR'
    Stock_Currency : Optional[str] = 'EUR'
    AI_on_Conversion: Optional[bool] = True

    def conversion_price(self):
        return self.Face_Value/self.Conversion_Ratio
    
    def parity(self):
        #Equivalent value in shares if converted right now
        return None

@dataclass
class Option:
    #Use of abstraction
        S: float
        K: float
        T: float
        sig: float
        r: float

    def d1(self):
        return (np.log(self.S/self.K)+(self.r+(self.sig**2)/2)*self.T)/(self.sig*np.sqrt(self.T))

    def d2(self):
        return self.d1() - self.sig*np.sqrt(self.T)

    #Constant greek across options:
    def gamma(self):
      return norm.pdf(self.d1())/(self.S*self.sig*np.sqrt(self.T))
    
    def vega(self):
      return self.S*np.sqrt(self.T)*norm.pdf(self.d1())
    

class Call(Option):
    
    def price(self):
      return self.S*norm.cdf(self.d1()) - self.K*np.exp(-self.r*self.T)*norm.cdf(self.d2())

    def delta(self):
      return norm.cdf(self.d1())

    def theta(self):
      return -self.S*self.sig*norm.pdf(self.d1())/(2*np.sqrt(self.T)) - self.r*self.K*np.exp(-self.r*self.T)*norm.cdf(self.d2())

    def rho(self):
      return (self.K*self.T*np.exp(-self.r*self.T)*norm.cdf(self.d2()))
