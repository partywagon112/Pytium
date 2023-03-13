import compoundfiles
import re
import logging

# i do not condone this
import warnings
warnings.filterwarnings("ignore")


class AltiumLCompoundTools():
    PARAM_FINDALL_REGEX = r'([^\|]*)=([^\|]*)'

    BANNED_CHARACTERS = ['\\', '/']

    @staticmethod
    def strip_illegal_chars(string:str) -> str:
        for banned_char in AltiumLCompoundTools.BANNED_CHARACTERS:
            string = string.replace(banned_char, '_')
        return string

    @staticmethod
    def read_altium_frame(filestream) -> list:
        length = int.from_bytes(filestream.read(4), 'little')
        data = filestream.read(length -1)
        eof = filestream.read(1)
        if eof.decode() == b'\x00':
            logging.warning("EOF not correctly detected!")
        
        return data
    
    def read_as_parameters(data: bytes) -> list:
        properties_list = re.findall(AltiumLCompoundTools.PARAM_FINDALL_REGEX, data.decode('utf-8', errors="ignore"))
        return properties_list

    @staticmethod
    def locate_dir(compound_file, tree: list):
        """
        A function that returns the location of a compound file and digs until it finds
        the right directory.

        Returns a compoundFileEntity.
        """

        if type(tree) != list:
            tree = [tree]

        return AltiumLCompoundTools.__recurse_dir_tree(compound_file.root, tree)

    @staticmethod
    def __recurse_dir_tree(root, tree: list):
        """
        PASS THE ROOT NOT THE COMPOUND FILE!

        Recursive to dig down and find a relevant directory based
        on a list of folders to get to a file.

        eg __recurse_dir_tree(file, ["ADS1115", "Data"]) -> compountfiles.CompoundFileEntity
        """
        if len(tree) == 1:
            return root[tree[0]]
        
        else:
            next_layer = tree[0]
            tree.remove(next_layer)
            # compoundfiles.reader.CompoundFileReader
            return AltiumLCompoundTools.__recurse_dir_tree(root[next_layer], tree)

class SchematicLibrary():
    LIBREF_NUMBER_REGEX = r'LibRef([0-9]*)'
    
    def __init__(self, path):
        self.properties = dict()

        self.components = dict()

        with compoundfiles.CompoundFileReader(path) as compound_file:

            self.__import_header(compound_file)
        
            self.__get_component_refs(compound_file)

        # get a list from the header with all the parts and their number.
    
    def __get_component_refs(self, compound_file):
        self.components = dict()

        for property_name, property in self.properties.items():
            libref = re.findall(SchematicLibrary.LIBREF_NUMBER_REGEX, property_name)
            if len(libref) > 0:
                # put in the name, the reference in the list, and the number of parts 
                # associated with this one part.
                self.components[property] = SchematicLibraryComponent(
                    name=property, 
                    reference_number=libref[0], 
                    parts_count=self.properties[f"PartCount{libref[0]}"],
                    compound_file = compound_file
                )

    def __import_header(self, compound_file):
            try:
                fileheader_stream = compound_file.open(compound_file.root["FileHeader"])
                data = AltiumLCompoundTools.read_altium_frame(fileheader_stream)
                properties_list = AltiumLCompoundTools.read_as_parameters(data)
                for item in properties_list:
                    self.properties[item[0]] = item[1]
                
                if len(properties_list) != len(self.properties.keys()):
                    logging.warning("During convertion of properties list to dict, there was\
                        a missed entry")
                    # TODO clean up. Don't create an error, fix it.

            except KeyError:
                logging.error(f"Invalid schematic library!")
    
class SchematicLibraryComponent():
    """
    RECORD=1 <- The symbol properties
    
    RECORD=6 <- The properties of a box.
    unmarked 
        it looks like pins are stored as a union of some kind?

    RECORD=34 = Designator Field
    RECORD=41 = Comment Field
    
    """
    def __init__(self, name, reference_number, parts_count=1, compound_file=None, *args, **kwargs):
        self.name = name
        self.reference_number = reference_number
        self.parts_count = parts_count
        
        self.general = kwargs

        dir = compound_file.root[AltiumLCompoundTools.strip_illegal_chars(name)]

        properties_list = []
        self.properties = dict()
        
        for file in dir:
            if file.name == "Data":
                filestream = compound_file.open(dir[file.name])
                
                # get the header first - these are the properties for the symbol.
                data = AltiumLCompoundTools.read_altium_frame(filestream)
                properties_list = AltiumLCompoundTools.read_as_parameters(data)

                drawing = bytearray()
                while(filestream.tell() < dir[file.name].size):
                    drawing.extend(bytearray(AltiumLCompoundTools.read_altium_frame(filestream)))
                
                # then pass all that into the drawing data:
                self.drawing = SchematicLibraryComponentDrawing(data)

            for property in properties_list:
                # we can ignore that one!
                if property[0] != "RECORD":
                    self.properties[property[0]] = property[1]

        records = []
        record_params = []

        for property in properties_list:
            if property[0] == "RECORD":
                # put in the parameter so we can track out what's going on.
                record_params.append(property)
                # fill up the list with the last bit of stuff
                records.append(record_params)
                # dump the list
                record_params.clear()
            else:
                record_params.append(property)

class SchematicLibraryComponentDrawing():
    def __init__(self, drawing_data):
        # this can be treated as a sub frame... almost?
        pass

library = SchematicLibrary("integrated.SchLib")

for name, component in library.components.items():
    print(name)
    print("---")
    for key, value in component.properties.items():
        print(f"{key}={value}")

    print()