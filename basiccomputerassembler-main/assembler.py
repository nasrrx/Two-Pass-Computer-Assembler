class Assembler(object):
    def __init__(self, asmpath='', mripath='', rripath='', ioipath='') -> None:
        """
        Assembler class constructor.

        Initializes 7 important properties of the Assembler class:
        -   self.__address_symbol_table (dict): stores labels (scanned in the first pass)
            as keys and their locations as values.
        -   self.__bin (dict): stores locations (or addresses) as keys and the binary 
            representations of the instructions at these locations (job of the second pass) 
            as values.
        -   self.__asmfile (str): the file name of the assembly code file. This property
            is initialized and defined in the read_code() method.
        -   self.__asm (list): list of lists, where each outer list represents one line of 
            assembly code and the inner list is a list of the symbols in that line.
            for example:
                ORG 100
                CLE
            will yiels __asm = [['org', '100'] , ['cle']]
            Notice that all symbols in self.__asm are in lower case.
        -   self.__mri_table (dict): stores memory-reference instructions as keys, and their
            binary representations as values.
        -   self.__rri_table (dict): stores register-reference instructions as keys, and their
            binary representations as values.
        -   self.__ioi_table (dict): stores input-output instructions as keys, and their
            binary representations as values.
        
        Thie constructor receives four optional arguments:
        -   asmpath (str): path to the assembly code file.
        -   mripath (str): path to text file containing the MRI instructions. The file should
            include each intruction and its binary representation separated by a space in a
            separate line. Their must be no empty lines in this file.
        -   rripath (str): path to text file containing the RRI instructions. The file should
            include each intruction and its binary representation separated by a space in a
            separate line. Their must be no empty lines in this file.
        -   ioipath (str): path to text file containing the IOI instructions. The file should
            include each intruction and its binary representation separated by a space in a
            separate line. Their must be no empty lines in this file.
        """
        super().__init__()
        # Address symbol table dict -> {symbol: location}
        self.__address_symbol_table = {}
        # Assembled machine code dict -> {location: binary representation}
        self.__bin = {}
        # Label addresses for MRI Usage Later On
        self.__label_addresses = {}
        # Load assembly code if the asmpath argument was provided.
        if asmpath:
            self.read_code(asmpath)   
        # memory-reference instructions
        self.__mri_table = self.__load_table(mripath) if mripath else {}
        # register-reference instructions
        self.__rri_table = self.__load_table(rripath) if rripath else {}
        # input-output instructions
        self.__ioi_table = self.__load_table(ioipath) if ioipath else {}
    

    def read_code(self, path:str):
        """
        opens .asm file found in path and stores it in self.__asmfile.
        Returns None
        """
        assert path.endswith('.asm') or path.endswith('.S'), \
                        'file provided does not end with .asm or .S'
        self.__asmfile = path.split('/')[-1] # on unix-like systems
        with open(path, 'r') as f:
            # remove '\n' from each line, convert it to lower case, and split
            # it by the whitespaces between the symbols in that line.
            self.__asm = [s.rstrip().lower().split() for s in f.readlines()]


    def assemble(self, inp='') -> dict:
        assert self.__asm or inp, 'no assembly file provided'
        if inp:
            assert inp.endswith('.asm') or inp.endswith('.S'), \
                        'file provided does not end with .asm or .S'
        # if assembly file was not loaded, load it.
        if not self.__asm:
            self.read_code(inp)
        # remove comments from loaded assembly code.
        self.__rm_comments()
        # do first pass.
        self.__first_pass()
        # do second pass.
        self.__second_pass()
        # The previous two calls should store the assembled binary
        # code inside self.__bin. So the final step is to return
        # self.__bin
        return self.__bin


    # PRIVATE METHODS
    def __load_table(self, path) -> dict:
        """
        loads any of ISA tables (MRI, RRI, IOI)
        """
        with open(path, 'r') as f:
            t = [s.rstrip().lower().split() for s in f.readlines()]
        return {opcode:binary for opcode,binary in t}


    def __islabel(self, string) -> bool:
        """
        returns True if string is a label (ends with ,) otherwise False
        """
        return string.endswith(',')


    def __rm_comments(self) -> None:
        """
        remove comments from code
        """
        for i in range(len(self.__asm)):
            for j in range(len(self.__asm[i])):
                if self.__asm[i][j].startswith('/'):
                    del self.__asm[i][j:]
                    break

    def __format2bin(self, num:str, numformat:str, format_bits:int) -> str:
        """
        converts num from numformat (hex or dec) to binary representation with
        max format_bits. If the number after conversion is less than format_bits
        long, the formatted text will be left-padded with zeros.
        Arguments:
            num (str): the number to be formatted as binary. It can be in either
                        decimal or hexadecimal format.
            numformat (str): the format of num; either 'hex' or 'dec'.
            format_bits (int): the number of bits you want num to be converted to
        """
        if numformat == 'dec':
            return '{:b}'.format(int(num)).zfill(format_bits)
        elif numformat == 'hex':
            return '{:b}'.format(int(num, 16)).zfill(format_bits)
        else:
            raise Exception('format2bin: not supported format provided.')
    def __is_pseudo_instruction(self, opcode: str) -> bool:
        """
        Checks if the opcode is a pseudo instruction.
        Pseudo instructions include 'ORG', 'END', etc.
        """
        pseudo_instructions = ['org', 'end', 'dec']  # Add all pseudo instructions here, except HEX as it is already handled in first pass
        return opcode.lower() in pseudo_instructions
    def __first_pass(self) -> None:
        """
        Runs the first pass over the assembly code in self.__asm.
        Should search for labels and store the labels alongside their locations in
        self.__address_symbol_table. The location must be in binary (not hex or dec).
        Returns None
        """
        current_location = 0  # LC == 0

        for line in self.__asm: # Scan Lines of code.
            if line:
                opcode = line[0] # Operation code is always the first element in the line

                if self.__islabel(opcode):  # Check if opcode a label
                    # If the line has a label
                    label = opcode[:-1]  # Remove the comma from the label

                    if(line[1] != "hex"): # If not HEX, take the instruction AFTER the label and convert it to binary directly
                        self.__address_symbol_table[self.__format2bin(str(current_location), 'dec',12)] = line[1]
                        self.__label_addresses[label] = str(current_location) # Will be used in getting addresses for MRIs

                    else: # In the HEX case, a hexadecimal number is the 3rd element in the line. accessing it directly and changing it is the most effecient approach
                        self.__address_symbol_table[self.__format2bin(str(current_location), 'dec',12)] = self.__format2bin(line[2], 'hex', 16)
                        self.__label_addresses[label] = str(current_location) # Will be used in getting addresses for MRIs


                else:
                    # If the line doesn't have a label
                    if opcode == 'org':
                        # ORG instruction found
                        current_location = int(line[1], 16) # set the current location to the ORG number, the 16 is added to convert from HEX to DEC ( Base 16 )
                        continue # skip the rest of the loop ( Don't increment the )

                    elif opcode == 'end':
                        # END instruction found, exit the first pass
                        break

                    else:
                        self.__address_symbol_table[self.__format2bin(str(current_location), 'dec',12)] = line[0] # Saving MRIs

                current_location += 1 # Increment the current location for the next instruction
    def __second_pass(self) -> None:
        current_location = 0  # LC = 0

        # Update the address symbol table with the converted values ( IOI and RRI )
        for key in list(self.__address_symbol_table.keys()):
            value = self.__address_symbol_table[key]

            if value in self.__rri_table:
                self.__address_symbol_table[key] = self.__rri_table[value] # RRI Values Handling, get binary equivlaent and set it directly

            if value in self.__ioi_table:
                self.__address_symbol_table[key] = self.__ioi_table[value] # IOI Values Handling, get binary equivlaent and set it directly

        for line in self.__asm:  # Scan lines of code.
            if line:
                opcode = line[0]

                # Handle pseudo instructions
                if self.__is_pseudo_instruction(opcode): # Check for pseudo instructions
                    if opcode.lower() == "org":
                        current_location = int(line[1], 16)
                        continue # skip the rest of the loop

                    elif opcode.lower() == "end":
                        print(self.__address_symbol_table) # Prints the
                        self.__bin = self.__address_symbol_table # Pass the address symbol table to the self bin, finalizing the assemble program.
                        break # End App
                    else:
                        print("OTHER PSUEDO INSTRUCTIONS, ALREADY HANDELED")

                else: # Not Psuedo Instructions ( MRIs,IOIs,RRIs Or Other )

                    # Check if this is an MRI instruction
                    if opcode.lower() in self.__mri_table:

                        binary_instruction = '0' * 16 # The binary instructions is always 16 bits

                        operation_code = self.__mri_table[opcode.lower()]  # Get the 3-bit code from the MRI table

                        binary_address = self.__format2bin(self.__label_addresses[line[1]], 'dec', 12) # 12 Bit Code Address, MRI Instructions always has a label next to them, we get that label address and set it to the binary_address

                        if 'I' in opcode:  # Better to check in opcode for 'I' condition
                            directness = '1' # Addressing Mode Indirect
                        else:
                            directness = '0' # Addressing Mode direct


                        binary_instruction = directness + operation_code + binary_address # 1-Bit Directness + 3-Bit MRI Code + 12-Bit Label/Binary Address

                        self.__address_symbol_table[self.__format2bin(str(current_location), 'dec',12)] = binary_instruction # From the current address, we'll convert the MRI instructions to binary

                # Increment LC for the next instruction
                current_location += 1