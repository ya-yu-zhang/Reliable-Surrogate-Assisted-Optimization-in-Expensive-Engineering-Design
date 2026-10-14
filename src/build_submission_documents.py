"""Render supporting preparation documents without signing or submitting them."""
from pathlib import Path
from html import escape
import json,re
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle
from .prepare_submission_20261014 import TITLE

COVER=[
('14 October 2026','small'),
('Editors, Engineering Optimization','h2'),
('Re: '+TITLE,'h1'),
('Dear Editors,','body'),
('We have prepared the above research article for consideration in Engineering Optimization. It addresses a computational question that arises when a surrogate-management decision depends on a response that has not yet been observed: which next actions can still be minimal over the declared response domain?','body'),
('For a fixed-kernel Gaussian process, enclosed binary-system coefficients yield affine posterior-mean bands. Our exact rational envelope returns the complete relaxed-band action set, closed feasible intervals and at most two rival indices for each excluded action. It retains isolated ties and separates the construction algorithm from an independent exclusion checker. Classical affine-envelope geometry is acknowledged; the claimed increment is the executable coefficient-band contract and its measured computational improvement, rather than a new acquisition policy or a new convex-geometric principle.','body'),
('On all 114 archived engineering branches and both response domains, the operator preserves the frozen action sets and includes every stored next action. All 232,564 new exclusions pass rational replay. Against the frozen same-contract pairwise reference, construction is 3.19-fold faster, or 2.62-fold when separate proof replay is included. These timings describe a computational stage, not full deployment savings. The study also retains the unfavorable engineering outcome: tighter action information still yields no new H1 category or baseline selection certificate.','body'),
('The proposed fit is a numerical method for surrogate-assisted engineering optimization, evaluated within one deterministic beam family. The review archive supplies the current GP inputs, certificates and verification code. Three supporting paired-grid recovery files are currently unavailable; the manuscript preserves their historical analysis outputs and explicitly limits complete raw-record reproducibility for that check. Known AI assistance includes formal argument drafting and manuscript preparation, and is disclosed without asserting venue-policy compliance.','body'),
('This is an unsigned preparation copy. Affiliations for Zhenyu Meng and Jia Zhao remain to be supplied by instruction. Originality, exclusive submission and other required factual declarations must be completed by the submitting author in the journal workflow; they have not been invented here.','note'),
('Corresponding author listed in the manuscript:<br/>Shu-Chuan Chu<br/>School of Computer Science, Nanjing University of Information Science and Technology<br/>Nanjing 210044, Jiangsu, China<br/>100130@nuist.edu.cn','small')
]

NOTE=[
('Editorial evidence note','h1'),
('Current verified contribution and preservation limits | 14 October 2026','small'),
('Current computational contribution','h2'),
('The exact coefficient-band envelope produces closed response-domain outer action sets and constant-size rival-index witnesses. The 43 nontrivial construction contexts contain 114 branches. Across two declared domains, all 228 action sets equal the frozen pairwise sets, and all 232,564 new exclusions pass independent rational checks. The original archive, matrices, bands, original certificates and recorded computational comparison are supplied for scoped review.','body'),
('Interpretation of the measured improvement','h2'),
('Summed casewise median construction times are 19.257762912 s and 6.040864692 s (3.187915-fold). Separate complete proof-replay passes are 3.578688102 s and 2.668741318 s; including those single passes gives 2.621984-fold. Common coefficient construction and physical work are outside these numbers. No independent sampling, optimized-library superiority or full deployment saving is claimed. H1 downstream certification remains unsuccessful.','body'),
('Supporting paired-grid evidence gap','h2'),
('Twenty-two of 25 historical raw files have been recovered with matching hashes. The completed recovery events.jsonl, responses.json and run_status.json are missing, totaling 908,908 bytes. Historical analysis.json, paired_contrasts.csv and case_summary.csv match the former full package hashes. Those outputs support inspection of the reported tables but cannot replace raw response, residual, density or cache-provenance replay. The historical failed coarse-source gate and all 521 paid attempts remain recorded.','body'),
('Access and remaining submission facts','h2'),
('The source GitHub repository is private, so its URL is not reviewer access. Data_and_Code_for_Review_20261014.zip is the scoped attachment to be supplied through an accepted journal route. It excludes the full historical 13.6 GB archive and the missing paired-grid files. Author affiliations b/c remain pending. Known AI assistance is disclosed; Taylor & Francis policy compliance is not certified. No manuscript has been submitted and no manuscript ID exists.','body')
]

