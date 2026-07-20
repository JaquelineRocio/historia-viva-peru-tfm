import { FileBlob, PresentationFile } from "@oai/artifact-tool";

const source = process.argv[2];
const textOnly = process.argv.includes("--text-only");
const presentation = await PresentationFile.importPptx(await FileBlob.load(source));
const slides = Array.from(presentation.slides.items ?? presentation.slides ?? []);

if (textOnly) {
  for (const [index, slide] of slides.entries()) {
    console.log(`SLIDE ${index + 1}`);
    for (const shape of slide.shapes?.items ?? []) {
      const value = String(shape.text ?? "").trim();
      if (value) console.log(`${shape.id}\t${value.replace(/\s+/g, " ")}`);
    }
  }
  process.exit(0);
}

const protoKeys = (value) => {
  const keys = new Set();
  let current = value;
  while (current && current !== Object.prototype) {
    for (const key of Object.getOwnPropertyNames(current)) keys.add(key);
    current = Object.getPrototypeOf(current);
  }
  return [...keys].sort();
};

console.log(JSON.stringify({
  presentationKeys: Object.keys(presentation),
  slideCount: slides.length,
  slides: slides.map((slide, index) => ({
    index: index + 1,
    shapeCount: slide.shapes?.items?.length,
    shapes: (slide.shapes?.items ?? []).map((shape) => ({
      id: shape.id,
      name: shape.name,
      type: shape.type,
      frame: shape.frame,
      textType: typeof shape.text,
      text: typeof shape.text === "string" ? shape.text : String(shape.text ?? ""),
      paragraphs: (() => {
        try {
          return (shape.getParagraphs?.() ?? []).map((p) => String(p.text ?? p));
        } catch { return []; }
      })(),
    })).filter((shape) => shape.text || shape.paragraphs.length),
  })),
}, null, 2));
