import { MlMetrics } from '../ml/ml-service.port';
import { isModelRecommended } from './training.service';

function metrics(f1Macro: number, classScores: number[], baselineF1 = 0.35): MlMetrics {
  return {
    accuracy: 0.8,
    precision_macro: 0.8,
    recall_macro: 0.8,
    f1_macro: f1Macro,
    labels: classScores.map((_, index) => `class-${index}`),
    confusion_matrix: [],
    per_class: classScores.map((f1, index) => ({
      label: `class-${index}`,
      precision: f1,
      recall: f1,
      f1,
      support: 100,
    })),
    baseline: { name: 'tfidf_logistic_regression', f1_macro: baselineF1 },
  };
}

describe('isModelRecommended', () => {
  it('recommends a model only when macro and every class meet the thresholds', () => {
    expect(isModelRecommended(metrics(0.7, [0.5, 0.73, 0.81]))).toBe(true);
  });

  it('keeps a model experimental when one class is below 0.50', () => {
    expect(isModelRecommended(metrics(0.82, [0.84, 0.49, 0.9]))).toBe(false);
  });

  it('keeps a model experimental when macro F1 is below 0.70', () => {
    expect(isModelRecommended(metrics(0.69, [0.7, 0.72, 0.75]))).toBe(false);
  });

  it('keeps a model experimental when it does not beat TF-IDF', () => {
    expect(isModelRecommended(metrics(0.75, [0.7, 0.76, 0.8], 0.76))).toBe(false);
  });

  it('keeps legacy metrics without an auditable baseline experimental', () => {
    const candidate = metrics(0.8, [0.7, 0.8, 0.9]);
    delete candidate.baseline;
    expect(isModelRecommended(candidate)).toBe(false);
  });
});