def render(path,sections,rows=None):
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle('body2',fontName='Times-Roman',fontSize=10.5,leading=13.4,spaceAfter=8,textColor=colors.HexColor('#17202b')))
    styles.add(ParagraphStyle('head1',fontName='Helvetica-Bold',fontSize=15,leading=18,spaceAfter=13,textColor=colors.HexColor('#163451')))
    styles.add(ParagraphStyle('head2',fontName='Helvetica-Bold',fontSize=10.5,leading=13,spaceBefore=6,spaceAfter=6,textColor=colors.HexColor('#163451')))
    styles.add(ParagraphStyle('small2',fontName='Helvetica',fontSize=9,leading=12,spaceAfter=9,textColor=colors.HexColor('#445260')))
    styles.add(ParagraphStyle('note2',fontName='Helvetica',fontSize=8.7,leading=11.5,spaceAfter=10,textColor=colors.HexColor('#74530a')))
    mapped={'body':'body2','h1':'head1','h2':'head2','small':'small2','note':'note2'}
    story=[]
    for text,kind in sections:
      story.append(Paragraph(text,styles[mapped[kind]]))
    if rows:
      data=[[Paragraph(escape(str(c)),styles['small2']) for c in row] for row in rows]
      table=Table(data,colWidths=[118,380],hAlign='LEFT')
      table.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('BOTTOMPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),7),('LINEBELOW',(0,0),(-1,-1),.35,colors.HexColor('#cdd5dd')),('BACKGROUND',(0,0),(0,-1),colors.HexColor('#f1f4f7'))]))
      story.append(table)
    def footer(c,doc):
      c.setStrokeColor(colors.HexColor('#cdd5dd'));c.line(48,39,A4[0]-48,39)
      c.setFont('Helvetica',8);c.setFillColor(colors.HexColor('#627181'))
      c.drawString(48,27,'Preparation copy | No portal submission performed')
      c.drawRightString(A4[0]-48,27,str(doc.page))
    path.parent.mkdir(parents=True,exist_ok=True)
    SimpleDocTemplate(str(path),pagesize=A4,rightMargin=48,leftMargin=48,topMargin=43,bottomMargin=51,title=sections[0][0],author='Manuscript preparation',invariant=1).build(story,onFirstPage=footer,onLaterPages=footer)

def main(root):
    output=root/'output/pdf/submission_20261014';output.mkdir(parents=True,exist_ok=True)
    render(output/'Cover_letter_preparation_20261014.pdf',COVER)
    render(output/'Editorial_evidence_note_20261014.pdf',NOTE)
    title_sections=[(TITLE,'h1'),('Author information | 14 October 2026','small'),('Author order and affiliations','h2')]
    rows=[('1. Shu-Chuan Chu','Corresponding author. School of Computer Science, Nanjing University of Information Science and Technology, Nanjing 210044, Jiangsu, China. Email: 100130@nuist.edu.cn.'),
      ('2. Ya-Yu Zhang','School of Computer Science, Nanjing University of Information Science and Technology, Nanjing 210044, Jiangsu, China.'),
      ('3. Zhenyu Meng','Affiliation b: to be supplied. Intentionally pending by user instruction.'),
      ('4. Jia Zhao','Affiliation c: to be supplied. Intentionally pending by user instruction.'),
      ('Remaining factual fields','Author ORCIDs and additional emails were not supplied. Enter them if requested by the portal. Funding, conflicts, contribution assignments, originality and exclusive submission must reflect actual author facts.'),
      ('Article identity','Research article; confirm the exact portal category. Keywords: expensive engineering optimization; Gaussian processes; numerical certificates; affine envelopes; decision auditing.')]
    render(output/'Author_information_20261014.pdf',title_sections,rows)
    notes=root/'submission_20261014';notes.mkdir(exist_ok=True)
    (notes/'COVER_LETTER.txt').write_text('\n\n'.join(re.sub('<[^>]+>',' ',text) for text,_ in COVER)+'\n')
    print(json.dumps({'documents':[p.name for p in output.glob('*.pdf')],'submission_performed':False}))

if __name__=='__main__':
    main(Path(__file__).resolve().parents[1])
