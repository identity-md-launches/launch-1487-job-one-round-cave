// Media finalization only: isolate model pigment and preserve ancestor pixels.
// Run once with record 29's wall.png and the downloaded prediction at wall-v11.png.
const fs = require('node:fs');
const crypto = require('node:crypto');
const cp = require('node:child_process');
const digest = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const ancestorPath = 'artifacts/line-1/wall.png';
const generatedPath = 'artifacts/line-1/wall-v11.png';
const oldBytes = fs.readFileSync(ancestorPath);
const oldRecord = JSON.parse(fs.readFileSync('dist/line-1/29.json', 'utf8'));
if (digest(oldBytes) !== oldRecord.image.split('/').pop()) throw Error('wrong ancestor');
const generatedBytes = fs.readFileSync(generatedPath);
function ffmpeg(args, input) {
  const result = cp.spawnSync('ffmpeg', ['-v','error', ...args],
    {input, maxBuffer: 16*1024*1024});
  if (result.status !== 0) throw Error('ffmpeg failed: ' + result.stderr.toString());
  return result.stdout;
}
const width = 1254, height = 1254;
const old = ffmpeg(['-i','pipe:0','-f','rawvideo','-pix_fmt','rgb24','pipe:1'], oldBytes);
if (old.length !== width*height*3) throw Error('unexpected cave dimensions');
// Only the basket region from the 1024-square generation is retained.
const insertW = 160, insertH = 192, left = 270, top = 215;
const pigment = ffmpeg(['-i','pipe:0','-vf','crop=280:336:190:170,scale=160:192',
  '-f','rawvideo','-pix_fmt','rgb24','pipe:1'], generatedBytes);
if (pigment.length !== insertW*insertH*3) throw Error('unexpected pigment dimensions');
const wall = Buffer.from(old);
let changed = 0;
for (let y=0; y<insertH; y++) for (let x=0; x<insertW; x++) {
  const p = (y*insertW+x)*3;
  const [r,g,b] = pigment.subarray(p,p+3);
  const dark = r<90 && g<70 && b<55;
  const stone = r<115 && g<100 && b<85 && r<1.35*g;
  if (!(dark || stone)) continue;
  const at = ((top+y)*width+left+x)*3;
  // Translucent earth pigment follows existing rock, rather than replacing it.
  const strength = dark ? 0.70 : 0.48;
  [38,27,17].forEach((tone,c) => {
    wall[at+c] = Math.min(old[at+c], Math.round(old[at+c]*(1-strength)+tone*strength));
  });
  if (!wall.subarray(at,at+3).equals(old.subarray(at,at+3))) changed++;
}
if (changed < 500) throw Error('too little new pigment');
let outside=0;
for (let y=0;y<height;y++) for(let x=0;x<width;x++) {
  const at=(y*width+x)*3;
  if (!wall.subarray(at,at+3).equals(old.subarray(at,at+3)) &&
      !(x>=left && x<left+insertW && y>=top && y<top+insertH)) outside++;
}
if (outside !== 0) throw Error('ancestor pixels changed outside vacant rock');
const png = ffmpeg(['-f','rawvideo','-pix_fmt','rgb24','-s','1254x1254','-i','pipe:0',
  '-frames:v','1','-c:v','png','-pix_fmt','rgb24','-f','image2pipe','pipe:1'],wall);
const jpg = ffmpeg(['-f','rawvideo','-pix_fmt','rgb24','-s','1254x1254','-i','pipe:0',
  '-vf','scale=512:512','-frames:v','1','-c:v','mjpeg','-q:v','5','-f','image2pipe','pipe:1'],wall);
if (jpg.length > 100000) throw Error('thumbnail too large');
fs.writeFileSync(ancestorPath,png);
fs.writeFileSync(generatedPath,png);
fs.writeFileSync('dist/line-1/30.jpg',jpg);
const meaning = 'One charcoal basket holds several stones from the same remembered moment.';
const record = {name:'The Batch Basket',image:'https://api.imd.fun/artifacts/'+digest(png),
  attributes:[['Cave','Base'],['Wall','Line 1'],['Number',30],['Left behind','batch-capture'],
    ['Meaning',meaning],['One thing','portable live Ethereum state snapshots']]
    .map(([trait_type,value])=>({trait_type,value}))};
fs.writeFileSync('dist/line-1/30.json',JSON.stringify(record,null,2)+'\n');
const review = {source_record:29,record_number:30,source_sha256:digest(oldBytes),
  prediction_id:'v0am4yeb8drmr0d16a7v3bqeac',model:'black-forest-labs/flux-kontext-pro',
  generated_sha256:digest(generatedBytes),wall_sha256:digest(png),
  png_dimensions:[width,height],png_format:'8-bit RGB PNG',png_bytes:png.length,
  png_paths:[ancestorPath,generatedPath],jpeg_dimensions:[512,512],jpeg_format:'JPEG',
  jpeg_bytes:jpg.length,addition_rectangle:[left,top,insertW,insertH],
  changed_pixels:changed,changed_pixels_outside_rectangle:outside,
  visual_review:{status:'pending final inspection',new_hands_or_stencils:0,
    unmet_visual_requirements:['Inherited cave background is photographic-looking; preserved to retain the wall.']}};
fs.writeFileSync('line-1/wall-review-30.json',JSON.stringify(review,null,2)+'\n');
console.log(JSON.stringify(review,null,2));
