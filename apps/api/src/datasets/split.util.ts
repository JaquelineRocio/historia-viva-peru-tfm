/** PRNG determinista (mulberry32) para splits reproducibles. */
function mulberry32(seed: number): () => number {
  let a = seed >>> 0;
  return () => {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function shuffle<T>(arr: T[], rand: () => number): T[] {
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(rand() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

export interface Splittable {
  label: string;
}

export interface GroupSplittable extends Splittable {
  group: string;
  /** Tipo de fuente opcional (pdf, youtube, ...), usado para evaluar dominio. */
  stratum?: string;
}

/** Mantiene cada fuente completa en un único split para evitar fuga de información. */
export function groupedSplit<T extends GroupSplittable>(
  items: T[],
  trainRatio: number,
  valRatio: number,
  seed: number,
): Array<T & { split: 'train' | 'val' | 'test' }> {
  const rand = mulberry32(seed);
  const groups = new Map<string, T[]>();
  for (const item of items) groups.set(item.group, [...(groups.get(item.group) ?? []), item]);
  const groupKeys = [...groups.keys()];
  const n = groupKeys.length;
  const nTrain = Math.max(1, Math.floor(n * trainRatio));
  const nVal = n >= 3 ? Math.max(1, Math.floor(n * valRatio)) : 0;
  const testRatio = Math.max(0, 1 - trainRatio - valRatio);
  const labels = [...new Set(items.map((item) => item.label))];
  const strata = [...new Set(items.map((item) => item.stratum).filter((value): value is string => !!value))];
  const groupsPerStratum = new Map(
    strata.map((stratum) => [
      stratum,
      new Set(items.filter((item) => item.stratum === stratum).map((item) => item.group)).size,
    ]),
  );
  const labelTotals = new Map(labels.map((label) => [label, items.filter((item) => item.label === label).length]));
  const targetRatios = { train: trainRatio, val: valRatio, test: testRatio };

  const score = (keys: string[]) => {
    const counts = new Map<string, number>();
    const totals = { train: 0, val: 0, test: 0 };
    const stratumGroups = new Map<string, Set<string>>();
    keys.forEach((key, index) => {
      const split = index < nTrain ? 'train' : index < nTrain + nVal ? 'val' : 'test';
      for (const item of groups.get(key) ?? []) {
        totals[split]++;
        counts.set(`${split}:${item.label}`, (counts.get(`${split}:${item.label}`) ?? 0) + 1);
        if (item.stratum) {
          const mapKey = `${split}:${item.stratum}`;
          const assigned = stratumGroups.get(mapKey) ?? new Set<string>();
          assigned.add(key);
          stratumGroups.set(mapKey, assigned);
        }
      }
    });
    let value = 0;
    for (const split of ['train', 'val', 'test'] as const) {
      const targetTotal = items.length * targetRatios[split];
      value += Math.abs(totals[split] - targetTotal) / Math.max(1, targetTotal);
      for (const label of labels) {
        const total = labelTotals.get(label) ?? 0;
        const actual = counts.get(`${split}:${label}`) ?? 0;
        const target = total * targetRatios[split];
        value += Math.abs(actual - target) / Math.max(1, target);
        if (n >= 3 && total >= 3 && actual === 0) value += 50;
      }
    }
    // Si existen al menos dos fuentes de un tipo, reserva una para train y
    // otra para test. Con tres o más también exige cobertura en validación.
    for (const stratum of strata) {
      const available = groupsPerStratum.get(stratum) ?? 0;
      if (available >= 2) {
        if (!(stratumGroups.get(`train:${stratum}`)?.size)) value += 100;
        if (!(stratumGroups.get(`test:${stratum}`)?.size)) value += 100;
      }
      if (available >= 3 && nVal > 0 && !(stratumGroups.get(`val:${stratum}`)?.size)) value += 100;
    }
    return value;
  };

  // Con pocas fuentes, un reparto aleatorio puede dejar una clase completa
  // fuera de validación o test. Se exploran asignaciones reproducibles y se
  // conserva la de mejor cobertura y balance por clase.
  let keys = shuffle(groupKeys, rand);
  let bestScore = score(keys);
  const attempts = Math.min(5000, Math.max(200, n * n * 50));
  for (let attempt = 1; attempt < attempts; attempt++) {
    const candidate = shuffle(groupKeys, rand);
    const candidateScore = score(candidate);
    if (candidateScore < bestScore) {
      keys = candidate;
      bestScore = candidateScore;
    }
  }
  const splitByGroup = new Map<string, 'train' | 'val' | 'test'>();
  keys.forEach((key, index) => splitByGroup.set(key, index < nTrain ? 'train' : index < nTrain + nVal ? 'val' : 'test'));
  return items.map((item) => ({ ...item, split: splitByGroup.get(item.group)! }));
}

/**
 * Split estratificado por clase: cada clase se reparte en train/val/test
 * según los ratios, para que la distribución se conserve en cada partición.
 */
export function stratifiedSplit<T extends Splittable>(
  items: T[],
  trainRatio: number,
  valRatio: number,
  seed: number,
): Array<T & { split: 'train' | 'val' | 'test' }> {
  const rand = mulberry32(seed);
  const byLabel = new Map<string, T[]>();
  for (const it of items) {
    const arr = byLabel.get(it.label) ?? [];
    arr.push(it);
    byLabel.set(it.label, arr);
  }

  const out: Array<T & { split: 'train' | 'val' | 'test' }> = [];
  for (const [, arr] of byLabel) {
    const shuffled = shuffle(arr, rand);
    const n = shuffled.length;
    const nTrain = Math.max(1, Math.floor(n * trainRatio));
    const nVal = n >= 3 ? Math.max(1, Math.floor(n * valRatio)) : 0;
    shuffled.forEach((it, i) => {
      const split = i < nTrain ? 'train' : i < nTrain + nVal ? 'val' : 'test';
      out.push({ ...it, split });
    });
  }
  return out;
}
