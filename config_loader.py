import os
import sys
import yaml
import logging

def load_config(config_file='./config/config.yaml'):
    # Check if config file exists
    if not os.path.exists(config_file):
        logging.error(f"Configuration file not found: {config_file}")
        logging.error("Performing graceful shutdown due to missing configuration.")
        print(f"Error: Configuration file {config_file} does not exist.")
        sys.exit(1)

    try:
        with open(config_file, 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)

        # Nastavení úrovně logování z konfigurace
        log_level = config.get('logging', {}).get('level', 'INFO')
        
        # Mapování textové úrovně na úroveň logování
        log_level_mapping = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        
        # Nastavení logování
        logging.basicConfig(
            level=log_level_mapping.get(log_level.upper(), logging.INFO),
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

        # Převést seznam allowed_users na slovník pro rychlejší přístup
        allowed_users_dict = {}
        for user in config.get('allowed_users', []):
            email = user['email']
            allowed_users_dict[email] = user
        config['allowed_users'] = allowed_users_dict
        
        return config

    except yaml.YAMLError as e:
        logging.error(f"Error parsing configuration file: {e}")
        print(f"Error: Unable to parse configuration file {config_file}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Unexpected error loading configuration: {e}")
        print(f"Error: Failed to load configuration from {config_file}")
        sys.exit(1)

def load_tasks(tasks_file='./config/tasks.yaml'):
    # Check if tasks file exists
    if not os.path.exists(tasks_file):
        logging.error(f"Tasks file not found: {tasks_file}")
        logging.error("Performing graceful shutdown due to missing tasks configuration.")
        print(f"Error: Tasks file {tasks_file} does not exist.")
        sys.exit(1)

    try:
        with open(tasks_file, 'r', encoding='utf-8') as file:
            tasks = yaml.safe_load(file)

        # Optional: Validate tasks structure if needed
        if not isinstance(tasks, (dict, list)) or not tasks:
            logging.error(f"Invalid or empty tasks configuration in {tasks_file}")
            print(f"Error: Invalid tasks configuration in {tasks_file}")
            sys.exit(1)

        return tasks

    except yaml.YAMLError as e:
        logging.error(f"YAML parsing error in tasks file: {e}")
        print(f"Error: Unable to parse tasks file {tasks_file}")
        sys.exit(1)
    except PermissionError:
        logging.error(f"Permission denied when trying to read tasks file: {tasks_file}")
        print(f"Error: Permission denied for tasks file {tasks_file}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Unexpected error loading tasks: {e}")
        print(f"Error: Failed to load tasks from {tasks_file}")
        sys.exit(1)

