# DeepSpot-M quickstart

Aurora predicts spatial gene expression from routine H&E images, helping
researchers explore molecular patterns across samples, cohorts and disease.

These two notebooks take one H&E slide to its predicted spatial gene
expression and explore it on your own tissue: a gene map, a UMAP and clusters
drawn back on the slide.

| Notebook | What you get |
|---|---|
| [`01-first-prediction.ipynb`](notebooks/01-first-prediction.ipynb) | From slide to result: one H&E slide to one `.h5ad`. |
| [`02-downstream.ipynb`](notebooks/02-downstream.ipynb) | Explore your result: gene maps, a UMAP and clusters on your tissue. |

## Choose the workflow that fits your research

- **Send your slides.** Prepare your H&E slide on your own machine and send its
  tiles. [Install and prepare a slide](https://docs.auroraomics.org/quickstart/).
- **Your slides stay with you.** Run DeepSpot-H, the foundation model for H&E
  images, on your own machine and send the numbers it produces. No image leaves
  your machine.
  [Run DeepSpot-H locally](https://docs.auroraomics.org/guides/embeddings/).

DeepSpot-M, the model that predicts spatial gene expression, runs on ours in
both, and both return the same result file. You choose one in the first
notebook, with one setting.

To send a slide without writing code, upload it on the website with
[Aurora Direct](https://auroraomics.org/upload).

## Run it

```bash
git clone https://github.com/auroraomics/deepspot-m-quickstart.git
cd deepspot-m-quickstart
pip install -r requirements.txt
auroraomics login you@institution.edu
jupyter lab notebooks/01-first-prediction.ipynb
```

Notebook 01 needs a key, and `auroraomics login` stores it on this machine.
[Get access](https://docs.auroraomics.org/get-access/) says how to ask for one.

To keep your slides with you, add the extra that runs DeepSpot-H on your
machine:

```bash
pip install "auroraomics[embed]"
```

On a machine with no GPU, ask for the CPU build as well:

```bash
pip install "auroraomics[embed]" --extra-index-url https://download.pytorch.org/whl/cpu
```

Analysis is for academic and non-profit research. Commercial evaluation and use
are governed by a written agreement with Aurora.
[Discuss commercial access](https://auroraomics.org/contact).

## The example slide

One lung cancer section, `LC1`, from an open-access dataset:

> Dawo, S., Nonchev, K., & Silina, K. (2025). *10x Visium Spatial
> Transcriptomics Dataset: Kidney (3) and Lung (5) Cancer with Tertiary
> Lymphoid Structures* [Data set]. Zenodo.
> <https://doi.org/10.5281/zenodo.14620362>

`quickstart/zenodo.py` fetches that one slide from the record, not the whole
archive. To fetch another section, pass its name:

```bash
python -m quickstart.zenodo --list                 # every member of the archive
python -m quickstart.zenodo slide --sample LC2     # another section's slide
```

## What you get back

One `.h5ad` per slide, with the same layout on both workflows: one row per
tile, one column per gene, and each tile's centre on your slide under
`obsm["spatial"]`. Genes are indexed by Ensembl identifier, and the symbol sits
beside it in `var["feature_name"]`.
[What you get back](https://docs.auroraomics.org/results/) is the full layout.

To explore a result as a map in
[Aurora Intelligence](https://app.auroraomics.org), submit with
`land_in_workspace=True` and import it into a workspace.

## Learn more

- [From slide to result](https://docs.auroraomics.org/first-prediction/): the
  same journey in Aurora Docs, from Python, a shell or an agent.
- [From an image to a virtual molecular view](https://docs.auroraomics.org/examples/whole-slide/):
  one real slide, and genes you can check against the stain.
- [`deepspot-h-quickstart`](https://github.com/auroraomics/deepspot-h-quickstart):
  tiles and embeddings on your own machine, in depth.
- [Aurora](https://auroraomics.org) and
  [Aurora Docs](https://docs.auroraomics.org).

## Licence

The code in this repository is MIT licensed: [LICENSE](LICENSE). The
`auroraomics` package carries its own licence.
