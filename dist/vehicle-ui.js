const VEHICLE_PHOTO_CREDITS={
 '718':{author:'Vauxford',url:'https://commons.wikimedia.org/wiki/File:2018_Porsche_Cayman_718_Boxster_2.0_Front.jpg',license:'CC BY-SA 4.0',licenseUrl:'https://creativecommons.org/licenses/by-sa/4.0/'},
 e:{author:'Tokumeigakarinoaoshima',url:'https://commons.wikimedia.org/wiki/File:The_frontview_of_Mercedes-Benz_E_200_Edition_Exclusive_(W214).jpg',license:'CC0 1.0',licenseUrl:'https://creativecommons.org/publicdomain/zero/1.0/'}
};
Object.assign(VEHICLE_PHOTO_CREDITS,VEHICLE_PHOTO_SOURCES);
function vehiclePhotoNotice(car){return car.photoNote?`<span class="vehicle-reference-badge">${esc(state.lang==='en'?car.photoNoteEn:car.photoNote)}</span>`:''}
function vehicleImageFrame(car,attributes=''){return `<div class="vehicle-image-wrap">${vehiclePhoto(car,attributes)}${vehiclePhotoNotice(car)}</div>`}
function vehiclePhotoCredit(c){const credit=VEHICLE_PHOTO_CREDITS[c.id];return credit?`<p class="showroom-credit">Photo: <a href="${credit.url}" target="_blank" rel="noopener noreferrer">${credit.author}</a> · <a href="${credit.licenseUrl}" target="_blank" rel="noopener noreferrer">${credit.license}</a></p>`:''}
function vehicleCopy(zh,en){return state.lang==='en'?en:zh}
function vehicleReferenceShowroom(c){return `<section class="showroom" aria-label="${vehicleCopy('车型图片','Vehicle photos')}"><div class="showroom-bar"><div><span class="eyebrow">YICHEN · VEHICLE PHOTOS</span><span class="showroom-model">${c.name}</span></div></div><div class="showroom-stage"><div class="showroom-photo">${vehiclePhoto(c,'alt="'+esc(c.name)+'"')}${vehiclePhotoNotice(c)}</div></div><p class="showroom-note">${vehicleCopy('图片为车型风格参考，年款、版本与配置以实车核验资料为准。','Images are model-style references. Confirm the actual year, trim and equipment.')}</p>${vehiclePhotoCredit(c)}</section>`}

function vehicleShowroom(c){return vehicleReferenceShowroom(c)}
