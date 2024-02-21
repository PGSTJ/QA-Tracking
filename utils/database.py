import sqlite3 as sl
import os
import traceback
import json
import csv
import datetime
import pandas as pd

from .custom_errors import ProspectiveScribeDivision
# from custom_errors import ProspectiveScribeDivision, DivisionExistenceError

dbf = "QAData.db"
dbp = os.path.abspath(dbf)
conn = sl.connect(dbp, check_same_thread=False)
curs = conn.cursor()



"""
Tables:
- Prospective
- Due

- Scribes
- Abbreviations
- Scribe Data
    - Name
    - Solo date
    - QAT
    - LQA
    - NQA
    - TQA
    - FFTS (meta data)
    - Division(s); str or str list
- QA Tracks
"""


class QAD():
    """ Constructor class for database tables, contains common, basic function """
    EXTRACT_VALUES = 'SELECT name FROM sqlite_master'

    def __init__(self) -> None:
        self.table_name = self.__class__.__name__.lower()

    def post_init(self):
        columns = [column[1] for column in curs.execute(f'PRAGMA table_info({self.table_name})').fetchall()]
        self.values = ','.join(columns)
        self.insert_placeholders = '?,'*(len(columns)-1) + '?'
        return True

    def get_single_value(self, column:str, name:str=None) -> str | int | list:
        """ Get all single column data or specify a name. """
        try:
            if name:
                return [info[0] for info in curs.execute(f'SELECT {column} FROM {self.table_name} WHERE name=?')][0] # str or int
            else:
                return [info[0] for info in curs.execute(f'SELECT {column} FROM {self.table_name}')] # list 
        except Exception as e:
            print('ERROR GETTING COLUMN DATA')
            traceback.print_exc()
            # error handling/catching


    def get_multiple_values(self, columns:list, name:str) -> tuple:
        """ Get data from multiple columns at a specified name. """
        # parse specified columns to SQL format
        try:
            col_names = ''
            for col in columns:
                if len(col_names) == 0:
                    col_names += col
                elif len(col_names) > 0:
                    col_names += f', {col}'

            return [info for info in curs.execute(f'SELECT {col_names} FROM {self.table_name} WHERE name=?', (name,))][0] 
        except Exception as e:
            print('ERROR GETTING MULTIPLE COLUMN DATA')
            traceback.print_exc()
            # error handling/catching

    def drop_table(self):
        curs.execute(f'DROP TABLE {self.table_name}')


class Abbreviations(QAD):
    """
    
    """
    mass_upload_file = 'data\\massUploadAbbreviations.csv'
    def __init__(self) -> None:
        super().__init__()
        curs.execute(f'CREATE TABLE IF NOT EXISTS {self.table_name}(uid TEXT PRIMARY KEY, name TEXT, shortname TEXT)')
        self.post_init()

    def _current_total(self) -> int:
        """  Total number of stored abbreviations/shorthands """
        return len([info[0] for info in curs.execute(f'SELECT uid FROM {self.table_name}')])

    def generate_uid(self, type:str):
        """ UID depends on abbreviation type (division, QAT) """
        match type:
            case 'DIV':
                return f'{self._current_total()}.{self._uid_type_total(type)}.{type}'
            case 'QAT':
                return f'{self._current_total()}.{self._uid_type_total(type)}.{type}'

    def _uid_type_total(self, type:str) -> int:
        """ Total number of abbreviations in a specified abbreviation type """
        return len([info[0] for info in curs.execute(f'SELECT uid FROM {self.table_name}') if type in info[0]])
    
    def add_abbreviation(self, name:str, abbreviation:str, type:str):
        """
        type param options: DIV or QAT
        """
        try:
            uid = self.generate_uid(type)
            curs.execute(f'INSERT INTO {self.table_name}({self.values}) VALUES({self.insert_placeholders})', (uid, name, abbreviation))
            conn.commit()
            return True
        except sl.IntegrityError:
            print('This abbreviation already exists.')
        except Exception:
            print('ERROR ADDING ABBREVIATION')
            traceback.print_exc()

    def mass_upload(self):
        """ Mass Upload abbreviations per CSV data file """
        with open(self.mass_upload_file, 'r') as fn:
            fn.readline()
            for line in csv.reader(fn):
                self.add_abbreviation(line[0], line[1], line[2])
        print('mass upload done')
                    



