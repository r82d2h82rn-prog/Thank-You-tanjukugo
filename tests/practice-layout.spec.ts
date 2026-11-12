import { test, expect } from '@playwright/test';
const key='thank-you.learning.v1';
for (const size of [{width:402,height:874},{width:375,height:667}]) {
 for(const kind of ['英単語','英熟語'])test(`practice top card and bottom controls fit ${size.width}x${size.height} ${kind}`,async({page})=>{
  await page.setViewportSize(size);
  await page.addInitScript(k=>localStorage.setItem(k,JSON.stringify({version:1,progress:{},favorites:[],settings:{sound:false,speech:false},permanentAwards:[],lastSection:{catalog:'sample',level:1,kind:'word',section:1}})),key);
  await page.goto('/');
  await expect(page.getByText(/制作済み|検討済み|校閲前|草稿|試用中/)).toHaveCount(0);
  await page.getByRole('button',{name:'LEVEL 1 高校入試',exact:true}).click();
  await page.getByRole('button',{name:`SECTION 01 · ${kind}`,exact:true}).click();
  await page.getByRole('button',{name:'選択式練習を始める',exact:true}).click();
  await page.getByRole('button',{name:'この設定で練習を開始',exact:true}).click();
  const card=page.getByTestId('practice-card'),footer=page.getByTestId('practice-footer');
  await expect(page.getByRole('button',{name:'わからない',exact:true})).toBeInViewport({ratio:1});
  await expect(footer.getByRole('button',{name:'← 戻る',exact:true})).toBeInViewport({ratio:1});
  await expect(page.getByText('学習中',{exact:true})).toHaveCount(0);
  const header=await page.getByTestId('app-header').boundingBox(),question=await card.boundingBox(),bottom=await footer.boundingBox();
  expect(question!.y-header!.y-header!.height).toBeLessThanOrEqual(16);
  expect(question!.y+question!.height).toBeLessThanOrEqual(bottom!.y+1);
  expect(await page.getByTestId('study-scroll').evaluate(el=>el.scrollTop)).toBe(0);
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  await page.screenshot({path:`test-results/practice-${size.width}-${kind==='英単語'?'word':'idiom'}.png`});
  await page.getByRole('button',{name:'わからない',exact:true}).click();
  await expect(page.getByText('？ わからない',{exact:true})).toBeInViewport();
  await expect(footer).toBeInViewport({ratio:1});
  await footer.getByRole('button',{name:'← 戻る',exact:true}).click();
  await expect(page.getByRole('button',{name:'選択式練習を始める',exact:true})).toBeVisible();
  await expect.poll(async()=>page.evaluate(k=>Object.values(JSON.parse(localStorage.getItem(k)!).progress).reduce((n:number,p:any)=>n+(p.choice?.history?.length??0),0),key)).toBe(1);
 });
}
