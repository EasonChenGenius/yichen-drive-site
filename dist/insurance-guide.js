/* Public guidance only. Actual policy limits and rental liability remain unconfirmed. */
function insuranceGuideHTML(){
 const en=state.lang==='en';
 const rows=en?[
 ['Policy cover','Confirm compulsory liability cover and any purchased vehicle damage, third-party and occupant cover. Limits, dates and permitted vehicle use must match the actual policy.'],
 ['Customer responsibility','List any deductible, excess and separately agreed protection service fee before booking. Final liability follows the policy and rental contract.'],
 ['Exclusions and special terms','Commercial policies can exclude drink-driving, an invalid or incompatible licence, deliberate damage and tampering with accident evidence. Check the policy applicable to each claim.'],
 ['Items to check individually','Confirm tyres, wheels, scratches, glass, underbody, water damage and personal belongings separately, including applicable endorsements.'],
 ['After an accident','Protect people and the scene, report to police as required, notify the operator and insurer promptly, and keep photos and documents. Agree assessment and repairs with the insurer before proceeding.'],
 ['Additional costs','Any recovery charges, downtime or loss-of-value claim needs a stated basis and supporting evidence; responsibility is confirmed in the contract and settlement.']
 ]:[
 ['保单保障范围','预订前核对交强险，以及实际投保的车损险、商业第三者责任险和车上人员责任险；保额、有效期及车辆用途按保单确认。'],
 ['免赔额与服务费用','每次事故的免赔额、自负额及保障服务费在报价中单列。客户承担的责任按保单、租赁合同与事故责任确认。'],
 ['免责与特别约定','商业保险可能对酒驾、无有效或准驾不符的驾照、故意制造事故、破坏事故证据等情形免责。交强险赔付及追偿按法定规则处理。'],
 ['需逐项核对的损失','轮胎轮毂、划痕、玻璃、底盘、涉水及个人物品等损失，逐项核对承保险种、附加条款和责任限制。'],
 ['事故处理步骤','先保护人员与现场，按规定报警，及时通知经营者和承保公司，保留照片及单据；维修前与保险公司协商定损和维修安排。'],
 ['额外费用的确认','救援、停运、车辆价值减损等费用，须在合同中说明适用条件、计算依据和凭证，结算时核对责任与实际损失。']
 ];
 return `<section class="detail-block insurance-guide"><h2>${en?'Insurance and accident guidance':'保险与事故处理'}</h2><p class="configuration-note">${en?'General guidance. The actual policy, limits, excess and fees are confirmed before booking.':'通用说明；具体承保情况、保额、免赔额与费用在预订前按实际保单确认。'}</p>${servicePointsHTML(rows)}<details><summary>${en?'Sources and details to confirm':'参考来源与待确认项目'}</summary><p>${en?'Confirm insurer, covered use, policy dates, limits, excess, optional service fees and the accident contact.':'请核对承保公司、适用车辆用途、保险有效期、各险种保额、事故自负额、可选保障服务费及事故联络方式。'}</p><div class="insurance-sources"><a href="https://www.nfra.gov.cn/cn/view/pages/ItemDetail.html?docId=928013&itemId=915" target="_blank" rel="noopener noreferrer">${en?'NFRA: compulsory liability limits':'金融监管总局：交强险责任限额'} ↗</a><a href="https://property.picc.com.cn/chaxunbaoxiantiaokuan/cheliangbaoxian/202009/t20200919_85937.html" target="_blank" rel="noopener noreferrer">${en?'PICC: commercial motor policy terms':'人保财险：商业车险条款'} ↗</a><a href="https://www.1hai.cn/Help/HelpContent?isLimitRules=False&menuId=24" target="_blank" rel="noopener noreferrer">${en?'eHi: rental protection reference':'一嗨：租车保障参考'} ↗</a></div></details></section>`;
}
