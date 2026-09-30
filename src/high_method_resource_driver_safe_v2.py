"""Resume the frozen resource driver with PID and 4096+8 audit adapters."""
from . import run_application_high_method_resource as driver
from . import application_high_precheck as gate
from .application_high_journal_audit_safe import audit_high_journal
from .build_integrated_manuscripts_pid_safe import pid_safe_inventory

def main():
    original_inventory=gate.process_inventory;gate.process_inventory=lambda:pid_safe_inventory(gate.ROOT,original_inventory())
    driver.prerequisite=gate.prerequisite;driver.audit_journal=audit_high_journal
    original_run=driver.subprocess.run
    def run(command,*args,**kwargs):
        command=list(command)
        if "src.application_high_method_resource" in command:
            command[command.index("src.application_high_method_resource")]="src.high_method_resource_worker_pid_safe"
        return original_run(command,*args,**kwargs)
    driver.subprocess.run=run;driver.main()
if __name__=="__main__":main()