class ProspectiveQAs(QAD):
    """
    
    """

    def __init__(self) -> None:
        super().__init__()
        curs.execute(f'CREATE TABLE IF NOT EXISTS {self.table_name}(uid TEXT PRIMARY KEY, date VARCHAR(11), scribe TEXT, division VARCHAR(3), assessor TEXT, provider TEXT, comments TEXT, FOREIGN KEY (scribe) REFERENCES scribedata(name), FOREIGN KEY (division) REFERENCES abbreviations(shortname))')
        self.post_init()
        self.RECORD = 'logging\\records\\completedqas.txt'

    def add_prospective(self, scribe:str, date:str, division:str, assessor:str, provider:str, comments:str):
        try:
            if not self._verify_scribedivision(scribe, division):
                raise ProspectiveScribeDivision('This division is not associated with this scribes database profile')
            uid = self.uid_generator(scribe, date, division)
            curs.execute(f'INSERT INTO {self.table_name}({self.values}) VALUES({self.insert_placeholders})', (uid, date, scribe, division, assessor, provider, comments))
            conn.commit()
            return True
        except ProspectiveScribeDivision:
            print('This division is not associated with this scribes database profile')
        except Exception:
            traceback.print_exc()


    def _verify_scribedivision(self, scribe, division:str) -> bool:
        """ verifies that the scribe is the in the division of the prospective QA """
        scribe_div = [info for info in curs.execute(f'SELECT division FROM scribedata WHERE name=?', (scribe,))] # should be documented as 3 letter abbreviation
        if division in scribe_div:
            return True
        else:
            return False
        #TODO might deprecate this too since could also do drop down options when adding prospective

    def _verify_division(self, division:str) -> bool:
        """ verifies that the division exists within scribe coverage """
        #TODO no need to verify - just have drop down option of available divisions when adding prospective




    def uid_generator(self, scribe:str, date:str, division:str):
        name_format = self._uid_name_formatter(scribe)
        date_format = date.split('-')
        return f'{self._total_qas()}.{name_format}.{date_format}.{division}'

    def _total_qas(self) -> int:
        with open(self.RECORD, 'r') as fn:
            return len([line for line in fn])



    @staticmethod
    def _uid_name_formatter(name:str) -> str:
        final = ''
        stepone = name.split(' ')
        for n in stepone:
            final += n[:3]
        return final
    


class DueQAs(QAD):
    def __init__(self) -> None:
        super().__init__()
        curs.execute(f'CREATE TABLE IF NOT EXISTS {self.table_name}(name TEXT PRIMARY KEY, duedate VARCHAR(11), division VARCHAR(3), qan INT)')
        self.post_init()

    def add_due_qa(self, name:str, due_date:str, division:str, qan:int) -> bool:
        curs.execute(f'INSERT INTO {self.table_name}({self.values}) VALUES ({self.insert_placeholders})', (name, due_date, division, qan))
        conn.commit()
        return True


QAT_VALUES = 'data\\qa-tracks.json'

