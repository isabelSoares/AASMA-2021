import os
import csv
import sys
from datetime import datetime

EXPORT_DIR = "./exports"
DELIMITER = "/"

class ExportModule:
    def __init__(self, type_of_agent):
        # Initialize Attributes
        self.timestamp = dateTimeObj = datetime.now()
        self.timestamp_str= dateTimeObj.strftime("%Y-%m-%d@%H-%M-%S")
        self.directory_name = DELIMITER.join([EXPORT_DIR, type_of_agent, self.timestamp_str])

        # Create needed directories
        directory_path = DELIMITER.join([EXPORT_DIR, type_of_agent])
        if not os.path.isdir(directory_path):
            os.makedirs(directory_path)
        # Create needed files
        self.txt_file = open(self.directory_name + '.txt', 'w')
        self.csv_file = open(self.directory_name + '.csv', 'w', newline='')
        self.csv_writer = csv.writer(self.csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

    def write_to_txt(self, string):
        self.txt_file.write(string)
    
    def print_and_write_to_txt(self, string):
        #print(string)
        self.write_to_txt(string + '\n')

    def write_row_to_csv(self, row_values):
        self.csv_writer.writerow(row_values)

    def write_rows_to_csv(self, rows):
        self.csv_writer.writerows(rows)

    def save_current_state(self):
        self.txt_file.close()
        self.txt_file = open(self.directory_name + '.txt', 'a')

        self.csv_file.close()
        self.csv_file = open(self.directory_name + '.csv', 'a', newline='')
        self.csv_writer = csv.writer(self.csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

def create_export_module(type_of_agent):
    global export_module
    export_module = ExportModule(type_of_agent)