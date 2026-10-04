# DeepSpot-M quickstart

**Explore your tissue from a new molecular perspective.**

Aurora predicts spatial gene expression from routine H&E images, helping
researchers explore molecular patterns across samples, cohorts and disease.

These two notebooks follow one H&E slide, a lung cancer section, to its
predicted spatial gene expression, and explore it on the tissue: where a gene's
signal appears, how the regions of the section differ, and which patterns to
take further.

| Notebook | What you get |
|---|---|
| [`01-first-prediction.ipynb`](notebooks/01-first-prediction.ipynb) | From slide to result: one H&E slide to its predicted spatial gene expression. |
| [`02-downstream.ipynb`](notebooks/02-downstream.ipynb) | Explore the result: gene maps, clusters and the regions they draw on your tissue. |

To try Aurora without writing code, upload a slide on the website with
[Aurora Direct](https://auroraomics.org/upload), or
[explore the example slide](https://auroraomics.org/demo).

## Choose the workflow that fits your research

- **Upload your slides.** Prepare your H&E slide on your own machine and send
  it to Aurora.
- **Keep your slides with you.** When images must stay in your environment,
  run DeepSpot-H on your own machine and send what it computes. No image leaves
  your machine.

Both return the same result, and you choose one in the first notebook.

## Run it

```bash
git clone https://github.com/auroraomics/deepspot-m-quickstart.git
cd deepspot-m-quickstart
pip install -r requirements.txt
auroraomics login you@institution.edu
jupyter lab notebooks/01-first-prediction.ipynb
```

The first notebook needs access to Aurora API:
[get access](https://docs.auroraomics.org/get-access/). To keep your slides
with you, also install `pip install "auroraomics[embed]"`;
[Your slides stay with you](https://docs.auroraomics.org/guides/embeddings/)
has the details.

Analysis is for academic and non-profit research. Commercial evaluation and use
are governed by a written agreement with Aurora.
[Discuss commercial access](https://auroraomics.org/contact).

## The example slide

One lung cancer section, `LC1`, from an open-access dataset:

> Dawo, S., Nonchev, K., & Silina, K. (2025). *10x Visium Spatial
> Transcriptomics Dataset: Kidney (3) and Lung (5) Cancer with Tertiary
> Lymphoid Structures* [Data set]. Zenodo.
> <https://doi.org/10.5281/zenodo.14620362>

To work on your own slide, point the first notebook at your file.

## Learn more

- [From slide to result](https://docs.auroraomics.org/first-prediction/) and
  [what you get back](https://docs.auroraomics.org/results/), in Aurora Docs.
- [Open a result in Aurora Intelligence](https://app.auroraomics.org) to explore
  it as a map.
- [deepspot-h-quickstart](https://github.com/auroraomics/deepspot-h-quickstart)
  keeps your slides with you.
- [Aurora](https://auroraomics.org)

The code in this repository is open source: [LICENSE](LICENSE).