class ScribeData(QAD):
    """
    Class set for the Scribe Data DB table. Contains all function operations used throughout the site. 

    Column parameter values for getting column data:
    - qat
    - lqa
    - nqa
    - tqa
    - ffts
    - division

    """
    QAT_VALUES = 'data\\qa-tracks.json'


    def __init__(self) -> None:
        super().__init__()
        curs.execute(f'CREATE TABLE IF NOT EXISTS {self.table_name}(name TEXT PRIMARY KEY, solo_date VARCHAR(11), qat INT, lqa VARCHAR(11), nqa VARCHAR(11), tqa INT, ffts VARCHAR(3), division TEXT, aqaes VARCHAR(5), qaf VARCHAR(5), qar VARCHAR(5), qats VARCHAR(5), apes VARCHAR(3), assr BOOL)')
        self.post_init()
        
        # print(f'values: {self.values}')
        # print(f'placeholders: {self.insert_placeholders}')
        

    def add_scribe(self, name:str, division:str, qat=None, solo:str=None, ffts:float=None):
        """
        Add a scribe to DB with default values as follows:
        - TQA = 0 | QAT = 9
        - LQA/NQA/FFTS | aQAES/aPES/QATS/QAF/QAR = 'empty_string'
        - ASSR = False
        
        """
        try:
            qat_int, fsd, fffts = self._verify_provided_values(qat, solo, ffts)  
            div_abbrv = self._convert_division(division)

            nqa, fqat = self._derive_nqa(qat_int, fsd)
                
            curs.execute(f'INSERT INTO {self.table_name}({self.values}) VALUES ({self.insert_placeholders})', (name.title(), fsd, fqat, '',nqa, 0, fffts, div_abbrv, '', '', '', '', '', False))
            conn.commit()
        except sl.IntegrityError:
            print('This scribe already exists within the database.')
        except Exception:
            print('ERROR ADDING SCRIBE - ENSURE QAT IS AN INT')
            traceback.print_exc()
            # error handling/catching

    def remove_scribe(self, name:str) -> bool:
        """ Remove specified scribe from database """
        try:
            curs.execute(f'DELETE FROM {self.table_name} WHERE name=?', (name.title(),))
            conn.commit()
            return True
        except Exception as e:
            print('ERROR REMOVING SCRIBE - CHECK SPELLING')
            traceback.print_exc()
            # error handling/catching

    def update_attributes(self, **attribute):
        """
        Updates attributes per specified kwargs

        Available options:
            - solo_date
            - qat
            - ffts
        """

    def _verify_provided_values(self, qat, solo, ffts) -> tuple:
        """ Checks whether an input was provided for QAT or Solo Date, since these are optional initiation parameters """
        qat_exist = [info for info in curs.execute('SELECT name, shortname FROM abbreviations WHERE name=?', (qat,))][0]
        # print(f'qat existence: {qat_exist}')
        if isinstance(qat_exist, tuple):
            final_qat = self._convert_qat(qat_exist[1])
        else:
            final_qat = 9

        if len(solo) > 1:
            final_sd = solo
        else:
            final_sd = ''

        if ffts is None:
            final_ffts = '0.0'
        elif isinstance(ffts, float):
            final_ffts = str(ffts)
        elif isinstance(ffts, str):
            final_ffts = str(ffts)
        

        return final_qat, final_sd, final_ffts
    
    
    def _convert_qat(self, qat_abbr:str) -> int:
        """ Converts QAT description to numerical id, which also happens to be the same as NQA interval factor """
        try:
            with open(self.QAT_VALUES, 'r') as fn:
                all_qatv = json.load(fn)
                qatv = all_qatv[qat_abbr]

                return qatv
        except Exception:
            traceback.print_exc()

    @staticmethod
    def _convert_division(division_longname:str) -> str:
        """ Converts whole division name from form to 3 letter abbreviation, then formats as string list for DB entry """
        return [info[0] for info in curs.execute('SELECT shortname FROM abbreviations WHERE name=?', (division_longname,))][0]
    
    @staticmethod
    def _derive_nqa(qat_value, solo_date):
        """ Calculates next QA date based on QATv, which happens to be the same as the QAT numerical ID """
        if not len(solo_date) > 1:
            qatv = solo_date
            end_format = ''
        else:
            starting = datetime.datetime.strptime(solo_date, '%Y-%m-%d')
            end = pd.Timestamp(starting) + pd.DateOffset(months=int(qat_value))
            end_format = end.strftime('%m-%d-%Y')
            qatv = qat_value
        return end_format, qatv
            
        
class ProviderData(QAD):
    def __init__(self) -> None:
        super().__init__()
        curs.execute(f'CREATE TABLE IF NOT EXISTS {self.table_name}(name TEXT PRIMARY KEY, division TEXT, subspecialty TEXT, FOREIGN KEY(division) REFERENCES abbreviations(shortname))')
        self.post_init()


    def add_provider(self, name:str, division_ln:str) -> bool:
        div_sn:str = [info[1] for info in curs.execute('SELECT name, shortname FROM abbreviations WHERE name=?', (division_ln,))][0]

        curs.execute(f'INSERT INTO {self.table_name}({self.values}) VALUES ({self.insert_placeholders})', (name, div_sn, ''))
        conn.commit()
        return True
        


