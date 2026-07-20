import { distinctiveTerms, supportedEvidence } from './evidence-support.util';

describe('supportedEvidence', () => {
  it('abstains when the distinctive subject is absent', () => {
    const evidence = [{ text: 'La independencia organizó un nuevo Congreso peruano.', score: 0.78 }];
    expect(distinctiveTerms('¿Qué relación tuvo Apolo 11 con la Independencia peruana?')).toContain('apolo');
    expect(supportedEvidence('¿Qué relación tuvo Apolo 11 con la Independencia peruana?', evidence)).toEqual([]);
  });

  it('still abstains if a client damages accented characters', () => {
    const evidence = [{ text: 'Bolivia y su relación con el Perú durante la independencia.', score: 0.65 }];
    expect(supportedEvidence('¿Qu� relaci�n tuvo Apolo 11 con la Independencia peruana?', evidence)).toEqual([]);
  });

  it('keeps evidence anchored in the historical subject', () => {
    const evidence = [{ text: 'La población indígena participó de maneras distintas.', score: 0.41 }];
    expect(supportedEvidence('¿Qué papel tuvo la población indígena?', evidence)).toHaveLength(1);
  });

  it('requires a calibrated score for fully generic questions', () => {
    expect(supportedEvidence('¿Qué pasó en la historia del Perú?', [
      { text: 'fragmento débil', score: 0.2 },
      { text: 'fragmento suficiente', score: 0.4 },
    ])).toEqual([{ text: 'fragmento suficiente', score: 0.4 }]);
  });
});
