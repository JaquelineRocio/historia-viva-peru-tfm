# English demonstration script

## Application and prediction

“Historia Viva Peru helps teachers find historical evidence in PDFs and YouTube videos. I add a source, and the application extracts its text and divides it into traceable segments. Each segment keeps its page number or timestamp.

The BETO classifier predicts one of seven topics. Years, people and places are extracted separately. The teacher can review and correct the suggested topic. Corrections are saved as feedback for a future dataset; they do not immediately change the active model.”

## Training and evaluation

“Our frozen dataset contains 814 reviewed segments from ten sources: 596 for training, 81 for validation, and 137 for testing. Each source belongs to only one split.

We compare configurations using validation macro F1 and select the model before evaluating it on the test set. Macro F1 gives equal weight to every class. Our original BETO model achieved approximately 0.425, compared with 0.353 for the original TF-IDF baseline. These results are experimental. The labels were assisted by AI and were not independently validated by a historian.”

“In the new experiment, we compared three learning rates. The configuration with a learning rate of 0.00002 achieved the best validation macro F1, approximately 0.438, at epoch two. Its test macro F1 was approximately 0.311, below our previous model and the baseline. We kept this candidate experimental and did not replace the production model.”

## Functional cases to show live

1. Add a supported PDF or YouTube source, wait for processing, open a segment at its page or timestamp, inspect the prediction, correct it and reload to verify persistence.
2. Ask an out-of-scope question about Apollo 11. Verify that the application abstains and returns no supporting evidence.

Record expected and actual results, the environment, time and screenshots. Login checks alone do not demonstrate the prediction workflow.

## Maintenance and continuous integration

“The CI workflow runs automated tests and builds the application. A failed check must prevent deployment.

The ML experiment pipeline validates a versioned dataset, trains candidates, selects using validation data, evaluates the winner, and archives metrics and model files. The pipeline keeps an audit trail. A candidate that fails the quality criteria remains experimental.”

Only explain automatic collection of corrections, promotion or rollback as working after those steps have been implemented and demonstrated. At present, the experiment workflow does not update the production model.
