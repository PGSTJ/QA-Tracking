import sqlite3 as sl
import os
import traceback
import json
import csv
import datetime
import pandas as pd

from .custom_errors import ProspectiveScribeDivision, DivisionExistenceError, ScribeNameExistenceError, MultipleDivisionInputs
# from custom_errors import ProspectiveScribeDivision, DivisionExistenceError, ScribeNameExistenceError, MultipleDivisionInputs

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
        conn.commit()

    @staticmethod
    def division_conversion(division_longname:str=None, division_shortname:str=None) -> str:
        """ Converts from division long name to the short, abbreviation, and vice versa - based on what value is provided """

        # check to ensure two values are not provided
        if division_longname and division_shortname:
            raise MultipleDivisionInputs('Provide only either the long name or the abbreviation, not both.')
        
        elif isinstance(division_longname, str):
            return [info[0] for info in curs.execute('SELECT shortname FROM abbreviations WHERE name=?', (division_longname,))][0]
        elif isinstance(division_shortname, str):
            return [info[0] for info in curs.execute('SELECT name FROM abbreviations WHERE shortname=?', (division_shortname,))][0]



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
            div_sn = self.division_conversion(division_longname=division)
            uid = self.uid_generator(scribe, date, div_sn)
            with open(self.RECORD, 'w') as fn:
                fn.write(uid)
            curs.execute(f'INSERT INTO {self.table_name}({self.values}) VALUES({self.insert_placeholders})', (uid, date, scribe, div_sn, assessor, provider, comments))
            conn.commit()
            return True
        except ProspectiveScribeDivision:
            print('This division is not associated with this scribes database profile')
        except Exception:
            traceback.print_exc()

    def uid_generator(self, scribe:str, date:str, division:str):
        name_format = self._uid_name_formatter(scribe)
        date_format = ''.join(date.split('-'))
        
        return f'{self._total_qas()}.{name_format}.{date_format}.{division}'

    def _total_qas(self) -> int:
        return len([info for info in curs.execute(f'SELECT uid FROM {self.table_name}')])



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
            
        
class ScribeProfile(ScribeData):
    """ Intermediary user to database manipulation of scribe data. Each object pertains to one scribe profile, with all associated functions for manipulating a profile. """
    def __init__(self, scribe_name:str) -> None:
        super().__init__()
        
        scribe_data = [info for info in curs.execute('SELECT name, solo_date, qat, lqa, nqa, tqa, ffts, division, aqaes, qaf, qar, qats, apes, assr FROM scribedata WHERE name=?', (scribe_name.title(),))][0]
        if len(scribe_data) < 4:
            # print(f'SCRIBE DATA: {scribe_data}')
            raise ScribeNameExistenceError('Scribe name doesn\'t exist, check spelling again')

        self.name = scribe_data[0]
        self.solo_date:str = scribe_data[1]
        self.qat:int = scribe_data[2]
        self.lqa:str = scribe_data[3]
        self.nqa:str = scribe_data[4]
        self.tqa:float = scribe_data[5]
        self.ffts:float = scribe_data[6]
        self.divisions:list = scribe_data[7].split(', ')
        self.aqaes:float = scribe_data[8]
        self.qaf:float = scribe_data[9]
        self.qar:float = scribe_data[10]
        self.qats:float = scribe_data[11]
        self.apes:float = scribe_data[12]
        self.assr:bool = scribe_data[13]

    
    def remove_scribe(self) -> bool:
        """ Remove scribe from database """
        try:
            curs.execute(f'DELETE FROM {self.table_name} WHERE name=?', (self.name,))
            conn.commit()
            return True
        except Exception as e:
            traceback.print_exc()
            # error handling/catching

    def get_solo_date(self) -> str:
        """ The date this scribe starting doing solo shifts """
        return self.solo_date

    def current_qat(self) -> int:
        """ Retrieves this users current QA Track, default_best=3 """
        return self.qat
    
    def last_qa(self) -> str:
        """ Retrieves the date of this users last QA """
        return self.lqa
    
    def next_qa(self) -> str:
        """ Retrieves the date of this users next QA, which is calculated based on the current QAT """
        return self.nqa
        
    def total_qas(self) -> float:
        """ Retrieves the total number of QAs this user has had """
        return self.tqa

    def final_training_score(self) -> float:
        """ The training score of this users last FT (either 5 or 6) per the trainer feedback form, max=5 """
        return self.ffts
    
    def average_qa_evaluation_score(self) -> float:
        """ The average score of all QA evaluations for this user, max=10 """
        return self.aqaes
    
    def qa_rating(self) -> float:
        """ 
        Overall rating for a scribe based on their QA performance, derived by combining the QATS (default max score=3) with the average QAES (max score=10). 
        
        The default max score is 13, however can be variable since the QATS contains a subjective measurement affecting its max score therefore, QARm will be defined to explicitly define the max score. """
        return self.qar
    
    def qat_score(self) -> float:
        """ Quantifies a scribes QAT history into a score, no greater than the highest QAT type value (default=3). This is used to derive the QA Rating (QAR) """
        return self.qats
    
    def provider_evaluation(self) -> float:
        """ An average of each category in the the providers ACE evaluation, max=5 """
        return self.apes

    def all_divisions(self) -> list:
        """ Retrieves collection of all divisions associated with this scribe """
        return self.divisions
    
    def assessor_status(self) -> bool:
        """ Verifies whether this user is registered as a QA Assessor """
        return self.assr


    def update_solo_date(self, new_solo_date:str) -> bool:
        """ Updates the registered solo date for this scribe """
        self.solo_date = new_solo_date
        print(f'solo date updated: {new_solo_date}')
        return True
    
    def update_qat(self, new_qat:int) -> bool:
        """ Updates the QAT with the specified QAT """
        if isinstance(new_qat, int):
            self.qat = new_qat
            print(f'QAT updated: {new_qat}')
            return True
        else:
            print(f'NEW QAT: {new_qat}')
            # TODO make custom error to raise -> Please enter whole numbers only (consider making customizable setting??? lol)
            return False

    def update_provder_evaluation_score(self, new_pes:float) -> bool:
        """ Updates the current provider evaluation score """
        if isinstance(new_pes, float) or isinstance(new_pes, int):
            self.apes = new_pes
            print(f'PES udpated: {new_pes}')
            return True
        else:
            print(f'PES update failed; NEWPES:{new_pes}')
            return False
    
    def set_assessor(self) -> bool:
        """ Sets this scribe as a QA Assessor """
        self.assr = True
        return True

    def add_division(self, division_longname:str) -> bool:
        """ Add additional divisions to a scribe profile """
        try:
            division_sn = [info[1] for info in curs.execute('SELECT name, shortname FROM abbreviations WHERE name=?', (division_longname.title(),))][0]
            # verifies whether the specified division is already associated with this scribe
            if division_sn not in self.divisions:
                self.divisions.append()
                print(f'div added')
                return True
            elif division_sn in self.divisions:
                print(f'div already in there')
                # custom error handling
            else:
                print(f'something else wrong with adding division')
                # custom error handling
        except Exception:
            traceback.print_exc()
            # custom error handle -> division doesn't exist, check spelling

    def remove_division(self, division_longname:str) -> bool:
        """ Remove specified divisions from this scribes associations """
        try:
            self.divisions.remove([info[1] for info in curs.execute('SELECT name, shortname FROM abbreviations WHERE name=?', (division_longname.title(),))][0])
            print(f'div removed')
            return True
        except Exception:
            traceback.print_exc()
            # custom error handle -> division doesn't exist, check spelling


    def add_final_training_score(self, ffts:float) -> bool:
        """ Adds a final FT score to scribe profile if one doesn't already exist; updating isn't allowed """
        try:
            float(self.ffts)
            self.ffts = ffts
            print(f'FFTS updated to: {ffts}')
        except Exception:
            # error handle -> if ffts cant be converted to float/int
            traceback.print_exc()

            

    def add_qa_report(self):
        """ Upload results of QA evaluation to add data """
        # for future

    
    def save_changes(self) -> bool:
        """ Saves all recently made changes (since last save) by pushing all changes to database """
        try:
            curs.execute('UPDATE scribedata SET solo_date=?, qat=?, ffts=?, division=?, apes=?, assr=? WHERE name=?', (self.solo_date, self.qat, self.ffts, ', '.join(self.divisions), self.apes, self.assr, self.name))
            conn.commit()
            return True
        except Exception:
            traceback.print_exc()
            # custom error handline


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
    ProspectiveQAs()
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

def prospective_dropdown_display(division_sn:str):
    """ Displays providers and scribes in pQAF dropdown based on specified division """       
    # creates list of all scribes/providers in the specified division
    scribes = [data for data in [info[0] for info in curs.execute(f'SELECT name, division FROM scribedata') if division_sn in info[1].split(', ')]]
    providers = [data for data in [info[0] for info in curs.execute(f'SELECT name, division FROM providerdata') if division_sn in info[1].split(', ')]]
    return {'scribes':scribes, 'providers':providers}
        

if __name__ == '__main__':
    d = ScribeProfile('Therry Malone')
    d.set_assessor()
    e = d.save_changes()
    if e:
        print('updated')
    
