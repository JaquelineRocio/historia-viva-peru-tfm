import { computeCohenKappa } from './datasets.service';

describe('computeCohenKappa', () => {
  it('returns one for perfect agreement with more than one class', () => {
    expect(computeCohenKappa([
      { primary: 'a', secondary: 'a', count: 10 },
      { primary: 'b', secondary: 'b', count: 10 },
    ]).kappa).toBe(1);
  });

  it('calculates agreement corrected by chance', () => {
    const result = computeCohenKappa([
      { primary: 'a', secondary: 'a', count: 8 },
      { primary: 'a', secondary: 'b', count: 2 },
      { primary: 'b', secondary: 'a', count: 1 },
      { primary: 'b', secondary: 'b', count: 9 },
    ]);
    expect(result.observed).toBeCloseTo(0.85);
    expect(result.kappa).toBeGreaterThan(0.69);
  });

  it('returns null until there are completed pairs', () => {
    expect(computeCohenKappa([]).kappa).toBeNull();
  });
});
