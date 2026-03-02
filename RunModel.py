import subprocess

class RunModel():
    """
    """
    def __init__(self,model_cfg):
        """
        """
        self.target_directory = model_cfg['target_directory']
        self.executable_name = model_cfg['executable_name'] 
        self.namelist_file=model_cfg['namelist_file']

    def run(self):
        """
        run the model
        """
        try:
            # Use check=True to automatically raise an error if the command fails
            # On Windows, this might be ['cmd', '/c', 'echo', 'Hello World']
            result = subprocess.run(
                [self.executable_name,self.namelist_file],
                cwd=self.target_directory,
                capture_output=True,
                text=True,
                check=True
            )    
            print("Command successful!")
            print("Output:", result.stdout.strip())

        except FileNotFoundError:
            print("Error: Command not found. Make sure the executable is in your system's PATH.")
        except subprocess.CalledProcessError as e:
            print(f"Error: Command failed with return code {e.returncode}")
            print("Error Output (stderr):", e.stderr)        
       
