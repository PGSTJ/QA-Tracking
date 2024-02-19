import sqlite3 as sl
import os
import traceback
import json

# from .custom_errors import ProspectiveScribeDivision
from custom_errors import ProspectiveScribeDivision

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
        x = len([info for info in curs.execute(f'SELECT uid FROM {self.table_name}') if type in info])
        print(x)
        return x
    
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
    def __init__(self) -> None:
        super().__init__()
        curs.execute(f'CREATE TABLE IF NOT EXISTS {self.table_name}(name TEXT PRIMARY KEY, solo_date VARCHAR(11), qat INT, lqa INT, nqa VARCHAR(11), tqa INT, ffts VARCHAR(3), division TEXT)')
        self.post_init()
        
        # print(f'values: {self.values}')
        # print(f'placeholders: {self.insert_placeholders}')
        

    def add_scribe(self, name:str, qat:int, division:str, solo:str=None):
        """
        Add a scribe to DB with default values as follows:
        - LQA/TQA = 0
        - NQA/FFTS = 'empty_string'
        
        """
        try:
            if solo:
                val = solo
            else:
                val = ''    
                
            curs.execute(f'INSERT INTO {self.table_name}({self.values}) VALUES ({self.insert_placeholders})', (name.title(), val, qat, 0, '', 0, '', division))
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



        

if __name__ == '__main__':
    f = Abbreviations()
    e = ScribeData()
    d = ProspectiveQAs()
    print('done')
    
