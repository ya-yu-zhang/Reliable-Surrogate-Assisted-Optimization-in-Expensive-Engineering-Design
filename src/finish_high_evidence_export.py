"""Export audited high-extension manuscripts and PDFs after the science parent exits."""
import hashlib,json,os,subprocess
from pathlib import Path
from time import perf_counter,sleep
from .run_solo_cost import process_inventory

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/high_evidence_export_v1'


def main():
    assert not OUT.exists(),'High evidence export record exists; refuse duplicate restart'
    frozen=json.loads((ROOT/'docs/frozen_high_evidence_export_v1/sha256.json').read_text('utf-8'))
    assert all(hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==v for n,v in frozen.items())
    OUT.mkdir(parents=True);stage='waiting_for_high_extension_audit';failure=None;start=perf_counter()
    def save():
        (OUT/'status.json').write_text(json.dumps(dict(stage=stage,pid=os.getpid(),elapsed=perf_counter()-start,
            failure=failure,visual_quality_verified=False),indent=2),encoding='utf-8')
    def execute(command,log,workdir=ROOT):
        result=subprocess.run(command,cwd=workdir,capture_output=True,text=True,encoding='utf-8',errors='replace')
        (OUT/log).write_text(result.stdout+result.stderr,encoding='utf-8')
        if result.returncode:raise RuntimeError(f'exit {result.returncode}; retained {log}')
    try:
        save()
        while True:
            prior=json.loads((ROOT/'results/high_extension_completion_v1/status.json').read_text('utf-8'))
            alive={p['ProcessId'] for p in process_inventory()}
            if prior['stage']=='failed' or prior['failure'] is not None:raise RuntimeError('High extension prerequisite failed')
            if prior['stage']=='complete' and prior['pid'] not in alive:break
            if prior['pid'] not in alive:raise RuntimeError('High extension parent ended without complete audit')
            save();sleep(30)
        assert all(hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==v for n,v in frozen.items())
        stage='building_high_extension_revision';save()
        execute([str(ROOT/'.venv312/Scripts/python.exe'),'-m','src.build_high_extension_revision'],'build.log')
        stage='compiling_reading_pdfs';save()
        pairs=[('english_high_extension_manuscript','english-paper-template.tex'),('论文高维扩展机制稿','paper-template.tex')]
        for name,template in pairs:
            execute(['pandoc',name+'.md','--standalone','--template','../configs/'+template,
                '--lua-filter','../configs/keep-math-mechanism.lua','-o',name+'.tex'],name+'_pandoc.log',ROOT/'paper')
            for number in [1,2]:execute(['xelatex','--disable-installer','-interaction=nonstopmode','-halt-on-error',
                '-output-directory=pdf',name+'.tex'],name+f'_xelatex_{number}.log',ROOT/'paper')
            pdf=ROOT/'paper/pdf'/(name+'.pdf');assert pdf.exists() and pdf.stat().st_size>10000
        stage='compiled_pending_visual_review';save()
        print('High-extension PDFs compiled; all pages still require visual inspection.',flush=True)
    except Exception as error:
        failure=dict(error_type=type(error).__name__,error=str(error));stage='failed';save();raise


if __name__=='__main__':main()
