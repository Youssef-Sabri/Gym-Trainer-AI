import os
import torch
import logging
from mmpose.apis import MMPoseInferencer
from bicep_curl_training import BicepCurl

class AITrainer:
    def __init__(self):
        """Initialize AI Trainer with pose estimation model and exercise trainers."""
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger('AITrainer')
        
        # Model configuration
        self.config_file = 'models/config.py'
        self.checkpoint_file = 'models/RTMpose.pth'
        self._verify_model_files()
        
        # Initialize inferencer with proper device handling
        self.inferencer = self._initialize_inferencer()
        
        # Initialize exercise trainers
        self.bicep_curl_trainer = BicepCurl(self.inferencer)
        self.logger.info("AI Trainer initialized successfully")

    def _verify_model_files(self):
        """Verify that required model files exist."""
        if not os.path.exists(self.config_file):
            error_msg = f"Config file not found at {self.config_file}"
            self.logger.error(error_msg)
            raise FileNotFoundError(error_msg)
            
        if not os.path.exists(self.checkpoint_file):
            error_msg = f"Model weights not found at {self.checkpoint_file}"
            self.logger.error(error_msg)
            raise FileNotFoundError(error_msg)

    def _initialize_inferencer(self):
        """Initialize MMPose inferencer with proper device handling."""
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.logger.info(f"Initializing inferencer on {device.upper()}")
        
        try:
            return MMPoseInferencer(
                pose2d=self.config_file,
                pose2d_weights=self.checkpoint_file,
                device=device
            )
        except Exception as e:
            self.logger.error(f"Failed to initialize inferencer: {str(e)}")
            raise RuntimeError("Failed to initialize pose estimation model") from e

    def analyze_frame(self, frame):
        """
        Analyze frame using the appropriate trainer.
        
        Args:
            frame: Input image frame
            
        Returns:
            Analysis results from the current trainer
        """
        try:
            return self.bicep_curl_trainer.analyze_frame(frame)
        except Exception as e:
            self.logger.error(f"Frame analysis failed: {str(e)}")
            raise RuntimeError("Frame analysis failed") from e

    def release_resources(self):
        """Clean up resources safely."""
        self.logger.info("Releasing resources...")
        try:
            if hasattr(self, 'inferencer') and self.inferencer is not None:
                self.inferencer.__del__()
        except Exception as e:
            self.logger.warning(f"Error during resource release: {str(e)}")
        finally:
            self.logger.info("Resources released")

    def __del__(self):
        """Destructor to ensure resources are released."""
        self.release_resources()