def load_prospective_qas() -> list[tuple]:
    """ Extracts all entries from prospective QA DB table and formats to display in table """
    return [info for info in curs.execute('SELECT date, scribe, division, assessor, provider, comments FROM prospectiveqas')]

def load_due_qas() -> list[tuple]:
    """ Extracts all entries from due QA DB table and formats to display in table """




def load_divisions() -> list[str]:
    """ Extracts all divisions to display in drop down selections """
    return [info[1] for info in curs.execute('SELECT uid, name FROM abbreviations') if 'DIV' in info[0]]

def load_qa_tracks() -> list[str]:
    """ Extracts QAT longnames to display in drop down selections """
    return [info[1] for info in curs.execute('SELECT uid, name FROM abbreviations') if 'QAT' in info[0]]

def load_scribes() -> list[tuple]:
    """ Extracts all scribes to display in drop down selections; extracts div too for adding prospective QAs """
    return [info for info in curs.execute('SELECT name, division FROM scribedata')]
     


def load_providers() -> list[str]:
    """ Extracts all providers to display in drop down selections """
    

def load_assessors() -> list[str]:
    """ Extracts all eligible QA assessors to display in drop down selections """
    return [info[0] for info in curs.execute('SELECT name FROM scribedata WHERE assr=?', (True,))]
    



def add_division(scribe:str, division_longname:str) -> bool:
    """ Add additional divisions to a scribe profile | considering add scribe profile class, this will be apart of there """
    current_divs:list = [info[0] for info in curs.execute('SELECT division FROM scribedata WHERE name=?', (scribe,))][0].split(', ')
    current_divs.append([info[1] for info in curs.execute('SELECT name, shortname FROM abbreviations WHERE name=?', (division_longname.title(),))][0])
    curs.execute('UPDATE scribedata SET division=? WHERE name=?', (', '.join(current_divs), scribe))
    conn.commit()
    return True

def remove_division(scribe:str, division_longname:str) -> bool:
    """  """
    current_divs:list = [info[0] for info in curs.execute('SELECT division FROM scribedata WHERE name=?', (scribe,))][0].split(', ')
    current_divs.remove([info[1] for info in curs.execute('SELECT name, shortname FROM abbreviations WHERE name=?', (division_longname.title(),))][0])
    curs.execute('UPDATE scribedata SET division=? WHERE name=?', (', '.join(current_divs), scribe))
    conn.commit()
    return True



def _convert_division_long_short(division_ln:str) -> list:
    return [info[1] for info in curs.execute('SELECT name, shortname FROM abbreviations WHERE name=?', (division_ln,))][0]
    
        


def display_scribe_divisions(division_sn:str) -> dict:
    """ Displays all scribes associated with a division """
    scribe_list = [info[0] for info in curs.execute('SELECT name, division FROM scribedata') if division_sn in info[1].split(', ')]
    associated_scibes = [scribe for scribe in scribe_list]
    return {'scribes':associated_scibes} 

def display_providers_divisions(division_sn:str) -> dict:
    """ Displays all providers associated with a division """
    provider_list = [info[0] for info in curs.execute('SELECT name, division FROM providerdata') if division_sn in info[1].split(', ')]
    associated_providers = [provider for provider in provider_list]
    return {'providers': associated_providers}

def prospective_dropdown_display(division_ln:str, type:str):
    """ Displays providers and scribes in pQAF dropdown based on specified division """       
    # convert div long name to shortname (abbreviation)
    div_sn:str = [info[1] for info in curs.execute('SELECT name, shortname FROM abbreviations WHERE name=?', (division_ln.title(),))][0]
    # creates list of all scribes/providers in the specified division
    info = [data for data in [info[0] for info in curs.execute(f'SELECT name, division FROM {type}data') if div_sn in info[1].split(', ')]]
    return {type+'s':info}
        

if __name__ == '__main__':
    d = prospective_dropdown_display('endocrinology', 'provider')
    print(d)
    
