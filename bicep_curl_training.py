import numpy as np
import cv2
import time

class BicepCurl:
    def __init__(self, inferencer):
        self.inferencer = inferencer
        self.rep_count = 0
        self.current_state = "down"
        self.rep_start_time = time.time()
        self.last_angle = 0
        self.form_score = 100
        self.last_shoulder_y = None
        self.bad_rep_streak = 0
        self.rep_phase_time = time.time()

    def calculate_angle(self, a, b, c):
        """Calculate joint angle between three points in degrees"""
        a, b, c = np.array(a), np.array(b), np.array(c)
        radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
        angle = np.abs(radians * 180.0 / np.pi)
        return angle if angle <= 180 else 360 - angle

    def evaluate_curl(self, keypoints):
        feedback = []
        score = 100
        valid_rep = True

        # Keypoints: COCO format
        shoulder = keypoints[5][:2]
        elbow = keypoints[7][:2]
        wrist = keypoints[9][:2]

        # 1. Form Evaluation Rules
        elbow_travel = np.linalg.norm(np.array(elbow) - np.array(shoulder))
        if elbow_travel > 80:
            score -= 15
            feedback.append("⚠️ Keep your upper arm steady")
            valid_rep = False

        # Check shoulder stability
        if self.last_shoulder_y is not None:
            shoulder_delta = abs(shoulder[1] - self.last_shoulder_y)
            if shoulder_delta > 30:
                score -= 10
                feedback.append("⚠️ Keep shoulders level")
                valid_rep = False
        self.last_shoulder_y = shoulder[1]

        # Check arm swing
        lateral_movement = abs(shoulder[0] - elbow[0])
        if lateral_movement > 70:
            score -= 10
            feedback.append("⚠️ Keep movement vertical")
            valid_rep = False

        # 2. Range of Motion Rules
        elbow_angle = self.calculate_angle(shoulder, elbow, wrist)
        
        if elbow_angle > 170:
            score -= 5
            feedback.append("⚠️ Don't lock your elbow")
            valid_rep = False
        elif elbow_angle < 160 and self.current_state == "down":
            score -= 10
            feedback.append("⚠️ Lower the weight fully")
            valid_rep = False

        # Top position check
        if self.current_state == "up" and elbow_angle > 20:
            score -= 10
            feedback.append("⚠️ Curl higher")
            valid_rep = False

        # 3. Tempo and Rep Counting
        current_time = time.time()
        rep_time = current_time - self.rep_start_time
        
        # State transitions
        if self.current_state == "down" and elbow_angle < 60:
            if rep_time < 1.0:
                score -= 5
                feedback.append("⚠️ Control the lift")
            self.current_state = "up"
            self.rep_start_time = current_time
            self.rep_phase_time = current_time
            
        elif self.current_state == "up" and elbow_angle > 130:
            phase_time = current_time - self.rep_phase_time
            if phase_time < 1.5:
                score -= 5
                feedback.append("⚠️ Control the descent")
            
            # Count the rep
            self.rep_count += 1
            if score >= 90:
                feedback.append("✨ Perfect form!")
            elif score >= 80:
                feedback.append("👍 Good rep!")
            
            self.current_state = "down"
            self.rep_start_time = current_time

        return {
            'metrics': {
                'reps': self.rep_count,
                'form_score': max(0, score),
                'elbow_angle': elbow_angle
            },
            'messages': feedback
        }

    def analyze_frame(self, frame):
        results = next(self.inferencer(frame, return_vis=True))
        vis_frame = results['visualization'][0]
        feedback_data = {'metrics': {'reps': 0, 'form_score': 0}, 'messages': []}

        if len(results['predictions']) > 0:
            keypoints = results['predictions'][0][0]['keypoints']
            feedback_data = self.evaluate_curl(keypoints)

            # Visual feedback
            color = (0, 255, 0) if feedback_data['metrics']['form_score'] > 70 else (0, 0, 255)
            cv2.putText(vis_frame, f"Reps: {feedback_data['metrics']['reps']}", 
                       (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
            cv2.putText(vis_frame, f"Form: {feedback_data['metrics']['form_score']}%",
                       (20, 90), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

            if feedback_data['metrics']['form_score'] < 70:
                cv2.rectangle(vis_frame, (0, 0), (vis_frame.shape[1], vis_frame.shape[0]), (0, 0, 255), 8)

        return vis_frame, feedback_data

    def reset_data(self):
        """Reset all exercise tracking data"""
        self.rep_count = 0
        self.current_state = "down"
        self.rep_start_time = time.time()
        self.last_angle = 0
        self.form_score = 100
        self.last_shoulder_y = None
        self.bad_rep_streak = 0
        self.rep_phase_time = time.time()