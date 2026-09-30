from . import analyze_application_high_formal as analyzer
from .application_high_journal_audit_safe import audit_high_journal
def main():
    analyzer.audit_journal=audit_high_journal;analyzer.main()
if __name__=="__main__":main()
