import ConfigParser
import os
import subprocess

def parse_hex_line(line):
    """
    Parses an Intel HEX line and returns its components.
    """
    if line[0] != ":":
        raise ValueError("Invalid Intel HEX line")
    
    byte_count = int(line[1:3], 16)
    address = int(line[3:7], 16)
    record_type = int(line[7:9], 16)
    data = line[9:-2]
    checksum = int(line[-2:], 16)
    return byte_count, address, record_type, data, checksum


def calculate_checksum(byte_count, address, record_type, data):
    """
    Calculates the checksum for an Intel HEX line.
    """
    checksum_data = (
        [byte_count]
        + [address >> 8, address & 0xFF]
        + [record_type]
        + [int(data[i:i+2], 16) for i in range(0, len(data), 2)]
    )
    checksum = (-(sum(checksum_data) & 0xFF)) & 0xFF
    return checksum

def get_config_file_for_hex():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, 'config.ini')

def read_config_for_hex(config_file_path):
    """Read the configuration file and return the configparser object."""
    config_for_hex = ConfigParser.ConfigParser()
    try:
        config_for_hex.read(config_file_path)
        return config_for_hex
    except IOError:
        print("Error: The configuration file '{}' does not exist.".format(config_file_path))
        return None

def get_hex_file_path_from_config(config_for_hex):
    try:
        return config_for_hex.get('CONFIGURATION', 'BDS_MEM_ASW_DS_PATH')  # Access the 'command' option under 'settings' section
    except ConfigParser.NoOptionError as e:
        print("Error: Missing configuration option 'command' in 'settings' section: {}".format(e))
    except ConfigParser.NoSectionError as e:
        print("Error: Missing section 'settings' in config file: {}".format(e))
    return None 
    
def sort_and_process_hex(hex_file):
    """
    Sorts an Intel Hex file by record type 4, appends zeros to the line before a specific address
    (variant-specific fixed address) if it has less than 32 bytes, recalculates the checksum, and writes the result.
    """
    # Define fixed addresses for variants
    fixed_addresses = {
        "variant1": ":020000048080FA",
        "variant2": ":02000004093CB5",
    }

    # Define variant identification patterns
    variant_patterns = {
        ":02000004800C6E": "variant1",
        ":020000040902EF": "variant2",
    }

    # Read the input file lines
    with open(hex_file, "r") as infile:
        lines = infile.readlines()

    if not lines:
        raise ValueError("Input file is empty.")

    # Determine the variant based on the first line
    first_line = lines[0].strip()
    variant = variant_patterns.get(first_line)
    if not variant:
        raise ValueError("Unknown first line: {}".format(first_line))

    fixed_address = fixed_addresses[variant]

    sorted_blocks = []  # To store blocks grouped by type 4
    current_block = []
    extended_address = 0

    for line in lines:
        if line.startswith(":02000004"):  # Detect record type 4
            if current_block:
                sorted_blocks.append((extended_address, current_block))
                current_block = []
            extended_address = int(line[9:13], 16)
            current_block.append(line)
        elif line.startswith(":00000001"):  # Record type 1 (EOF)
            if current_block:
                sorted_blocks.append((extended_address, current_block))
            current_block = [line]  # EOF as a separate block
        else:
            current_block.append(line)

    # Sort the blocks based on the extended linear address
    sorted_blocks.sort(key=lambda x: x[0])

    # Flatten the sorted blocks into a single list of lines
    sorted_lines = []
    for _, block in sorted_blocks:
        sorted_lines.extend(block)

    # Process the line before the fixed address
    for i, line in enumerate(sorted_lines):
        if line.strip() == fixed_address:
            if i > 0:  # Ensure there is a line before the fixed address
                prev_line = sorted_lines[i - 1].strip()

                # Parse the previous line
                byte_count, address, record_type, data, checksum = parse_hex_line(prev_line)

                # Check if it's a data record and less than 32 bytes
                if record_type == 0 and byte_count < 32:
                    # Append zeros to make it 32 bytes
                    data = data.ljust(32 * 2, "0")
                    byte_count = 32

                    # Recalculate the checksum
                    new_checksum = calculate_checksum(byte_count, address, record_type, data)

                    # Create the updated line
                    updated_line = ":{:02X}{:04X}{:02X}{}{:02X}".format(byte_count, address, record_type, data, new_checksum)
                    sorted_lines[i - 1] = updated_line + "\n"

            break

    # Write the processed lines to the output file
    with open(hex_file, "w") as outfile:
        outfile.writelines(sorted_lines)

    # Ensure the file ends with the proper EOF record
    with open(hex_file, "a") as f:
        f.write(":00000001FF\n")

    print("Processed Intel Hex file saved to: {}".format(hex_file))

def get_config_file_path_for_bat():
    """Retrieve the dynamic path to the configuration file."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, 'FlashingUtilities\python_script_config.ini')

def read_config_for_bat(config_file_path):
    """Read the configuration file and return the configparser object."""
    config = ConfigParser.ConfigParser()
    try:
        config.read(config_file_path)
        return config
    except IOError:
        print("Error: The configuration file '{}' does not exist.".format(config_file_path))
        return None

def get_batch_file_path(config):
    """Retrieve the batch file path from the configuration file."""
    try:
        return os.path.join(os.path.abspath(os.path.dirname(__file__)), config.get('SETTING', 'BDS_FLASH_BAT_PATH'))  # Access the 'command' option under 'settings' section
    except ConfigParser.NoOptionError as e:
        print("Error: Missing configuration option 'command' in 'settings' section: {}".format(e))
    except ConfigParser.NoSectionError as e:
        print("Error: Missing section 'settings' in config file: {}".format(e))
    return None

def execute_batch_file(bat_file_path):
    """Execute the batch file if it exists."""
    if os.path.exists(bat_file_path):
        try:
            os.chdir(os.path.dirname(bat_file_path))
            os.system('cmd.exe /k ' + bat_file_path + ' & pause')
        except Exception as e:
            print("Error while executing the batch file:", e)
    else:
        print("Error: The batch file does not exist at path:", bat_file_path)

def execute_batch_file_from_config():
    """Main function to coordinate reading config and executing batch file."""
    # Get the path to the config file for hex file dynamically
    config_file_path_for_hex=get_config_file_for_hex()

    config_for_hex=read_config_for_hex(config_file_path_for_hex)

    hex_file=get_hex_file_path_from_config(config_for_hex)

    # output_file=input_hex_file

    sort_and_process_hex(hex_file)

    # Get the path to the config file dynamically
    config_file_path = get_config_file_path_for_bat()

    # Read the configuration file
    config = read_config_for_bat(config_file_path)
    if not config:
        return

    # Get the batch file path
    bat_file_path = get_batch_file_path(config)
    if not bat_file_path:
        return

    # Execute the batch file
    execute_batch_file(bat_file_path)

if __name__ == "__main__":
    #current_dir = os.getcwd()
    print(os.getcwd())
    execute_batch_file_from_config()
    #os.chdir(current_dir)
