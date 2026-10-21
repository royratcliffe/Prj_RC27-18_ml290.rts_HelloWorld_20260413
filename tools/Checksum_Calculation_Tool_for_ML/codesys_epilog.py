# -*- coding: utf-8 -*-
from __future__ import print_function
import os
import sys
import subprocess
import warnings

# Suppress deprecation warnings from external tools
warnings.filterwarnings("ignore", category=DeprecationWarning)

try:
    import ConfigParser
except ImportError:
    import configparser as ConfigParser

def error(msg):
    """Print error message and exit."""
    print("[ERROR] %s" % msg)
    sys.exit(1)

def get_script_dir():
    """Return the directory of this script."""
    return os.path.dirname(os.path.abspath(__file__))

def get_path_in_script_dir(filename):
    """Return absolute path for a file in the script directory."""
    return os.path.join(get_script_dir(), filename)

def resolve_relative_to_config(config_dir, path):
    """Resolve a path relative to the config directory."""
    if not path:
        return path
    if os.path.isabs(path):
        return os.path.normpath(path)
    return os.path.normpath(os.path.join(config_dir, path))

def read_config(config_path):
    """Read and validate config.ini."""
    if not os.path.isfile(config_path):
        error("config.ini not found: %s" % config_path)
    config = ConfigParser.ConfigParser()
    if not config.read(config_path):
        error("Failed to read config.ini: %s" % config_path)
    try:
        hexmodx_cmd_raw = config.get("PATHS", "hexmodx_cmd").strip()
        hex_file_raw = config.get("FILES", "hex_file").strip()
    except Exception as e:
        error("Missing required entries in config.ini: %s" % e)
    return hexmodx_cmd_raw, hex_file_raw, os.path.dirname(os.path.abspath(config_path))

def validate_file_exists(path, description):
    """Check if a file exists, else error."""
    if not os.path.isfile(path):
        error("%s not found: %s" % (description, path))

def run_batch(batch_path, hexmodx_cmd, hex_file, working_dir):
    """Run the batch file and print output."""
    cmdline = subprocess.list2cmdline([batch_path, hexmodx_cmd, hex_file])
    print("[INFO] Running batch file...")
    print("[DEBUG] Command line:\n%s" % cmdline)
    print("[DEBUG] Working dir:\n%s" % working_dir)
    
    # Set environment to suppress warnings from HexmodX
    env = os.environ.copy()
    env['PYTHONWARNINGS'] = 'ignore::DeprecationWarning'
    
    try:
        proc = subprocess.Popen(
            cmdline,
            shell=True,
            cwd=working_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env
        )
    except OSError as e:
        error("Failed to start process: %s" % e)
    
    stdout, stderr = proc.communicate()
    
    if stdout:
        print("[STDOUT]")
        try:
            output = stdout.decode('utf-8')
        except Exception:
            output = str(stdout)
        sys.stdout.write(output)
    
    if stderr:
        # Filter out deprecation warnings from stderr
        try:
            stderr_text = stderr.decode('utf-8')
        except Exception:
            stderr_text = str(stderr)
        
        # Remove deprecation warning lines
        filtered_lines = []
        for line in stderr_text.splitlines():
            if 'DeprecationWarning' not in line and 'sys.exc_clear()' not in line:
                filtered_lines.append(line)
        
        if filtered_lines:
            print("\n[STDERR]")
            sys.stdout.write('\n'.join(filtered_lines))
    
    if proc.returncode != 0:
        error("Batch file failed with exit code: %d" % proc.returncode)
    
    print("\n[INFO] Completed successfully!")

def main():
    """Main entry point."""
    script_dir = get_script_dir()
    config_path = get_path_in_script_dir("config.ini")
    batch_path = get_path_in_script_dir("Checksum_Calculation_ML.bat")
    validate_file_exists(config_path, "config.ini")
    validate_file_exists(batch_path, "Batch file")
    hexmodx_cmd_raw, hex_file_raw, config_dir = read_config(config_path)
    hexmodx_cmd = resolve_relative_to_config(config_dir, hexmodx_cmd_raw)
    hex_file = resolve_relative_to_config(config_dir, hex_file_raw)
    validate_file_exists(hexmodx_cmd, "HexmodX tool")
    validate_file_exists(hex_file, "HEX file")
    run_batch(batch_path, hexmodx_cmd, hex_file, script_dir)

if __name__ == '__main__':
    main()