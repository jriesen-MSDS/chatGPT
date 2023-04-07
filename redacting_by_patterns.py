import pandas as pd
import re

# Load the data file to update
data_file = pd.read_excel('path_to_data_file.xlsx')

# Define the regular expression to match words to hide

#For app_named_to_hide - Create an xlsx file, and call colum 1A, apps, place specific words you want deleted from the file
# Load the list of app names to hide
app_names_file = pd.read_excel('path_to_app_names_file.xlsx')
app_names_to_hide = set(app_names_file['apps'])
#or if several
#app_names_to_hide = ['app1', 'app2', 'app3']  # Replace with your list of app names
app_names_pattern = r'\b(?:{})\b'.format('|'.join(app_names_to_hide))
all_cap_pattern = r'\b[A-Z]{2,3}\d?\b'
network_path_pattern = r'\\\\[^\\\n]+\b'
url_pattern = r'\b(?:https?://|www\.)\S+\b'
pattern = r'{}|{}|{}|{}'.format(all_cap_pattern, network_path_pattern, url_pattern, app_names_pattern)

# Create a new DataFrame to hold the updated values
updated_data_file = pd.DataFrame()

# Iterate over each column in the data file and apply the regular expression to each cell
for column in data_file.columns:
    if data_file[column].dtype == 'object':  # Check if column contains strings
        updated_column = data_file[column].str.replace('_', ' ').str.replace('-', ' ').apply(lambda x: re.sub(pattern, '***', str(x)))
    else:
        updated_column = data_file[column]
    updated_data_file[column] = updated_column

# Save the updated data to a new xlsx file
updated_data_file.to_excel('path_to_updated_data_file.xlsx', index=False)
