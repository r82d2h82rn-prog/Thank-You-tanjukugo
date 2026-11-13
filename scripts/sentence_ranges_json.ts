import {readFileSync} from 'node:fs';
import {sentenceRanges} from '../src/readingSentences';
const input=JSON.parse(readFileSync(0,'utf8')) as {paragraphId:string;text:string}[];
process.stdout.write(JSON.stringify(input.map(x=>sentenceRanges(x.paragraphId,x.text))));
