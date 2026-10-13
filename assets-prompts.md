# 车辆视觉资源

## 成功生成的图片

迈腾（灰色）、Model Y（白色）、X5（深灰）、帕萨特（黑色）、捷达（白色）、考斯特（棕色）为 AI 车型示意图，不是车队实拍。

通用最终提示词：

> Use case: product mockup. Photorealistic premium rental catalog studio photograph. Entire car front three-quarter view facing LEFT, complete bumpers roof and wheels visible, generous margins, landscape 3:2. Camera at headlight height, normal lens. Seamless warm ivory studio, diffuse soft light, subtle floor shadow. No people, no text, no watermark, no scenery. Correct vehicle category and specified paint color. Illustrative automotive render.

车型描述：

- Volkswagen Magotan grey four-door sedan.
- Tesla Model Y white crossover SUV.
- BMW X5 dark charcoal SUV.
- Volkswagen Passat black sedan, long elegant four-door saloon with broad horizontal grille.
- Volkswagen Jetta white compact four-door sedan, classic Jetta shape and understated horizontal grille.
- Toyota Coaster brown minibus, tall long rectangular bus body, many rectangular passenger windows, passenger entry door, wide front windshield, commercial bus proportions.

棕色 GL8、奔驰 E 级和 718 图片生成多次返回网络连接错误，使用下列可再利用的车型照片补齐。三维 GLB 模型全部为项目原创模型，与这些照片版权独立。

## 照片来源与授权

- 棕色别克 GL8：User3204，[2023 Buick GL8 Land Business Edition](https://commons.wikimedia.org/wiki/File:2023_Buick_GL8_Land_Business_Edition_(third_facelift,_front).jpg)，[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)。原文件未修改。
- 黑色奔驰 E 级：Tokumeigakarinoaoshima，[Mercedes-Benz E 200 W214](https://commons.wikimedia.org/wiki/File:The_frontview_of_Mercedes-Benz_E_200_Edition_Exclusive_(W214).jpg)，[CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/)。原文件未修改。
- 保时捷 718 Boxster：Vauxford，[2018 Porsche 718 Boxster](https://commons.wikimedia.org/wiki/File:2018_Porsche_Cayman_718_Boxster_2.0_Front.jpg)，[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)。原文件未修改。

以上照片仅展示车型，并不代表租赁交付车辆。图像通过 CSS 等比例展示；无裁切或车身改色。各照片按上述许可分发，作者与许可亦在车型详情中标注。

## 2026-10-06 修正

原深棕考斯特 AI 图不再用于网页。网页采用用户上传的原始浅香槟棕参考图 `dist/coaster-reference-v2.png`，未经重绘或改色。该照片只作为外观参考，不证明任何实车配置。红旗 H7 尚未有实车参考图，页面明确显示等待实车照片。

## 2026-10-07 车型对应修正

原 GL8 图片是陆上公务舱，与用户指定陆尊不匹配，已从网页停用；文件及原许可记录保留用于追溯。考斯特结构原型不用于网页，单张外观照片不代表完整精确车身或内饰。

## 本次统一视觉更新

考斯特按用户照片生成浅香槟棕棚拍示意，帕萨特按2014中国车型目标生成黑色棚拍示意。内置imagegen成功输出原PNG保留在 `visual-assets/vehicles/`，网页JPEG在 `dist/images/vehicles/`。这是AI车型风格参考，不证明实车配置或精确几何。718/奔驰编辑与景点生成遇到网络错误，未更换成未完成图。十一张目的地改用已核对许可的实景照片，原图、作者与来源记录在 `visual-assets/destination-photo-sources.json`；网页仅压缩、裁切展示与统一色调，不声称AI重绘。
