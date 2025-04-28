import pandas as pd


class GLAD():
  '''
  https://glad.umd.edu/ard/home
  '''
  _base_url = "https://glad.umd.edu/"
  _interval_id_url = f'{_base_url}/users/Potapov/ARD/16d_intervals.xlsx'
  
  def __init__(self):
    self.get_interval_table()

  def get_interval_table(self):
    '''
    Get the 16 day interval table from GLAD.
    '''
    if not hasattr(self, '_interval_table'):
      print('Downloading interval table from GLAD...')
      self._interval_table = pd.read_excel(self._interval_id_url, sheet_name='16d interval ID', 
                                            header=1, index_col='Year')
      interval_dates = pd.read_excel(self._interval_id_url, sheet_name='16d interval dates',
                                            index_col='Interval ID')['end Date'].to_list()
      
      self._interval_dates = self._interval_table.copy().astype('str')
      for index, _ in self._interval_dates.iterrows():
        self._interval_dates.loc[index] = interval_dates.copy()
      self._interval_dates = self._interval_dates.astype('datetime64[ns]')
                                            
    return self._interval_table, self._interval_dates