REM Define the path to the main Python script
SET MAIN_FILE=%~dp0main.py

REM Define the path to the configuration file
SET CONFIG_FILE=%~dp0config_private.toml

REM Run the Python script with the specified configuration file
py -3.9 "%MAIN_FILE%" "%CONFIG_FILE%" || (pause)