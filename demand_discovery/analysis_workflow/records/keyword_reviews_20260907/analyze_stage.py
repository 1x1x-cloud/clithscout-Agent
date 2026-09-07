"""One-off, source-bound evidence annotation. Not a production classifier or a collector."""
import csv
import hashlib
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
SRC = ROOT / 'data_acquisition/apify_reviews/records/keyword_products_apify_20260907'
STATE = ROOT / 'project_governance/project_state/docs/TASK_STATE.md'
CONFIG = ROOT / 'workflow_execution/run_configuration/config/current_round.json'
sys.path.insert(0, str(ROOT))
from demand_discovery.demand_cards.src.prevalence import POLICY, validate_review_evidence

def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))

def write(name, obj):
    (OUT / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def rel(p):
    return p.relative_to(ROOT).as_posix()

def norm(s):
    return re.sub(r'\s+', ' ', s.casefold()).strip()

def stamp(s):
    return datetime.fromisoformat(s.replace('Z', '+00:00'))

# These are explicit analyst decisions on the 36 nonempty window bodies, in the
# immutable source's order. Raw-source SHA and expected counts bind the ordinals.
# tuple: substantive (None = unresolved), interpretation, uncertainties.
DECISIONS = {
 2: (True, '本品前扣解决旧款后扣引起的背部发痒；柔软、承托、36B穿M合身。旧款痛点不归给本品。', '自报身体/尺码仅适用于该评价；不推断其他买家。'),
 3: (True, '明确合身、舒适及聚拢效果的正向体验。', ''),
 4: (True, '柔软、舒适及可搭配多类服装的正向体验。', ''),
 6: (True, '柔软、舒适、合身及场合适用的正向体验。', ''),
 7: (True, '触感、磁扣牢固、小胸合身等正向体验。', '磁扣性质为评价者表述，未核验商品结构。'),
 8: (True, '合身且承托量合适，是承托不足的相反体验。', ''),
 9: (True, '尺码准确、贴合、穿衣不显痕且柔软舒适。', ''),
 11: (True, '合身、舒适、侧背平整及轻微提升的正向体验。', ''),
 13: (True, 'Perfect fit明确评价合身，保留为有维度的短评。', '无尺寸/部位，不据此验证尺码表。'),
 14: (True, '评价者自述术后重建情境，模杯塑形不适合自己；不扩展成医学建议或普遍人群结论。', '末尾The material is grea未写完；仅前半句明确诉求参与分类，不补成great。'),
 15: (True, '对可拆胸垫和滑的表现不满；保留可拆胸垫偏好及滑感未定位两条线索。', 'slippery修饰对象不清，不能断言胸垫移位、面料成分或做工故障。'),
 17: (True, '不舒适且塑形不美观；期待类似其他jelly bra的贴合效果。', '未说明具体尺码偏差，不并入偏小。'),
 20: (True, '自述38DD，买M后准备买L，保留换大码背景。', '没有明确说M太紧；仅推断可能需更大码，不计入明确过紧支持。'),
 21: (True, '柔软、舒适与背部蕾丝的正向体验。', ''),
 22: (True, '舒适、不勒且承托良好；Not binding为正向否定。', ''),
 23: (True, '舒适、合身、外衣不显痕及承托良好。', ''),
 24: (True, '舒适，但没有托起或收住胸部；提升和包容分开记录。', '具体偏差部位/目标尺寸未知。'),
 25: (True, '覆盖差并且很不舒服；未明确说明提升能力。', 'coverage不自动等同罩杯偏小或托举不足。'),
 26: (True, '自述XL扣合困难、过紧压胸、不提升且不舒适；另述湿热出汗情境不适。', '湿热问题机理不清，不能推断透气率或材质；正文XL不外推到其他SKU。'),
 29: (True, '非常舒适、磁扣牢固的正向体验。', ''),
 30: (True, '明确不舒适，虽短但有穿着体验维度。', '不适原因/部位未知。'),
 31: (True, '舒适及自述复购；有实质穿着体验。', '自述复购不作订单核验或新增买家。'),
 32: (False, '只有Love it!，纯赞美，无具体穿着维度。', ''),
 33: (True, '明确舒适、自述又订两件；不把件数当买家数。', ''),
 34: (True, '转述妻子对合身及材质的体验，保留关系语境。', '不是直接穿着者发言，不验证成交或穿着者身份。'),
 35: (True, '舒适且希望更多颜色，具体颜色未指定。', ''),
 36: (True, '与第35条同商品同正文，跨SKU重复；保留原记录但不重复计数。', '11.514秒间隔与正文相同不证明同一买家；只按正文去重。'),
 39: (True, '尺码准确且合身的正向体验。', ''),
 40: (True, '与第39条同商品同正文，跨SKU重复；不重复计数。', '11.922秒间隔不构成买家身份依据。'),
 41: (True, 'Snug描述贴身感，cute为赞美。保留贴合观察，不直接判为过紧。', '5星及snug不能独自确认不适或需大码，痛点方向未确认。'),
 44: (True, '明确合身，另有赞美和自述购买黑色。', '不把复购当新增买家，黑色表述不映射其他SKU。'),
 46: (False, 'Great quality love them jeans仅笼统质量赞美，未说明面料、做工或穿着表现。', '保守排除为无具体依据的赞美；保留原文供复核。'),
 48: (True, '腰位过高、臀部显长且与图片效果不同；同一条体验可标多个问题但不叠加人数。', '没有原广告图与尺寸实测，只能说评价者报告不符。'),
 51: (None, 'Los colored son muy为未完成句，疑指颜色但缺少评价谓语。', '不猜好坏、不补词、不因5星当好评；保留未确认并阻止占比确认。'),
 52: (True, '西语大意为穿着/贴合效果和细节好看；保留合身外观维度的正向体验。', '原句语法松散，不能推断具体尺寸、刺绣质量或成分。'),
 60: (False, '只有Good，纯赞美，无实质内容。', ''),
}

# Each support is an exact source excerpt. Similar symptom phrases can merge;
# different mechanical causes are kept separate. Duplicates stay in raw support.
ISSUES = [
 ('bra_lift', '文胸托举/提升不足', [(24,'doesnt hold my breast up'),(26,'dud not give the lift')], [2,8,11,22,23], 'explicit', '需确认目标提升效果、所购规格及胸部/下围测量；不能从相似款标题判断。'),
 ('bra_containment', '文胸包容/收拢不足', [(24,'doesnt hold my breast up or in')], [], 'explicit', '需说明溢出/收拢位置及期望包容范围；不与覆盖或提升合成一个统计问题。'),
 ('bra_coverage', '文胸覆盖不足', [(25,'Awful coverage')], [], 'explicit', '需明确覆盖部位、所购颜色尺码和目标覆盖。'),
 ('bra_discomfort', '文胸穿着不舒适', [(17,'Uncomfortable'),(25,'very uncomfortable'),(26,'It was uncomfortable because it was too tight'),(30,'Not very comfortable')], [3,4,6,7,9,11,21,22,23,24,29,31,33,35,36], 'explicit', '按共同症状归并；原因不同或未知，不声称同一设计缺陷。'),
 ('bra_tight', '文胸过紧/扣合困难', [(26,'It barely closed with the clasps'),(26,'too tight')], [2,3,6,7,8,9,11,13,22,23,34], 'explicit', '仅1条明确反馈；38DD换L记录只是待确认相关背景，不能凑成2条过紧。'),
 ('bra_molding', '自述术后重建情境下模杯塑形不适', [(14,'the molding would not be ideal for someone else in my situation')], [], 'explicit', '只保留评价者自述情境；适用结构、实测及专业适用性未知，不作医疗建议。'),
 ('bra_shape', '文胸穿着塑形不美观', [(17,'not flattering shape wise')], [3,34], 'explicit', '需目标轮廓和具体不满部位；不与术后结构适用性合并。'),
 ('bra_removable_pads', '对可拆胸垫配置不满', [(15,'Poor quality, slippery, removable breast pads. Junk!')], [], 'explicit', '可拆胸垫被置于负面评价；固定胸垫只是待核对替代方向，未证实移位。'),
 ('bra_slippery', '滑感问题，对象未定位', [(15,'slippery')], [], 'uncertain', '需分清胸垫滑动、面料滑还是整件滑落；不并入面料或胸垫故障。'),
 ('bra_humid', '湿热出汗情境穿着不适', [(26,'not if you’re sweaty in a hot humid climate')], [], 'explicit', '原文确认情境不满，但没有透气/速干测试，不推断材质原因。'),
 ('bra_colors', '希望更多颜色选项', [(35,'I would like to see more.color options if possible'),(36,'I would like to see more.color options if possible')], [], 'explicit', '2条原记录正文相同，仅1份正文支持；期望颜色及当前可选颜色未知。'),
 ('bra_size_up', '买M后计划换L的尺码线索', [(20,'I got the medium but I back ordering the larges.')], [2,9], 'inferred', '可能需要更大码是推断，原文未明确偏小，不作为明确过紧分子。'),
 ('dress_snug', '连衣裙贴身感，是否过紧未确认', [(41,'Snug & cute!')], [39,40,44], 'uncertain', '不能将snug自动归为too tight；没有明确当期负面问题。'),
 ('jeans_high_waist', '牛仔裤腰位过高', [(48,'Pants are very high waisted')], [], 'explicit', '目标前后裆长、腰线及所购尺码待补；不能据此说裤腿过长。'),
 ('jeans_silhouette', '牛仔裤臀部显长、穿着外观与图不符', [(48,'nothing like picture  and make your butt look long')], [52], 'explicit', '属于评价者外观反馈；广告图、臀部/裆长实测缺失，未独立验证图片不符。'),
]

def main():
    if (OUT / 'verification.json').exists():
        raise SystemExit('This completed snapshot is immutable; create a new snapshot for a new analysis.')
    now = datetime.now(timezone.utc).isoformat()
    rows, window_rows, config = read(SRC/'api_reviews.json'), read(SRC/'window_reviews.json'), read(CONFIG)
    assert sha(SRC/'api_reviews.json') == '33bbbc353b402b8bf5cf24026d2f9aa8035d0d0ba41f099e9a9284d1ca92d737'
    begin, end = map(stamp, (config['window']['start'], config['window']['end']))
    selected = [r for r in rows if begin <= stamp(r['timestamp']) < end]
    assert selected == window_rows and len(rows)==366 and len(selected)==63
    assert set(DECISIONS) == {i for i,r in enumerate(selected,1) if r['content'].strip()}
    assert len({r['reviewId'] for r in rows}) == 366
    before = {rel(p): sha(p) for directory in [SRC, ROOT/'workflow_execution/run_history/records', ROOT/'data_acquisition/fastmoss_catalog/records/keyword_product_review_pilot_20260907'] for p in directory.rglob('*') if p.is_file()}
    before[rel(CONFIG)] = sha(CONFIG)
    write('protected_before.json', before)
    (OUT/'TASK_STATE.before.md').write_bytes(STATE.read_bytes())
    source_ref = rel(SRC/'api_reviews.json')
    xref = {x['review_id']: x for x in read(SRC/'previous_sample_crosscheck.json')}
    n_by_id = {r['reviewId']:i for i,r in enumerate(selected,1)}
    groups = defaultdict(list)
    for i,r in enumerate(rows):
        if norm(r['content']): groups[(r['productId'],norm(r['content']))].append(r['reviewId'])
    duplicate_groups = []
    for (pid,body), ids in groups.items():
        if len(ids)>1:
            winids = [rid for rid in ids if rid in n_by_id]
            duplicate_groups.append({'product_id':pid,'normalized_body':body,'review_ids':ids,'window_review_ids':winids,'window_kept_id':winids[0] if winids else None,'rule':'同商品、casefold及空白规范化后的同正文；仅窗口内保留首条，窗口外不抢占窗口内代表；不推断买家相同。'})
    seen = {}
    annotated=[]
    for i,r in enumerate(rows):
        n=n_by_id.get(r['reviewId'])
        body=norm(r['content'])
        substantive, why, unknown = DECISIONS[n] if n in DECISIONS else (False,'空正文，无可解释的穿着体验。','') if n else (None,'原固定窗口外，只做范围隔离和全量同正文核对；本阶段未逐条进行历史语义分类。','不用于补足当期门槛。')
        duplicate=None
        disposition='outside_window' if n is None else 'excluded_empty' if not body else 'unresolved' if substantive is None else 'excluded_non_substantive' if substantive is False else 'text_valid'
        if n and substantive is True:
            key=(r['productId'],body)
            if key in seen:
                duplicate=seen[key]
                disposition='excluded_duplicate_body'
            else: seen[key]=r['reviewId']
        linked=xref.get(r['reviewId'])
        annotated.append({'product_id':r['productId'],'review_id':r['reviewId'],'sku_id':r['skuId'],'timestamp':r['timestamp'],'rating':r['rating'],'original_text':r['content'],'source_ref':f'{source_ref}#/{i}','product_url':r['productUrl'],'scraped_at':r['scrapedAt'],'market_as_reported':r['authorCountry'],'market_basis':'Actor US输入与authorCountry；未独立核实买家所在地。','in_window':n is not None,'window_ordinal':n,'semantic_review_scope':'current_window' if n else 'not_reviewed_outside_window','substantive':substantive,'disposition':disposition,'reason':why,'uncertainty':unknown,'duplicate_of':duplicate,'buyer_id':None,'buyer_identity_verified':False,'thread_id':None,'thread_identity_verified':False,'reused_account_status':'unknown','repost_status':'duplicate_body' if duplicate else 'not_established','author_verified_as_reported':r['authorVerified'],'variant_from_prior_web':None if not linked else {'label':linked['web_variant_label'],'source_ref':rel(SRC/'previous_sample_crosscheck.json'),'basis':linked['match_basis'],'actor_returned_variant':False},'checked_at':now})
    byn={a['window_ordinal']:a for a in annotated if a['in_window']}
    byid={a['review_id']:a for a in annotated}
    signals=[]
    for key,title,support,opposition,strength,missing in ISSUES:
        pid=byn[support[0][0]]['product_id']
        refs=[]
        for n,quote in support:
            a=byn[n]
            assert a['product_id']==pid and quote in a['original_text']
            refs.append({'review_id':a['review_id'],'product_id':pid,'sku_id':a['sku_id'],'timestamp':a['timestamp'],'quote':quote,'source_ref':a['source_ref'],'disposition':a['disposition']})
        ids=list(dict.fromkeys(x['review_id'] for x in refs))
        eligible=[rid for rid in ids if byid[rid]['disposition']=='text_valid']
        opp=[]
        for n in opposition:
            a=byn[n]
            assert a['product_id']==pid
            opp.append({'review_id':a['review_id'],'sku_id':a['sku_id'],'timestamp':a['timestamp'],'quote':a['original_text'],'source_ref':a['source_ref'],'disposition':a['disposition']})
        valid=[a for a in annotated if a['product_id']==pid and a['disposition']=='text_valid']
        count=len(eligible)
        signals.append({'signal_id':key,'product_id':pid,'title':title,'support_strength':strength,'supports':refs,'opposing_or_contextual_evidence':opp,'opposition_limit':'相反体验/合身背景来自同商品但可能不同SKU、身体和情境；不抵消原负面反馈，也不作为故障率证明。','raw_support_record_count':len(ids),'deduplicated_support_text_count':count,'confirmed_problem_support_text_count':count if strength=='explicit' else 0,'independent_buyer_count':None,'text_valid_sample_count':len(valid),'effective_sample_count':None,'problem_ratio':None,'text_only_diagnostic_fraction':{'numerator':count,'denominator':len(valid),'value':count/len(valid) if valid else None,'use':'仅诊断已读正文的结构，非业务有效问题占比；身份/线程、完整性与未知语义尚未全部核实。'},'gates':{'text_sample_at_least_5':len(valid)>=POLICY['min_effective_reviews'],'distinct_problem_texts_at_least_3':strength=='explicit' and count>=POLICY['min_distinct_support_texts'],'independent_buyers':'unknown','problem_ratio':'unknown'},'approved':False,'status':'待补证据','missing':missing})
    products=[]
    for pid,name in [('1732510609891758832','文胸'),('1732357239054307594','连衣裙'),('1731650530027868452','牛仔裤')]:
        a=[x for x in annotated if x['product_id']==pid]
        w=[x for x in a if x['in_window']]
        products.append({'product_id':pid,'name':name,'raw_records':len(a),'window_records':len(w),'window_nonempty':sum(bool(x['original_text'].strip()) for x in w),'dispositions':dict(Counter(x['disposition'] for x in w)),'text_valid_review_ids':[x['review_id'] for x in w if x['disposition']=='text_valid'],'unresolved_review_ids':[x['review_id'] for x in w if x['disposition']=='unresolved'],'effective_sample_count':None,'independent_buyers':None,'complete_business_sample':False,'coverage_basis':'全星级、全SKU请求未过滤，下载数与Actor公开流报告一致且未触发上限；没有额外证据将公开流数量等同完整业务样本。','problem_ratio':None,'demand_cards':0})
    evidence={'schema_version':1,'samples':[],'reviews':[]}
    for p in products:
        evidence['samples'].append({'product_id':p['product_id'],'market':config['market'],'window':config['window'],'rating_scope':'all','complete':False,'review_ids':[a['review_id'] for a in annotated if a['product_id']==p['product_id'] and a['in_window']],'source_ref':f'{rel(OUT/"coverage_and_identity.json")}; {rel(SRC/"download_validation.json")}; {rel(SRC/"actor_input.json")}; {rel(SRC/"run_log.redacted.txt")}','checked_at':now})
    for a in annotated:
        if not a['in_window']: continue
        entry={'product_id':a['product_id'],'review_id':a['review_id'],'buyer_id':None,'buyer_identity_verified':False,'thread_id':None,'suspected_reused_account':False,'is_repost':False,'source_ref':f'{rel(OUT/"review_annotations.json")}#review_id={a["review_id"]}','checked_at':now}
        if a['substantive'] is not None: entry['substantive']=a['substantive']
        evidence['reviews'].append(entry)
    validate_review_evidence(evidence)
    write('review_annotations.json',annotated)
    write('deduplication.json',{'normalization':'casefold + collapse whitespace; per product; exact normalized match','all_corpus_body_groups':duplicate_groups,'duplicate_review_ids':[],'buyer_deduplication':'unknown: no stable ID; names, avatars, timestamps, review IDs and purchase markers are not buyer IDs','thread_deduplication':'unknown: no stable thread IDs','reused_account_screening':'not established; not inferred from style or masked name','window_duplicate_exclusions':[a for a in annotated if a['disposition']=='excluded_duplicate_body']})
    write('exclusions_and_unresolved.json',{'window_exclusions':[a for a in annotated if a['in_window'] and a['disposition'].startswith('excluded_')],'window_unresolved':[a for a in annotated if a['disposition']=='unresolved'],'outside_window':[a for a in annotated if not a['in_window']]})
    write('problem_signals.json',signals)
    write('demand_cards.json',[])
    write('coverage_and_identity.json',{'checked_at':now,'products':products,'request_and_download_evidence':[rel(SRC/x) for x in ['actor_input.json','submitted_input.json','run_log.redacted.txt','dataset_read_provenance.json','download_validation.json','collection_summary.json']],'identity_fields_returned':['authorHandle (masked)','authorName (masked)','authorAvatar','authorVerified'],'stable_buyer_id_returned':False,'stable_thread_id_returned':False,'review_evidence_boolean_semantics':'suspected_reused_account=false/is_repost=false表示未发现有可靠依据的标记，不表示账号真实或转载筛查已证明无异常。unknown留在本档案；complete=false仅表示未确认业务完整性，不断言漏采。'})
    write('review_evidence.json',evidence)
    write('summary.json',{'checked_at':now,'scope':'当前固定窗口语义标注；全366条范围及相同正文核对','window':config['window'],'policy_ref':'project_governance/business_rules/docs/2026-09-06-clothing-demand-agent-v1-design.md#s1','policy_snapshot':POLICY,'products':products,'signals':len(signals),'explicit_problem_groups':sum(s['support_strength']=='explicit' for s in signals),'tentative_groups':sum(s['support_strength']!='explicit' for s in signals),'demand_cards':0,'new_actor_runs':0,'sourcing_queries':0,'network_requests':0,'production_code_changed':False})
    with (OUT/'review_annotations.csv').open('w',encoding='utf-8-sig',newline='') as f:
        fields=['product_id','review_id','sku_id','timestamp','rating','in_window','disposition','substantive','duplicate_of','original_text','reason','uncertainty','source_ref']
        writer=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');writer.writeheader();writer.writerows(annotated)
    # Explicit new source input; never use the default historical sixteen rows.
    cmd=[sys.executable,'-B',str(ROOT/'workflow_execution/launcher/scripts/launch.py'),'--reviews',str(SRC/'api_reviews.json'),'--review-evidence',str(OUT/'review_evidence.json'),'--output-root',str(OUT/'program_baseline')]
    result=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,encoding='utf-8')
    write('baseline_execution.json',{'command':cmd,'returncode':result.returncode,'stdout':result.stdout,'stderr':result.stderr,'network_enabled_by_cli':False})
    assert result.returncode==0, result.stdout+result.stderr
    receipt=json.loads(result.stdout)
    baseline=Path(receipt['output_directory'])
    base_evidence=read(baseline/'evidence.json')
    comparison=[]
    for b in base_evidence:
        if b['review_id'] not in n_by_id: continue
        a=byid[b['review_id']]
        comparison.append({'review_id':a['review_id'],'product_id':a['product_id'],'manual_disposition':a['disposition'],'manual_reason':a['reason'],'baseline_kind':b['kind'],'baseline_flags':b['flags'],'baseline_findings':b['extractions']})
    write('baseline_comparison.json',{'baseline_path':rel(baseline),'scope':'有限规则输出独立保存；布尔有效性接口不覆盖否定/转折分类，本文逐条语义分析不宣称已合入生产程序。','window_rows':comparison})
    build_report(annotated,signals,products,baseline)
    write('verification.json', {'status':'pending'})
    write('verification.json',verify(annotated,signals,products,before,baseline))

