import os
from typing import List
from torchreid.utils import FeatureExtractor
from torchreid import metrics

import yaml
import numpy as np
import torch
# from Entities.Person import Person
from utils.image_encodings_operations import ImageEncodings
from statistics import mode


class CustomerReID:
    def __init__(self, model_name = 'osnet_x1_0', 
                model_path = '../osnet_x1_0_market_256x128_amsgrad_ep150_stp60_lr0.0015_b64_fb10_softmax_labelsmooth_flip.pth'):

        self.model_name = model_name
        self.model_path = model_path
        self.config = yaml.safe_load(open('config.yaml', "r"))
        self.encodings_operations = ImageEncodings()

    def extract_person_embeddings(self, person_crops, model):
        return model(person_crops).detach().cpu().numpy()

    def register_person(self, new_encodings, counter):

        encodings = self.encodings_operations.load_encodings()

        if counter not in encodings.keys():
            encodings[counter] = new_encodings
        else:
            encodings[counter].extends(new_encodings)

        self.encodings_operations.save_encodings(encodings)
        return int(counter)

    def delete_person(self, person_id):
        """delets the records for the track id from the image_encodings file

        Args:
            person_id (int): id of the target person in image_encodings file
        """
        encodings, labels = self.encodings_operations.load_encodings()
        encodings = np.array(encodings)
        labels = np.array(labels)
        print("deleting")
        idx = np.where(labels == person_id)
        labels = np.delete(labels, idx)
        encodings = np.delete(encodings, idx, axis = 0)

        self.encodings_operations.save_encodings(encodings = encodings, labels = labels)

    # TODO --> add a checker for calculate exit time of an id
    def get_topk_results(self, k : int, known_labels, list_of_cosine_dist):
        """
        Return top-k (k belongs to integer value) of smallest
        cosine distance values for each tensor of distance
        in a list of tensors.

        Args:
            k (int) : number of smallest values
            list_of_cosine_dist (torch.tensor): tensor contains cosine distance for all
                                                detections with registered images.
        """

        cosine_dist, indices = torch.topk(list_of_cosine_dist, k , dim = 1, largest = False)
        indices = *(i for i in indices),
        out_indices = torch.cat(indices, dim = 0).detach().numpy()

        preds = mode(known_labels[out_indices])[0]  # taking first mode if two or more common values are found.
        return preds
    
    def load_extractor_model(self):
        extractor = FeatureExtractor(
            model_name = self.model_name,
            model_path = self.model_path,
            device = 'mps',
        )
        return extractor


    def re_identify(self, target_features, type = 'smallest'):
        try:
            known_encodings, known_labels = self.encodings_operations.load_encodings()
            known_encodings = torch.from_numpy(known_encodings)
            target_features = torch.from_numpy(target_features)

            ans = (metrics.compute_distance_matrix(target_features, known_encodings, metric = "cosine"))
            if type == 'average':
                avg_distances = torch.mean(ans, dim = 1)
                shortest_distance_position = torch.argmin(avg_distances).item()
                pred = known_labels[shortest_distance_position]
            elif type == 'smallest':
                distances, indices = torch.min(ans, dim = 1)
                indices = indices.detach().numpy()
                pred = mode(known_labels[indices])[0]
            else:
                pred = self.get_topk_results(3, known_labels, ans)
            return int(pred)

        except Exception as e:
            print(e)
            import traceback
            traceback.print_tb(e.__traceback__)
            return None


