"""
PATRICK CURTAIN

A Library that can decode Altium libraries for basic parameters in Python.
"""
import compoundfiles
import sys
import logging
import re
import os

class _AltiumLib():
    """
    Abstraction of an compound file
    """
    def __init__(self, import_path):
        self.import_path=import_path
        self.name=os.path.basename(import_path)
        self.parts = []
        try:
            self.raw = compoundfiles.CompoundFileReader(import_path)
        except FileNotFoundError:
            logging.error(f"No link found to {import_path}")
            sys.exit(2)
    
    def __str__(self):
        return_str = f"\n{self.name}\nCONTAINS:\n-----"
        for item in self.parts:
            return_str = f"{return_str}\n-{item.name}"
        return return_str

class SchLib(_AltiumLib):
    def __init__(self, import_path):
        super().__init__(import_path)

        # get the symbols out of the library.
        for dir in self.raw.root:
            if self.raw.root[dir.name].isdir:
                files = self.raw.root[dir.name]
                new_symbol = Symbol(dir.name)
                for file in files:
                    data = self.raw.open(self.raw.root[dir.name][file.name])
                    new_symbol.add_data(data.readall())

                self.parts.append(new_symbol)

class PcbLib(_AltiumLib):
    def __init__(self, import_path):
        super().__init__(import_path)

        for dir in self.raw.root:
            new_footprint = Footprint(dir.name, self.raw.root[dir.name])
            self.parts.append(new_footprint)

class _LibPart():
    def __init__(self, name):
        self.name=name
        self.raw = None
        self.update()
    
    def update(self):
        if self.raw != None:
            self.params = self.__parse_subdata(self.raw)
    
    def add_data(self, data: bytes):
        if self.raw != None:
            print(self.raw, "\n", data)
            self.raw = self.raw.join(data)
        else: 
            self.raw = data

    @staticmethod
    def __parse_subdata(data: bytes):
        params = re.findall(r'([^\|]*)=([^\|]*)', data.decode('utf-8', errors="ignore"))
        records = dict()

        groupname = "DEFAULT"
        records[groupname] = {}
        for param in params:
            
            records[groupname].update({param[0]: param[1]})
            
            if "RECORD" in param[0]:
                if f"RECORD_{param[1]}" != groupname:
                    repeats = 0
                    groupname = f"RECORD_{param[1]}"  
                else:
                    repeats = repeats + 1
                    f"{groupname}-{repeats}"
                records[groupname] = {}
        return records

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name
        

class Footprint(_LibPart):
    def __init__(self, name):
        super().__init__(name)

class Symbol(_LibPart):
    def __init__(self, name):
        super().__init__(name)
    