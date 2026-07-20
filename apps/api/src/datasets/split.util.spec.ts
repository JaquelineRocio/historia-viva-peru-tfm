import { groupedSplit } from './split.util';

describe('groupedSplit', () => {
  it('keeps sources isolated and preserves class coverage when a grouped solution exists', () => {
    const items: Array<{ group: string; label: string; id: string }> = [];
    const add = (group: string, label: string, count: number) => {
      for (let index = 0; index < count; index++) items.push({ group, label, id: `${group}-${label}-${index}` });
    };

    // Solo tres fuentes contienen la clase C. Para cubrir los tres splits,
    // el optimizador debe repartirlas entre train, validación y test.
    for (const group of ['g0', 'g1', 'g2']) {
      add(group, 'A', 8);
      add(group, 'B', 8);
      add(group, 'C', 8);
    }
    for (const group of ['g3', 'g4', 'g5', 'g6', 'g7', 'g8', 'g9']) {
      add(group, 'A', 6);
      add(group, 'B', 6);
    }

    const result = groupedSplit(items, 0.7, 0.15, 42);
    const splitByGroup = new Map<string, string>();
    for (const item of result) {
      const previous = splitByGroup.get(item.group);
      expect(previous === undefined || previous === item.split).toBe(true);
      splitByGroup.set(item.group, item.split);
    }
    for (const split of ['train', 'val', 'test']) {
      expect(new Set(result.filter((item) => item.split === split).map((item) => item.label))).toEqual(new Set(['A', 'B', 'C']));
    }
    expect(groupedSplit(items, 0.7, 0.15, 42)).toEqual(result);
  });

  it('places a source type in train and test when two independent sources exist', () => {
    const items = Array.from({ length: 10 }, (_, groupIndex) =>
      ['A', 'B'].flatMap((label) =>
        Array.from({ length: 5 }, (_, index) => ({
          group: `g${groupIndex}`,
          label,
          id: `${groupIndex}-${label}-${index}`,
          stratum: groupIndex < 2 ? 'youtube' : 'pdf',
        })),
      ),
    ).flat();

    const result = groupedSplit(items, 0.7, 0.15, 42);
    const youtubeSplits = new Set(
      result.filter((item) => item.stratum === 'youtube').map((item) => item.split),
    );
    expect(youtubeSplits.has('train')).toBe(true);
    expect(youtubeSplits.has('test')).toBe(true);
  });
});
