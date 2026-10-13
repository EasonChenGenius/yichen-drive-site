/* ============================================================================
   车辆真实资料表 —— 全站车辆数据的唯一填写位置
   ----------------------------------------------------------------------------
   改这里就会改到：首页报价、搜索筛选（座位/行李/驱动/变速箱/CarPlay）、
   YICHEN Match 推荐、车辆详情页配置表、预订费用明细。

   填写规则：
   1. 只有经营者确实核实过的项目才填。没核实的留 null，页面显示"待确认"，
      不要为了好看猜一个数字 —— 座位数和价格写错会直接变成对客户的承诺。
   2. price = 对外日租价（人民币/天）。未定价留 null，页面显示"待报价"。
   3. seats = 行驶证核定座位数（不是"最多能挤几个人"）。
   4. bags = 满载座位时后备厢能放的 24 寸行李箱件数，按实车实测填写。
   5. 填完一台就把该车的 confirmed 改成 true，页面会显示"已核对"。
   6. 建议顺序：year / trim → seats / bags → price / deposit → 其余。
   ============================================================================ */

const VEHICLE_FACTS = {
  /* ---- 敞篷跑车 ---- */
  '718': {
    confirmed: false,
    price: 1280,          // 当前为演示价，未确认为对外报价
    year: null,           // 例：2018
    trim: null,           // 例：Boxster S
    seats: null,          // 行驶证核定座位
    bags: null,
    drive: null,          // 例：后驱
    energy: null,         // 例：汽油
    transmission: null,   // 例：7 速双离合
    carplay: null,        // true / false
    deposit: null,        // 租车押金（元）
    note: null
  },
  /* ---- 豪华 SUV ---- */
  'x5': { confirmed: false, price: 1080, year: null, trim: null, seats: null, bags: null, drive: null, energy: null, transmission: null, carplay: null, deposit: null, note: null },
  /* ---- 新能源 SUV ---- */
  'my': { confirmed: false, price: 680, year: null, trim: null, seats: null, bags: null, drive: null, energy: null, transmission: null, carplay: null, deposit: null, note: null },
  /* ---- 豪华轿车 ---- */
  'e': { confirmed: false, price: 880, year: null, trim: null, seats: null, bags: null, drive: null, energy: null, transmission: null, carplay: null, deposit: null, note: null },
  /* ---- 商务 MPV ---- */
  'gl8': { confirmed: false, price: 680, year: null, trim: null, seats: null, bags: null, drive: null, energy: null, transmission: null, carplay: null, deposit: null, note: null },
  'gl8-653': { confirmed: false, price: null, year: null, trim: null, seats: null, bags: null, drive: null, energy: null, transmission: null, carplay: null, deposit: null, note: null },
  /* ---- 新能源 MPV ---- */
  'denza-d9': { confirmed: false, price: null, year: null, trim: null, seats: null, bags: null, drive: null, energy: null, transmission: null, carplay: null, deposit: null, note: null },
  /* ---- 商务轿车 ---- */
  'magotan': { confirmed: false, price: 420, year: null, trim: null, seats: null, bags: null, drive: null, energy: null, transmission: null, carplay: null, deposit: null, note: null },
  'passat': { confirmed: false, price: 480, year: 2014, trim: null, seats: null, bags: null, drive: null, energy: null, transmission: null, carplay: null, deposit: null, note: null },
  'h7': { confirmed: false, price: 680, year: null, trim: null, seats: null, bags: null, drive: null, energy: null, transmission: null, carplay: null, deposit: null, note: null },
  /* ---- 经济轿车 ---- */
  'jetta': { confirmed: false, price: 260, year: null, trim: null, seats: null, bags: null, drive: null, energy: null, transmission: null, carplay: null, deposit: null, note: null },
  /* ---- 商务中巴 ---- */
  'coaster': { confirmed: false, price: 1500, year: null, trim: null, seats: null, bags: null, drive: null, energy: null, transmission: null, carplay: null, deposit: null, note: null }
};

/* ----------------------------------------------------------------------------
   合同与计费规则 —— 全站租车条款的唯一填写位置
   填 null 的项不会在页面上编造数字，只显示"需线下确认"。
   ---------------------------------------------------------------------------- */
const RENTAL_TERMS = {
  confirmed: false,
  currency: 'CNY',
  minRentalDays: null,        // 最短租期（天）
  minDriverAge: null,         // 驾驶员最小年龄
  minLicenceYears: null,      // 驾照最短持证年限
  deposit: null,              // 统一押金（元）；单车押金写在 VEHICLE_FACTS 里优先
  freeKmPerDay: null,         // 每日免费里程（公里）
  excessKmPrice: null,        // 超公里单价（元/公里）
  overtimeHourPrice: null,    // 超时单价（元/小时）
  cancelFreeHours: null,      // 出发前多少小时可免费取消
  cancelFee: null,            // 逾期取消费用（元或比例文字）
  fuelPolicy: null,           // 油电政策，例："满油取还，差额按加油站票据结算"
  tollParkingPolicy: null,    // 路桥停车费由谁承担
  driverMealAccommodation: null, // 带司机时的餐宿标准（元/天）
  crossBorderAllowed: null,   // 是否允许出省/出境行驶（true/false）
  insuranceExcess: null,      // 事故自负额（元）
  contractUrl: null,          // 合同模板链接（PDF）
  note: null
};
