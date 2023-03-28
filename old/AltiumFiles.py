import compoundfiles
import compoundfiles.entities

class Frame():
    def __init__(self, length, data, eof):
        self.length = length
        self.data = data
        self.eof = eof

class File():
    """
    A file contained within the compound binary file with data to be parsed.

    The data contained with in a file is itself sectioned up into frames.

    We return a dictionary of frames, that themselves contain
    a dictionary of parameters contained within that subrecord.

    How these records are to be treated will depend on the file type.
    """
    SIZE_PREFIX_LENGTH = 4

    def __init__(self, compound_file, tree: list = ["FileHeader"]):

        file_location = File.locate_dir(compound_file, tree)
        stream = compound_file.open(file_location)

        # self.frames = dict()
        self.frames = []

        while(stream.tell() < file_location.size):
            length = int.from_bytes(stream.read(File.SIZE_PREFIX_LENGTH), 'little')
            data = stream.read(length)
            eof = stream.read(1)

            # self.frames["key"]
            self.frames.append(Frame(length, data, eof))
        
    
    @staticmethod
    def locate_dir(compound_file, tree: list):
        """
        A function that returns the location of a compound file and digs until it finds
        the right directory.

        Returns a compoundFileEntity.
        """

        if type(tree) != list:
            tree = [tree]

        return File.__recurse_dir_tree(compound_file.root, tree)
        
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
            return File.__recurse_dir_tree(root[next_layer], tree)
        
class SchLib():
    def __init__(self, file_location):
        """
        Entry point for an altium compound document.
        """

        self.header = dict()
        self.components = dict()

        with compoundfiles.CompoundFileReader(file_location) as compound_file:
            # treat each folder a a new opening point
            for entry in compound_file.root:
                entry: compoundfiles.entities.CompoundFileEntity
                if entry.isfile:
                    self.header[entry.name] = File(compound_file, entry.name)
                else:
                    self.components[entry.name] = []
                    for subentry in entry:
                        # for the subfolder, create a list for every dictionary entry.
                        self.components[entry.name].append(File(compound_file, [entry.name, subentry.name]))
                    

mySchLib = SchLib("integrated.SchLib")

for component_name, component in mySchLib.components.items():
    print("-----")
    print(component_name)

    for file in component:
        for frame in file.frames:
            print()
            print(frame.data)
    print("-----")