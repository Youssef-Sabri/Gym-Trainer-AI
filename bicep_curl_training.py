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
        self.last_shoulder_y = None  # For cheat detection

    def calculate_angle(self, a, b, c):
        """Calculate joint angle between three points in degrees"""
        a, b, c = np.array(a), np.array(b), np.array(c)
        radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
        angle = np.abs(radians * 180.0 / np.pi)
        return angle if angle <= 180 else 360 - angle

    def evaluate_curl(self, keypoints):
        feedback = []
        score = 100

        # Keypoints: COCO format
        shoulder = keypoints[5][:2]
        elbow = keypoints[7][:2]
        wrist = keypoints[9][:2]
        hip = keypoints[11][:2] if len(keypoints) > 11 else None

        # 1. Range of motion
        elbow_angle = self.calculate_angle(shoulder, elbow, wrist)
        if elbow_angle > 160:
            score -= 25
            feedback.append("❌ Incomplete extension at bottom")
        elif elbow_angle < 30:
            score -= 15
            feedback.append("⚠️ Over-rotation at top")

        # 2. Elbow stability (elbow-to-shoulder distance)
        elbow_travel = np.linalg.norm(np.array(elbow) - np.array(shoulder))
        if elbow_travel > 50:  # pixel threshold, calibrate as needed
            score -= 30
            feedback.append("❌ Keep elbows pinned to your sides!")

        # 3. Verticality (no arm swinging)
        verticality = abs(shoulder[0] - wrist[0])
        if verticality > 50:
            score -= 20
            feedback.append("⚠️ Avoid swinging your arm outward")

        # 4. Cheat detection (shoulder movement up = shrugging)
        if self.last_shoulder_y is not None:
            shoulder_delta = abs(shoulder[1] - self.last_shoulder_y)
            if shoulder_delta > 20:  # pixel threshold
                score -= 15
                feedback.append("❌ No shoulder shrugging (keep shoulders down)")
        self.last_shoulder_y = shoulder[1]

        # 5. Rep counting and tempo
        current_time = time.time()
        if elbow_angle < 50 and self.current_state == "down":
            rep_time = current_time - self.rep_start_time
            self.rep_count += 1
            if rep_time < 5.0:
                feedback.append("⚠️ Slow down! Aim for 5s per rep")
            self.current_state = "up"
            self.rep_start_time = current_time
        elif elbow_angle > 130 and self.current_state == "up":
            self.current_state = "down"

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
            # Draw border if form is bad
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