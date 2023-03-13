from Pytium import SchLib
import compoundfiles
import olefile
import compoundfiles
import compoundfiles.entities

import binascii

# library = SchLib()

# library.parts[0]

IMPORT_PATH = "Symbols\\integrated.schlib"

PARAM_FINDALL_REGEX = r'([^\|]*)=([^\|]*)'

"""
AltiumLibDoc
    - FileHeader
        - Root parameters
        - [] Lib References
    - Lib Reference
        - Root parameters
        - Frame
        - [] Components - Records


"""


class Libread():
    def __read(self, import_path):
        with compoundfiles.CompoundFileReader(import_path) as file:

            file = AltiumFrame(file.root)
    
    @staticmethod
    def parse_params(data):
        """
        Applys a regex to capture all parameter information. 

        Assumes UTF-8 being used.

        Returns a tuple (Parameter, Value)
        """
        parameters = dict()
        for parameter in re.findall(r'([^\|]*)=([^\|]*)', data.decode('utf-8', errors="ignore")):
            parameters[parameter[0]] = parameter[1]

        return parameters
    
class FileHeaderReference():
    """
    A reference to an object (Another file) contained within the header.
    """
    def __init__(self, LibRef, PartCount):
        self.LibRef = LibRef
        self.PartCount = PartCount

class FileHeader():
    """
    The FileHeader object is contained in the root directory and refers to how
    what is contained within the entire object.
    """
    def __init__(self, parameters: dict):
        self.components = dict()

        self.header = parameters.pop("HEADER")

        for parameter_name, parameter in parameters:
            reference_number = re.findall(r'Libref([0-9*]))', parameter_name)
            if reference_number != None:
                self.components[parameter] = FileHeaderReference(parameter, parameters[f"PartCount{reference_number}"])

class File():
    def __init__(self, compound_file, tree: list = ["FileHeader"]):
        
        compound_file.open(File.dir_tree(compound_file, tree))
        
    @staticmethod
    def dir_tree(root, tree: list):
        """
        Recursive to dig down and find a relevant directory based
        on a list of folders to get to a file.

        eg dirtree(file, ["ADS1115", "Data"]) -> compountfiles.CompoundFileEntity
        """
        if type(tree) != list:
            tree = [tree]
        
        next_layer = tree[0]
        if len(tree) == 1:
            return root[next_layer]
        else:
            tree.remove(next_layer)
            return File.dir_tree(root[next_layer], tree)

class Frame():
    """
    A frame is a length of data stored within a filestream. It is not the
    entire file.

    [0:4]   Frame length (little endian) The number of bytes s
    [4:-1]  Parameters for the record stored as a 
    [:1]    EOF 0x00
    """
    SIZE_PREFIX_LENGTH = 4

    def __init__(self, name, length, data):
        self.length = length
        # parameters is a list that needs to be sorted through
        # how this is handled, depends on the file.
        parameters = Libread.parse_params(data)

    @classmethod
    def import_frame(cls, name, compound_file: compoundfiles.CompoundFileEntity, compound_directory, start_byte = 0):
        """
        Imports a particular filestream document from a raw value.

        Inefficient for batch operations, but useful for individual reads.
        """
        filestream = compound_file.open(compound_directory)

        filestream.read(start_byte)
        
        # Length assigned to the first few bytes.
        length = int.from_bytes(filestream.read(Frame.SIZE_PREFIX_LENGTH), 'little')
        
        # Read the rest of the string, except the last character, this is a zero.
        data:bytes = filestream.read(length - 1)

        eof = filestream.read(1)
            
        return cls(name, length, data)
    
    def __str__(self):
        return (
            # f"HEADER=\"{self.header}\"\n" +
            f"LEGNTH={self.length}\n" 
            # f"PARAMETERS={self.parameters}"
        )

with compoundfiles.CompoundFileReader(IMPORT_PATH) as file:
    document = file.open(file.root["FileHeader"])
    document = Frame.import_frame("FileHeader", file, file.root["FileHeader"])

    print(document)

    print(type(file.root["FileHeader"]))
    # print(document.parameters)

    new_doc = File(file, ["ADS1115", "Data"])