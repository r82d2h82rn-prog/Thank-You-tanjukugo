#!/usr/bin/env python3
"""Attach CMU-derived IPA to independently written rows. Unknown readings require an override."""
import csv,pathlib,sys
import eng_to_ipa as ipa
source=pathlib.Path(sys.argv[1]);destination=pathlib.Path(sys.argv[2])
rows=[line.split('|') for line in source.read_text().splitlines() if line.strip()]
assert len(rows)==100,len(rows)
assert all(len(row) in (6,7) for row in rows)
readings=ipa.convert(' '.join(row[0] for row in rows)).split()
assert len(readings)==len(rows)
unknown=[row[0] for row,reading in zip(rows,readings) if '*' in reading and len(row)!=7]
if unknown:raise ValueError('発音を個別確認して指定してください: '+', '.join(unknown))
with destination.open('x') as stream:
 writer=csv.writer(stream,delimiter='\t',lineterminator='\n')
 writer.writerow(['english','pos','pronunciation','meaning','example','translation','explanation','pronunciation_source'])
 for row,reading in zip(rows,readings):
  manual=len(row)==7
  pronunciation=row[6] if manual else '/'+reading+'/'
  writer.writerow([row[0],row[1],pronunciation,*row[2:6],'original' if manual else 'cmudict'])
print('Prepared 100 independently authored entries; IPA requires editorial review.')
