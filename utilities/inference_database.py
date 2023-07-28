import os
import pandas as pd
from utilities.interaction_event import InteractionEvent


class Inference_Database:
    """
    CSV based data-store for saving shopper interactions data. 
    Structure of CSV file is described as dictionary `CSV_Structure` class attribute. 
    
    Attributes
    ----------
    df : pandas.DataFrame
        Pandas Dataframe to hold the data in memory.
    dst_path : str
        Destination directory to store the csv file.
    csv_filename : str
        Filename of the csv file. 

    Basic Usage
    -----------
    Construct a Inference_Database instance.

    >>> db = Inference_Database('/path/to/dir', 'shoppers.csv')

    Adding an event.

    >>> db.add_shopper_interaction_event(interaction_event)

    Persisting/Saving the records to a csv file

    >>> db.save_into_csv()

    """

    # Structure/Columns of the CSV file
    CSV_STRUCTURE = {
        'stream': 'Stream_No',
        'start': 'Checkpoint_Start',
        'end': 'Checkpoint_End',
        'name': 'Video_Name',
        'total': 'Total Persons Detected',
        'stl': 'Stopped to look',
        'persons_i': 'Persons who stood longer',
        'blocks_i': 'Interacted Blocks Count',
        'mt_10': 'More than 10 seconds',
        'mt_20': 'More than 20 seconds',
        'mt_30': 'More than 30 seconds',
        'mt_40': 'More than 40 seconds',
        'mt_50': 'More than 50 seconds',
        'mt_60': 'More than 1 minute',
        'overall_total': 'Total Persons till now (Accumulative)'
    }

    def __init__(self, dst_path, csv_filename="shoppers.csv"):
        """
        Constructor for the Inference_Database Class

        Parameters:
        ----------
        dst_path : str
            Destination directory to store the csv file.
        csv_filename : str
            Filename of the csv file. 
        """
        
        # Constructing a pandas DataFrame using `CSV_STRUCTURE` dictionary values as columns
        self.df = pd.DataFrame(columns=Inference_Database.CSV_STRUCTURE.values())

        self.dst_path = dst_path
        self.csv_filename = csv_filename

    def __str__(self):
        """String representation of the data"""

        return self.df

    def add_shopper_interaction_event(self, event: InteractionEvent):
        """
        Adds the InteractionEvent data to the database.

        Parameters
        ----------
        event : InteractionEvent
            Interaction event to add to the database.

        Returns
        -------
        None
        """

        # Constructing a dictionary from the event object
        row = {
                'Stream_No': event.camera_id,
                'Checkpoint_Start': event.start_time,
                'Checkpoint_End': event.end_time,
                'Region': "|".join(event.region),
                'Video_Name': os.path.basename(event.video_path),
                'Total Persons Detected': event.total_detected,
                'Stopped to look': event.total_confirmed,
                'Persons who stood longer': event.total_confirmed,
                'Interacted Blocks Count': event.interactions_count,
                'More than 10 seconds': event.count_dict['mt_10'],
                'More than 20 seconds': event.count_dict['mt_20'],
                'More than 30 seconds': event.count_dict['mt_30'],
                'More than 40 seconds': event.count_dict['mt_40'],
                'More than 50 seconds': event.count_dict['mt_50'],
                'More than 1 minute': event.count_dict['mt_60'],
                'Total Persons till now (Accumulative)': event.total_detected
            }
            
        self.df = self.df.append(row,ignore_index=True)

    def save_into_csv(self):
        """
        Saves the data into a csv file. Target directory is created if does not exist.

        Returns
        -------
        None
        """

        if not os.path.exists(self.dst_path):
            os.makedirs(self.dst_path)

        self.df.to_csv(os.path.join(self.dst_path, self.csv_filename),index=False)
