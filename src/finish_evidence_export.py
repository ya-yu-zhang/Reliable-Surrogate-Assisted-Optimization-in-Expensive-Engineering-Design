"""One dependency export after application and cost completion; PDF QA stays explicit."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
from time import perf_counter,sleep

from .run_solo_cost import process_inventory

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/evidence_export_v1'


def main():
    OUT.mkdir(parents=True,exist_ok=True);path=OUT/'status.json'
    if path.exists():raise RuntimeError('Export record already exists; refuse duplicate or automatic restart')
    frozen=json.loads((ROOT/'docs/frozen_evidence_export_v1/sha256.json').read_text('utf-8'))
    assert all(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest for name,digest in frozen.items())
    start=perf_counter();stage='waiting_for_complete_application_audit';failure=None
    own_hash=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    def save():
        path.write_text(json.dumps(dict(stage=stage,pid=os.getpid(),pipeline_sha256=own_hash,
            elapsed=perf_counter()-start,failure=failure,visual_quality_verified=False),indent=2),encoding='utf-8')
    def execute(command,log,workdir=ROOT):
        result=subprocess.run(command,cwd=workdir,capture_output=True,text=True,encoding='utf-8',errors='replace')
        (OUT/log).write_text(result.stdout+result.stderr,encoding='utf-8')
        if result.returncode:raise RuntimeError(f'Exit {result.returncode}; preserved {log}')
    try:
        save()
        while True:
            prior=json.loads((ROOT/'results/application_completion_v1/status.json').read_text('utf-8'))
            processes={p['ProcessId'] for p in process_inventory()}
            if prior['stage']=='failed' or prior['failure'] is not None:
                raise RuntimeError('Application prerequisite failed; no final evidence export or scientific rerun')
            if prior['stage']=='complete' and prior['pid'] not in processes:break
            if prior['pid'] not in processes:raise RuntimeError('Application prerequisite ended without complete audit')
            save();sleep(30)
        assert all(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest for name,digest in frozen.items())
        stage='full_evidence_integration';save()
        execute([str(ROOT/'.venv312/Scripts/python.exe'),'-m','src.build_integrated_manuscripts'],'integrated_manuscripts.log')
        stage='compiling_reading_pdfs';save()
        for name,template in [('english_integrated_manuscript','english-paper-template.tex'),('论文综合机制稿','paper-template.tex')]:
            execute(['pandoc',name+'.md','--standalone','--template','../configs/'+template,
                '--lua-filter','../configs/keep-math-mechanism.lua','-o',name+'.tex'],name+'_pandoc.log',ROOT/'paper')
            for pass_number in [1,2]:
                execute(['xelatex','--disable-installer','-interaction=nonstopmode','-halt-on-error',
                    '-output-directory=pdf',name+'.tex'],name+f'_xelatex_{pass_number}.log',ROOT/'paper')
            pdf=ROOT/'paper/pdf'/(name+'.pdf');assert pdf.exists() and pdf.stat().st_size>10000
        stage='compiled_pending_visual_review';save()
        print('Evidence-only integrated manuscripts and PDFs compiled. Every page still requires visual QA; no submission-ready claim.',flush=True)
    except Exception as error:
        stage='failed';failure=dict(error=str(error));save();raise


if __name__=='__main__':main()
