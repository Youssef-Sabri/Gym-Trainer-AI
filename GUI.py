import cv2
import threading
import tkinter as tk
from tkinter import messagebox, ttk
from trainer import AITrainer
from datetime import datetime

class ModernButton(ttk.Button):
    """Custom button class with hover effects"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bind('<Enter>', self.on_enter)
        self.bind('<Leave>', self.on_leave)

    def on_enter(self, e):
        self['style'] = f'{self["style"]}.Hover'

    def on_leave(self, e):
        self['style'] = self['style'].replace('.Hover', '')

class GymTrainerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gym Trainer AI")
        self.root.geometry("1024x768")
        self.root.configure(bg='#2C3E50')
        
        # Initialize AITrainer
        self.trainer = AITrainer()
        self.running = False
        self.capture_thread = None
        self.session_start = None

        # Setup theme and styles
        self.setup_styles()
        
        # Create main container
        self.container = ttk.Frame(root, style='Main.TFrame', padding="20")
        self.container.pack(fill=tk.BOTH, expand=True)

        # Create UI elements
        self.create_header()
        self.create_main_content()
        self.create_status_bar()
        self.setup_text_tags()

    def setup_styles(self):
        style = ttk.Style()
        style.configure('Main.TFrame', background='#2C3E50')
        style.configure('Content.TFrame', background='#34495E')
        style.configure('Header.TLabel',
                       font=('Helvetica', 28, 'bold'),
                       foreground='#ECF0F1',
                       background='#2C3E50')
        style.configure('Status.TLabel',
                       font=('Helvetica', 10),
                       foreground='#ECF0F1',
                       background='#2C3E50')
        style.configure('Start.TButton',
                       font=('Helvetica', 12),
                       padding=10)
        style.configure('Start.TButton.Hover',
                       font=('Helvetica', 12, 'bold'),
                       padding=10)
        style.configure('Stop.TButton',
                       font=('Helvetica', 12),
                       padding=10)
        style.configure('Stop.TButton.Hover',
                       font=('Helvetica', 12, 'bold'),
                       padding=10)

    def create_header(self):
        header_frame = ttk.Frame(self.container, style='Main.TFrame')
        header_frame.pack(fill=tk.X, pady=(0, 20))
        title_label = ttk.Label(
            header_frame,
            text="Gym Trainer AI",
            style='Header.TLabel'
        )
        title_label.pack(pady=(0, 10))
        subtitle = ttk.Label(
            header_frame,
            text="Advanced Exercise Analysis System",
            style='Status.TLabel'
        )
        subtitle.pack()

    def create_main_content(self):
        content = ttk.Frame(self.container, style='Content.TFrame')
        content.pack(fill=tk.BOTH, expand=True, pady=(0, 20))

        # Left panel - Controls
        control_panel = ttk.LabelFrame(
            content,
            text="Controls",
            style='Content.TFrame',
            padding="20"
        )
        control_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        self.start_button = ModernButton(
            control_panel,
            text="▶ Start Analysis",
            command=self.start_analysis,
            style="Start.TButton",
            width=20
        )
        self.start_button.pack(pady=(0, 10))

        self.stop_button = ModernButton(
            control_panel,
            text="■ Stop Analysis",
            command=self.stop_analysis,
            style="Stop.TButton",
            width=20,
            state=tk.DISABLED
        )
        self.stop_button.pack()

        # Right panel - Feedback
        feedback_panel = ttk.LabelFrame(
            content,
            text="Exercise Feedback",
            style='Content.TFrame',
            padding="20"
        )
        feedback_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.feedback_text = tk.Text(
            feedback_panel,
            height=15,
            width=50,
            font=("Helvetica", 11),
            bg='#ECF0F1',
            fg='#2C3E50',
            relief=tk.FLAT,
            state=tk.DISABLED
        )
        self.feedback_text.pack(fill=tk.BOTH, expand=True)

    def setup_text_tags(self):
        self.feedback_text.tag_configure("rep_count", 
                                       font=("Helvetica", 14, "bold"),
                                       foreground="#2980b9")
        self.feedback_text.tag_configure("good_score", 
                                       font=("Helvetica", 12, "bold"),
                                       foreground="#27ae60")
        self.feedback_text.tag_configure("bad_score", 
                                       font=("Helvetica", 12, "bold"),
                                       foreground="#c0392b")
        self.feedback_text.tag_configure("separator", 
                                       font=("Helvetica", 11),
                                       foreground="#7f8c8d")
        self.feedback_text.tag_configure("error", 
                                       foreground="#c0392b")
        self.feedback_text.tag_configure("warning", 
                                       foreground="#f39c12")

    def create_status_bar(self):
        self.status_var = tk.StringVar(value="Ready")
        self.status_bar = ttk.Label(
            self.root,
            textvariable=self.status_var,
            style='Status.TLabel',
            padding=(10, 5)
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def start_analysis(self):
        if self.running:
            return

        self.running = True
        self.session_start = datetime.now()
        self.start_button.configure(state=tk.DISABLED)
        self.stop_button.configure(state=tk.NORMAL)
        self.status_var.set("Analysis running...")
        
        self.capture_thread = threading.Thread(target=self.analyze, daemon=True)
        self.capture_thread.start()

    def stop_analysis(self):
        if not self.running:
            return
            
        self.running = False
        self.session_start = None
        self.start_button.configure(state=tk.NORMAL)
        self.stop_button.configure(state=tk.DISABLED)
        self.status_var.set("Analysis stopped")
        
        if self.capture_thread and self.capture_thread.is_alive():
            self.capture_thread.join(timeout=1.0)

    def analyze(self):
        try:
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                self.status_var.set("Error: Could not open camera")
                messagebox.showerror("Error", "Could not open video source.")
                self.stop_analysis()
                return

            while self.running:
                ret, frame = cap.read()
                if not ret:
                    break

                vis_frame, feedback_data = self.trainer.analyze_frame(frame)
                self.root.after(0, self.update_feedback, feedback_data)

                cv2.imshow('Exercise Analysis', vis_frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

        except Exception as e:
            self.root.after(0, self.show_error, str(e))
        finally:
            cap.release()
            cv2.destroyAllWindows()
            self.root.after(0, self.stop_analysis)

    def update_feedback(self, feedback_data):
        self.feedback_text.config(state=tk.NORMAL)
        self.feedback_text.delete(1.0, tk.END)
        
        # Session duration
        if self.session_start:
            duration = datetime.now() - self.session_start
            self.feedback_text.insert(tk.END, 
                f"Session Duration: {duration.seconds//60}m {duration.seconds%60}s\n\n",
                "separator")
        
        # Metrics
        metrics = feedback_data['metrics']
        self.feedback_text.insert(tk.END, f"Rep Count: {metrics['reps']}\n", "rep_count")
        score_tag = "good_score" if metrics['form_score'] > 70 else "bad_score"
        self.feedback_text.insert(tk.END, f"Form Score: {metrics['form_score']}%\n\n", score_tag)
        
        # Feedback messages
        if feedback_data['messages']:
            self.feedback_text.insert(tk.END, "Form Feedback:\n", "separator")
            for msg in feedback_data['messages']:
                tag = "error" if "❌" in msg else "warning" if "⚠️" in msg else None
                self.feedback_text.insert(tk.END, f"{msg}\n", tag)
        
        self.feedback_text.config(state=tk.DISABLED)

    def show_error(self, error_message):
        messagebox.showerror("Error", f"An error occurred: {error_message}")
        self.status_var.set("Error occurred")

    def on_closing(self):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.stop_analysis()
            try:
                self.trainer.release_resources()
            except:
                pass
            self.root.destroy()

if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = GymTrainerApp(root)
        root.protocol("WM_DELETE_WINDOW", app.on_closing)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("Fatal Error", f"Application failed to start: {str(e)}")