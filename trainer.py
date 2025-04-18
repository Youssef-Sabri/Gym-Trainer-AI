import os
import torch
from mmpose.apis import MMPoseInferencer
from bicep_curl_training import BicepCurl

class AITrainer:
    def __init__(self):
        # Model setup shared across trainers
        self.config_file = 'models/config.py'
        self.checkpoint_file = 'models/RTMpose.pth'

        if not os.path.exists(self.config_file):
            raise FileNotFoundError(f"Config file not found at {self.config_file}")
        if not os.path.exists(self.checkpoint_file):
            raise FileNotFoundError(f"Model weights not found at {self.checkpoint_file}")

        self.inferencer = MMPoseInferencer(
            pose2d=self.config_file,
            pose2d_weights=self.checkpoint_file,
            device='cuda' if torch.cuda.is_available() else 'cpu'
        )

        # Initialize trainers with shared model
        self.bicep_curl_trainer = BicepCurl(self.inferencer)

    def analyze_frame(self, frame):
        """Delegate frame analysis to the specific trainer"""
        return self.bicep_curl_trainer.analyze_frame(frame)

    def release_resources(self):
        """Release resources for all trainers"""
        self.inferencer.__del__()