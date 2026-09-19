# DeepSpot-M quickstart

**Predict spatial gene expression from an H&E image, and then read the answer
like data.** Two notebooks: one takes a slide to a result file, the other takes
that result file to a gene map, a UMAP and clusters drawn back on the tissue.

**The rule to settle first: you decide what leaves your machine.** Cut your
slide into tiles and send those, or run DeepSpot-H on your own machine and send
only the embeddings it computes. Both notebooks show both routes end to end.
DeepSpot-M runs on the service either way.

| Route | What you run locally | What leaves your machine | Observation kind |
|---|---|---|---|
| **Send your slides** | Tiling and quality control | The tile images | `patches` |
| **Your slides stay with you** | Tiling, quality control and DeepSpot-H | Numbers and positions. No image. | `embeddings` |

[Your slides stay with you](https://docs.auroraomics.org/guides/embeddings/) is
the reference for the second route; it is the page these notebooks follow.

## Who this is for

A computational biologist or bioinformatician who holds H&E images and has no
spatial assay for them, and who wants to see what a prediction looks like on
real tissue before deciding whether to run one on their own cohort. You need
Python and a laptop. A GPU is optional, and only for the local route.

Nothing here is a benchmark, and nothing here reports how well the model does.
It shows you the shape of the work.

## What is in the repository

| File | What it does |
|---|---|
| [`notebooks/01-first-prediction.ipynb`](notebooks/01-first-prediction.ipynb) | One slide to one `.h5ad`, on both routes. |
| [`notebooks/02-downstream.ipynb`](notebooks/02-downstream.ipynb) | A spatial gene map, a UMAP and clusters drawn back on the tissue. |
| [`quickstart/zenodo.py`](quickstart/zenodo.py) | Fetches one member of the example archive without downloading the archive. |

## Run it

```bash
git clone https://github.com/auroraomics/deepspot-m-quickstart.git
cd deepspot-m-quickstart
pip install -r requirements.txt
jupyter lab notebooks/01-first-prediction.ipynb
```

Preparing a sample needs no account. Submitting one needs a key, and a key is
minted for an account that has been granted programmatic access:
[Get access](https://docs.auroraomics.org/get-access/). Ask before you need it
— a person reviews the request, and the first two sections of notebook 01 run
while you wait.

For the local route, add the one extra that carries an encoder runtime:

```bash
pip install "auroraomics[embed]"
```

On a machine without a GPU, ask for the CPU build of the runtime as well; the
[embeddings guide](https://docs.auroraomics.org/guides/embeddings/) gives the
command.

## The example data

One lung-cancer section, `LC1`, from an open dataset of Visium sections with
tertiary lymphoid structures:

> Dawo, S., Nonchev, K., & Silina, K. (2025). *10x Visium Spatial
> Transcriptomics Dataset: Kidney (3) and Lung (5) Cancer with Tertiary
> Lymphoid Structures* [Data set]. Zenodo.
> <https://doi.org/10.5281/zenodo.14620362>

Licensed **CC-BY-4.0**. If you re-use it, cite it.

**The whole record is one archive of about 1.9 GiB, and the notebooks do not
download it.** A zip file keeps an index of its members at the end and HTTP can
ask for a byte range, so `quickstart/zenodo.py` reads the index over two small
requests and then streams only the member you asked for, checking the member's
own checksum as the bytes arrive. The slide is about 200 MiB on the wire and
the measured expression about 18 MiB. Pick a different section by changing one
name:

```bash
python -m quickstart.zenodo --list           # every member and what it costs
python -m quickstart.zenodo slide measured   # just the two the notebooks read
```

The record also holds this section's own measured spatial expression. Notebook
02 puts it beside the prediction, as a picture to look at rather than a score:
no metric is computed anywhere in this repository, and none should be read out
of those two panels.

## What comes back

One `.h5ad` per job, with the same layout whichever route produced it: one row
per tile, one column per gene, and the tile's centre in full-resolution slide
pixels under `obsm["spatial"]`.

**The gene axis is indexed by Ensembl stable gene identifier, and the symbol
travels beside it in `var["feature_name"]`.** Symbols are renamed, retired and
occasionally reassigned; an identifier is not. Look a gene up by identifier and
read the symbol for the label — this is the one place a first analysis reliably
goes wrong, and notebook 02 does it the right way in the open.

`var["measured_in_training"]` states, per gene, whether the model saw that gene
measured in training. Read it before you act on a gene.

[What you get back](https://docs.auroraomics.org/results/) is the full layout,
generated from the service, and it is the authority when this page and it
disagree.

## Access and limits

Analysis is for academic and non-profit research. Commercial evaluation and use
run under a separate written agreement — <https://auroraomics.org/contact>.

Every approved account starts on the `academic` tier, which meters tiles,
embedding rows and jobs per key. Notebook 01 prints the current counters out of
the contract document shipped inside the `auroraomics` package, so what you
read is what the service enforces rather than a copy of it.
[Limits](https://docs.auroraomics.org/limits/) states them on the site.

A prediction is a hypothesis about what an assay would have measured. It is not
a measurement, it is not evidence about a patient, and it has no clinical use.
[Responsible use](https://docs.auroraomics.org/responsible-use/) states the
conditions attached to every result, and the published Terms are the binding
text.

## Related

- [`deepspot-h-quickstart`](https://github.com/auroraomics/deepspot-h-quickstart)
  — tiling and embeddings on your own machine, in depth. This repository picks
  up where that one ends.
- [DeepSpot-H](https://docs.auroraomics.org/models/deepspot-h/) and
  [DeepSpot-M](https://docs.auroraomics.org/models/deepspot-m/) — what each
  part reads and returns.
- <https://auroraomics.org> and <https://docs.auroraomics.org>.

## Licence

The example code in this repository is MIT — see [LICENSE](LICENSE). Lift a
cell and use it.

The `auroraomics` package the notebooks call is published under its own,
different licence, which is stated on its
[install page](https://docs.auroraomics.org/quickstart/#install). Read it
before you build on the package. Model weights carry terms of their own, which
each model's card names.
