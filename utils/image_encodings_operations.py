import numpy as np
import os
import torch
import pickle
from glob import glob
import yaml

class ImageEncodings:

    def __init__(self) -> None:
        self.config = yaml.safe_load('config.yaml', "r")
        self.image_encodings_path = self.config['image_encodings']

    def save_encodings(self, encodings):

        f = open(self.image_encodings_path, "wb")
        pickle.dump(encodings, f)
        f.close()

    def load_encodings(self):
        with open(self.image_encodings_path, 'rb') as file:
            encodings = pickle.load(file)
        return encodings


# def manage_exited_ids_file(filename = EXITED_IDS, id = None, new = False):
#     def load(filename = EXITED_IDS):
#         with open(filename, 'rb') as f:
#             out = pickle.load(f)
#         return out

#     def update(ids, filename = EXITED_IDS):
#         ids = {
#             'exited_ids' : ids,
#         }

#         f = open(filename, "wb")
#         pickle.dump(ids, f)
#         f.close()

#     if new:
#         update(ids = [])

#     else:
#         old_ids = load()['exited_ids']

#         if id is not None:
#             old_ids.append(id)
#         update(ids = old_ids)

