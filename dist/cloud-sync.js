/* ============================================================================
   云服务接入 —— 租车咨询的云端持久备份
   ----------------------------------------------------------------------------
   为什么需要：WorkBuddy 托管环境的项目目录只读，咨询落在 /tmp，重启即丢。
   这份代码在提交成功后把同一条咨询写进云数据库，数据不再随容器回收而消失。

   安全设计：inquiries 表开了 RLS，只授予 INSERT，没有任何 SELECT 策略。
   也就是说浏览器端只能写、读不回来 —— 客户的手机号、微信号不会从前端泄露。
   数据只能由经营者通过管理端读取。

   容错：SDK 没加载、网络失败、写入被拒，都只记录状态，绝不影响原有提交流程。
   ============================================================================ */

/* publicConfig 由云服务开通后下发，四个字段都是可公开的前端配置 */
const CLOUD_PUBLIC_CONFIG = {
  endpoint: 'https://yichen-drive.app.workbuddy.host',
  oauthRelayBaseUrl: 'https://www.workbuddy.cn/v2/as/genie-baas/oauth',
  publishableKey: 'wbpk_zfQOMDHL31IfhqEiCsWPcI_QnmCX6MwM4PtGysjUktqebFHfQczBlZO'
};

let cloudClientCache = null;

function cloudClient() {
  if (cloudClientCache) return cloudClientCache;
  if (typeof window === 'undefined' || !window.WorkBuddyCloud) return null;
  try {
    cloudClientCache = window.WorkBuddyCloud.createWorkBuddyCloud({
      endpoint: CLOUD_PUBLIC_CONFIG.endpoint,
      oauthRelayBaseUrl: CLOUD_PUBLIC_CONFIG.oauthRelayBaseUrl,
      publishableKey: CLOUD_PUBLIC_CONFIG.publishableKey
    });
  } catch (e) {
    cloudClientCache = null;
  }
  return cloudClientCache;
}

/* 把咨询写入云数据库。返回 {ok, reason, message}，永不抛出。 */
async function cloudSaveInquiry(payload) {
  const cloud = cloudClient();
  if (!cloud) return { ok: false, reason: 'sdk-missing', message: '云服务 SDK 未加载' };
  try {
    const row = {
      request_id: payload.requestId || null,
      service: payload.service || null,
      car: payload.car || null,
      city: payload.city || null,
      people: Number.isFinite(Number(payload.people)) ? Number(payload.people) : null,
      bags: Number.isFinite(Number(payload.bags)) ? Number(payload.bags) : null,
      duration_days: Number.isFinite(Number(payload.durationDays)) ? Number(payload.durationDays) : null,
      start_at: payload.startDate ? String(payload.startDate) + 'T' + (payload.startTime || '') : null,
      end_at: payload.endDate ? String(payload.endDate) + 'T' + (payload.endTime || '') : null,
      nickname: payload.name || null,
      phone: payload.phone || null,
      wechat: payload.wechat || null,
      payload: payload || null
    };
    const { error } = await cloud.database.from('inquiries').insert(row);
    if (error) return { ok: false, reason: error.code || 'db-error', message: error.message };
    return { ok: true };
  } catch (e) {
    return { ok: false, reason: 'network', message: String((e && e.message) || e) };
  }
}

/* 记录最近一次云同步结果，便于排查；不参与业务逻辑 */
function cloudSyncStatus(result) {
  try {
    window.__cloudSync = result;
    if (result && !result.ok) console.warn('[cloud] 咨询未同步到云端：', result.reason);
  } catch (e) { /* 无痕忽略 */ }
}
