"""Wait for old in-flight units, switch to the documented 8/2 scheduler, then audit."""
import hashlib,json,os,shutil,subprocess,time
from pathlib import Path
from time import perf_counter
from .run_solo_cost import process_inventory
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/budget_performance_sensitivity_completion_v2'
ARCH=ROOT/'results/budget_concurrency_switch_20260923_v1'
def save(stage,start,**extra):
 (OUT/'status.json').write_text(json.dumps({'stage':stage,'pid':os.getpid(),'elapsed':perf_counter()-start,'failure':None,**extra},indent=2),encoding='utf-8')
def call(module,log):
 r=subprocess.run([str(ROOT/'.venv312/Scripts/python.exe'),'-m',module],cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace')
 (OUT/log).write_text(r.stdout+r.stderr,encoding='utf-8');assert r.returncode==0,(module,r.returncode)
def main():
 assert not OUT.exists() and not ARCH.exists();OUT.mkdir();start=perf_counter();save('waiting_for_four_old_inflight_units',start)
 while any('-m src.budget_sensitivity_worker' in (p['CommandLine'] or '') for p in process_inventory()):time.sleep(10)
 source=ROOT/'results/budget_performance_sensitivity_v1';(ARCH/'partial_runs').mkdir(parents=True)
 partial=[]
 for d in source.glob('budget_*D/*/*'):
  if d.is_dir() and not (d/'summary.json').exists():
   partial.append(d.relative_to(source).as_posix());target=ARCH/'partial_runs'/d.relative_to(source);target.parent.mkdir(parents=True,exist_ok=True);shutil.move(str(d),str(target))
 old=ROOT/'results/budget_performance_sensitivity_completion_v1'
 if old.exists():shutil.move(str(old),str(ARCH/'old_completion_state'))
 record={'schema':'budget_concurrency_switch_v1','partial_runs_archived':partial,'completed_before_switch':sum(1 for _ in source.glob('budget_*D/*/*/summary.json')),
         'old_worker_processes_remaining':0,'new_total_workers':8,'new_gp_workers':2,'scientific_design_changed':False,'timing_comparability':'mixed_concurrency_not_for_speed_claims'}
 (ARCH/'switch.json').write_text(json.dumps(record,indent=2),encoding='utf-8');save('formal_2700_runs_8x2',start,**record)
 call('src.run_budget_performance_sensitivity_8x2','runs.log');save('full_raw_audit',start,**record)
 call('src.analyze_budget_performance_sensitivity','audit.log');save('complete',start,runs=2700,**record)
if __name__=='__main__':main()