def build_report(annotations,signals,products,baseline):
    report=['# 三商品评价：需求证据分析','', '核验日期：2026-09-07（Asia/Shanghai）。使用既有Apify运行NjEXpgqOIip3PeBcU；本阶段全程离线。', '', '**结论：0张合格需求卡，0次找货。** 窗口内63条已逐条标注；窗口外303条仅作范围隔离与同正文核对，不参与当期门槛。', '', '规则继续引用[V1 S1](../../../../project_governance/business_rules/docs/2026-09-06-clothing-demand-agent-v1-design.md)，窗口为2026-08-30T09:05:42Z（含）至2026-09-06T09:05:42Z（不含）。临时FastMoss来源及旧配置保持原值。', '', '## 有效性与去重', '', '| 商品 | 窗口内 | 非空 | 正文层面有效且不同 | 空正文 | 纯赞美 | 重复排除 | 未确认正文 |', '|---|---:|---:|---:|---:|---:|---:|---:|']
    for p in products:
        c=p['dispositions']
        report.append(f'| {p["name"]}（{p["product_id"]}） | {p["window_records"]} | {p["window_nonempty"]} | {c.get("text_valid",0)} | {c.get("excluded_empty",0)} | {c.get("excluded_non_substantive",0)} | {c.get("excluded_duplicate_body",0)} | {c.get("unresolved",0)} |')
    report+=['', '“正文层面有效且不同”尚未完成同买家/同线程和疑似复用账号核验，不能称最终有效评价分母或买家人数。Perfect fit、Not very comfortable、Snug等有明确穿着维度的短评保留；Great quality love them jeans、Love it!、Good只有笼统赞美而排除。西语未完成句Los colored son muy保留未知。', '', '文胸末尾The material is grea未补写；其前半段模杯不适反馈完整，足以确认该条有实质内容。Snug & cute!保留贴身感，未当作过紧。更换大码、滑感对象等不确定性逐条保存。', '', '已发现同商品跨SKU的窗口内同正文重复：文胸7679956738765981453 / 7679956704881739534、连衣裙7681689016258430734 / 7681688957369681678。按API顺序保留前一条，所有SKU与原文仍保留。不能以11秒左右间隔、遮蔽昵称或头像断言同一买家。全366条的5组重复正文另见[去重记录](deduplication.json)。', '', '## 同商品同问题线索', '', '| 商品/问题 | 原记录数 | 去重正文数 | 判定 |', '|---|---:|---:|---|']
    for s in signals:
        report.append(f'| {s["title"]} | {s["raw_support_record_count"]} | {s["deduplicated_support_text_count"]} | {s["support_strength"]}；待补证据 |')
    report+=['', 'explicit为原文明确反馈；uncertain为方向/对象未明确；inferred为分析推断。表内每一行独立计数，同一评价可涉及多个问题，不能相加为买家数或统一问题分子。', '', '文胸最多的是“不舒适”：4份不同正文，占当前25份正文层面有效记录的诊断性比例为4/25=16%。这不是已确认的业务问题占比，更不是已知4位买家；只有这一问题具有至少3份不同正文。托举不足2份，包容不足1份，覆盖不足1份，按不同条件分别保留，不能合并凑门槛。已保存大量舒适、承托良好和合身的反向体验；同一条“舒适但托不住”分别用于舒适反例和承托支持，未混淆极性。', '', '连衣裙有3份不同的实质正文，其中“Snug & cute!”仅为贴身感待解释，没有明确当期负面需求。旧裙长反馈不并入：前次网页样本7679714961710515982的API时间是2026-08-30T06:57:03.419Z，早于窗口开始，不能只按日期2026-08-30判断在窗。', '', '牛仔裤1份明确反馈提到腰位过高及臀部显长、与图片不符，两种观察来自同一条评价。已明确的正文层面有效记录2份，另1份未完成句待确认；即使该未确认句最终有效，已知窗口文本也只有3份，不能达到5份门槛。', '', '## 门槛与资料接口', '', '三个条件必须同时满足：有效样本≥5、同问题不同买家≥3（不同正文≥3仍只是必要条件）、问题占比≥20%。文胸仅正文层面达到5份；独立买家和最终分母均未知。连衣裙最多3份已有效正文，牛仔裤2份明确加1份未知，样本条件未满足。所有线索approved=false，不生成需求卡或找货计划。', '', '请求覆盖全星级、未筛SKU且日志总量与下载一致；这些证明Actor公开流报告数量已取齐。现有档案仍未确认完整业务样本，因此[review_evidence.json](review_evidence.json)三个sample.complete均为false。全部buyer_id/thread_id保持null。suspected_reused_account=false/is_repost=false仅代表无可靠依据的标记，不能理解为已证明账号无复用/无转载。最终有效分母及业务问题占比均为null，未用删去未解释评价来抬高占比。', '', '文胸关键评价7680670162944722701 / SKU1732510617633002224：', '', '> Its comfortable, but definitely doesnt hold my breast up or in.', '', '时间2026-09-01T20:43:08.280Z；Nude, L来自旧网页样本与API唯一对账，非Actor直接规格字段。所有12条历史网页对账只附给各自匹配记录，不向同SKU其他记录传播未经再次核对的规格结论。', '', '## 程序基线与实际验证范围', '', f'已显式用366条新api_reviews.json及本阶段review_evidence.json执行离线CLI；结果保存在[独立基线]({baseline.relative_to(OUT).as_posix()}/REPORT.md)，命令和退出码见[执行记录](baseline_execution.json)。有限规则对否定、转折和新问题词仍可能漏检；[逐条差异](baseline_comparison.json)保存与本次语义标注的区别。生产分类代码未修改，本次分析不代表通用模型已接入流水线。', '', '核验覆盖366条来源字段与原文精确匹配、63条窗口集合、计数互斥完备、每条支持/反向引文、SKU关联、同正文去重、三商品资料接口、零需求卡及零查询、原始数据/旧运行/原配置SHA-256保全、报告链接。结果见[verification.json](verification.json)。这些是资料与程序一致性检查，不是独立人工标注准确率、买家真实性、供货或真实测品效果验证。', '', '## 缺证据与下一步', '', '1. 取得能回溯到评价ID的稳定买家标识，以及线程/追评关系；检查疑似账号复用。沿用Apify路径，不用昵称/头像补造身份，不重新运行这批已完成的Actor。', '2. 补全业务覆盖依据：确认已有公开流对当轮US、全SKU、全星级评价范围的适用性，说明限制；牛仔裤未完成句需取得完整原文或确认源句本就未完成。', '3. 身份补齐也不代表文胸自动达标：当前最多同问题4份/25份不同有效正文仅16%的诊断比例；需重新核算分子分母，仍按原门槛判断。不得滚动窗口或混用其他商品补数。', '4. 条件未齐，继续保留线索；只有合格需求才接原主图→图片找相似款→规格/SKU/供货核验。新采集范围或新Actor预算不继承旧次上限。', '', '## 交付文件', '', '- [全部366条标注JSON](review_annotations.json) / [CSV](review_annotations.csv)：窗口内逐条语义、窗口外隔离及原始引用；CSV长ID需按文本导入。', '- [逐条阅读版](ANNOTATIONS.md)：63条窗口内判断与原文。', '- [同问题线索](problem_signals.json)、[排除及未确认清单](exclusions_and_unresolved.json)、[覆盖与身份依据](coverage_and_identity.json)。', '- [摘要](summary.json)、[门槛结果](demand_cards.json)、[来源保全清单](protected_before.json)、[生成脚本](analyze_stage.py)。', '']
    pos=report.index('## 程序基线与实际验证范围')+2
    report[pos:pos]=['本次有限规则基线输出0条当期问题线索；助手逐条语义分析则保存15组线索（12组明确反馈、3组待解释/推断）。两者都为0张合格需求卡，但原因和识别覆盖不同，不能把基线的0线索当成没有当期问题。生产程序的语义覆盖仍是后续能力缺项。', '']
    (OUT/'REPORT.md').write_text('\n'.join(report),encoding='utf-8')
    appendix=['# 窗口内63条逐条证据','', '先文胸、后连衣裙、牛仔裤；保持原API顺序。标注为本次助手逐条解释，未声称独立人工复核。','']
    for a in annotations:
        if not a['in_window']: continue
        appendix += [f'## {a["window_ordinal"]}. {a["review_id"]}', '', f'商品 {a["product_id"]}；SKU {a["sku_id"]}；{a["timestamp"]}；{a["rating"]}星。', '', f'判定：{a["disposition"]}。{a["reason"]}', '', f'不确定：{a["uncertainty"] or "正文解释无额外待定项；买家/线程身份仍未知。"}', '', '原文：', '', *['> '+line for line in (a['original_text'] or '（空正文）').splitlines()], '']
    (OUT/'ANNOTATIONS.md').write_text('\n'.join(appendix),encoding='utf-8')

