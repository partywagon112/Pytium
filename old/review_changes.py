import logging
import pandas
import os
import Pytium
import sys

LIBRARY_PATH = "./ts_standard_library.xlsx"

DEFAULT_SYMBOL_DIR = "Symbols"
DEFAULT_FOOTPRINT_DIR = "Footprints"

WHITESPACE_REGEX = r'^\s|\s$'

# Default component library names and correct designator.
DEFAULT_DESIGNATOR_ASSIGNMENT = {
    "Resistors": "R",
    "Capacitors": "C",
    "Inductors": "L",
    "Diodes": "D",
    "LEDs": "D",
    "Crystals": "X",
    "Transistors": "Q",
    "Relays": "K",
    "Integrated": "U",
    "Fuses": "F"
}

def import_database_libraries(library_path) -> dict[pandas.DataFrame]:
    """
    Import the database library that controls
    """

    library_dict = {}
    
    xlsx = pandas.ExcelFile(library_path)
    sheet_names = xlsx.sheet_names

    for sheet_name in sheet_names:
        library_dict[sheet_name] = pandas.read_excel(library_path, sheet_name=sheet_name)

    return library_dict

def import_dependencies(database_libraries: dict) -> dict:
    """
    Import the libraries referenced by the excel sheet. 

    These are stored in an MS Compound file, and very basic exporting can 
    be done to bring them out.

    Returns dict of reference files using the CompoundFileEntity type
    """

    depend_dict = {}
    
    for database_name, database_library in database_libraries.items():
        database_library: pandas.DataFrame
        symbol_import_paths = database_library["Library Path"].unique()
        for import_filename in symbol_import_paths:
            Pytium.SchLib(os.path.join(DEFAULT_SYMBOL_DIR, import_filename))
    
    for database_name, database_library in database_libraries.items():
        database_library: pandas.DataFrame
        footprint_import_paths = database_library["Footprint Path"].unique()
        for import_filename in symbol_import_paths:
            Pytium.PcbLib(os.path.join(DEFAULT_FOOTPRINT_DIR, import_filename))
                
    return depend_dict

def check_whitespace(database_libraries: dict, replace: bool=True) -> bool:
    """
    Replaces part numbers with detected whitespace.

    Returns true on success
    """
    success = True

    for database_name, database_library in database_libraries.items():
        database_library: pandas.DataFrame
        failed = database_library.stack()[database_library.stack().str.contains(WHITESPACE_REGEX)]

        if len(failed.index) > 0:
            success = False
            logging.warning(f"\"{database_name}\" contains invalid whitespaces")
        
            if replace is True:
                logging.info(f"Replacing whitespace at start/end of entry.")
                database_library.replace(WHITESPACE_REGEX, value="", regex=True, inplace=True)
    
    return success

# def check_designator(database_libraries: dict, symbol_lib) -> list[str]:
#     """
#     Checks component designators are appropirate for nominated
#     components.

#     Also checks if the 
#     """
#     for database_name, database_library in database_libraries.items():
#         database_library: pandas.DataFrame

#         # get the appropriate designator
#         designator = DEFAULT_DESIGNATOR_ASSIGNMENT[database_name]

def check_references(database_libraries: dict, dependencies: dict) -> bool:
    """
    Checks that the references that have been specified in the xlsx are present in 
    the reference databases.
    """
    success = True

    for database_name, database_library in database_libraries.items():
        database_library: pandas.DataFrame
        # group by the symbol library first
        
        for symbol_library_name, symbol_library in database_library.groupby("Library Path"):
            for symbol in symbol_library["Library Ref"].unique():
                try:
                    if symbol not in dependencies[symbol_library_name].subitems:
                        success = False
                        logging.warning(f"\"{symbol}\" is not contained within \"{symbol_library_name}\"!")
                    else:
                        logging.debug(f"\"{symbol}\" found in \"{symbol_library_name}\"")
                except KeyError:
                    logging.error(f"No library found named \"{symbol_library_name}\"")
                    sys.exit(2)
        
def update_price_information(database_libraries: dict) -> bool:
    """
    Updates pricing and available quantity information from Digikey/Mouser

    Returns success status.
    """
    success = True

    return success

def main():

    print("Starting")

    logging.basicConfig(level=logging.DEBUG)

    library = import_database_libraries(LIBRARY_PATH)
    dependencies = import_dependencies(library)

    check_whitespace(library)

    check_references(library, dependencies)

    print("Done!")

if __name__ == "__main__":
    main()