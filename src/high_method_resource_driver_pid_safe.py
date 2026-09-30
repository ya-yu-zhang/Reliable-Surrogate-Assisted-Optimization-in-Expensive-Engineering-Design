"""PID-safe entry for the frozen serial high-dimensional resource driver."""
from . import run_application_high_method_resource as driver
from . import application_high_precheck as gate
from .build_integrated_manuscripts_pid_safe import pid_safe_inventory

def main():
    original_inventory=gate.process_inventory;gate.process_inventory=lambda:pid_safe_inventory(gate.ROOT,original_inventory())
    driver.prerequisite=gate.prerequisite
    original_run=driver.subprocess.run
    def run(command,*args,**kwargs):
        command=list(command)
        if "src.application_high_method_resource" in command:
            command[command.index("src.application_high_method_resource")]="src.high_method_resource_worker_pid_safe"
        return original_run(command,*args,**kwargs)
    driver.subprocess.run=run;driver.main()
if __name__=="__main__":main()