def verify(annotations,signals,products,before,baseline):
    checks={}
    original=read(SRC/'api_reviews.json')
    checks['all_366_original_fields_match']=len(annotations)==366 and all(all(a[k]==r[rk] for k,rk in [('product_id','productId'),('review_id','reviewId'),('sku_id','skuId'),('timestamp','timestamp'),('rating','rating'),('original_text','content')]) for a,r in zip(annotations,original))
    checks['window_63_exact_match']=[a['review_id'] for a in annotations if a['in_window']]==[r['reviewId'] for r in read(SRC/'window_reviews.json')]
    checks['expected_counts']= [p['dispositions'] for p in products] == [dict(excluded_empty=9,text_valid=25,excluded_non_substantive=1,excluded_duplicate_body=1),dict(excluded_empty=5,text_valid=3,excluded_duplicate_body=1),dict(excluded_empty=13,excluded_non_substantive=2,text_valid=2,unresolved=1)]
    byid={a['review_id']:a for a in annotations}
    checks['all_support_and_opposition_quotes_exact']=all(x['quote'] in byid[x['review_id']]['original_text'] and byid[x['review_id']]['in_window'] and byid[x['review_id']]['product_id']==s['product_id'] and x['sku_id']==byid[x['review_id']]['sku_id'] and x['timestamp']==byid[x['review_id']]['timestamp'] for s in signals for x in s['supports']+s['opposing_or_contextual_evidence'])
    checks['duplicate_bodies_match']=all(norm(a['original_text'])==norm(byid[a['duplicate_of']]['original_text']) and a['product_id']==byid[a['duplicate_of']]['product_id'] for a in annotations if a['duplicate_of'])
    checks['identities_unknown']=all(a['buyer_id'] is None and a['thread_id'] is None and a['buyer_identity_verified'] is False for a in annotations)
    checks['unknown_business_ratios_no_cards']=all(s['problem_ratio'] is None and not s['approved'] for s in signals) and read(OUT/'demand_cards.json')==[]
    checks['review_evidence_valid']=bool(validate_review_evidence(read(OUT/'review_evidence.json')))
    checks['source_and_history_unchanged']=all((ROOT/path).is_file() and sha(ROOT/path)==h for path,h in before.items())
    checks['baseline_new_source']=read(baseline/'raw_reviews.json')==original
    checks['baseline_no_cards_or_searches']=read(baseline/'demand_cards.json')==[] and read(baseline/'search_plan.json')==[] and not list((baseline/'searches').glob('*.json'))
    links=[]
    for name in ['REPORT.md','ANNOTATIONS.md']:
        for target in re.findall(r'\]\(([^)]+)\)',(OUT/name).read_text(encoding='utf-8')):
            if not target.startswith(('https:','http:')): links.append((OUT/target.split('#')[0]).exists())
    checks['report_links_exist']=all(links)
    with (OUT/'review_annotations.csv').open(encoding='utf-8-sig',newline='') as f:
        csvrows=list(csv.DictReader(f))
    checks['csv_rows_and_long_ids_match']=len(csvrows)==366 and all(c['review_id']==a['review_id'] and c['sku_id']==a['sku_id'] and c['original_text']==a['original_text'] for c,a in zip(csvrows,annotations))
    assert all(checks.values()), checks
    return {'status':'passed','checked_at':datetime.now(timezone.utc).isoformat(),'checks':checks,'protected_files':len(before),'scope':'来源/计数/引用/接口/离线程序/保全；未独立验证语义标注准确率、买家身份、业务覆盖、供货或测品表现。','artifact_sha256':{p.relative_to(OUT).as_posix():sha(p) for p in OUT.rglob('*') if p.is_file() and p.name!='verification.json'}}

if __name__=='__main__':
    main()
